# File: backend/app/core/middleware.py
# Description: Security middleware for SwasthyaGrid AI.
#   - Adds security response headers (X-Content-Type-Options, X-Frame-Options, etc.)
#   - Simple in-process rate limiter (token-bucket per IP) for auth endpoints
#   - Request ID injection for distributed tracing

import time
import uuid
import logging
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("swasthya.middleware")


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security-hardening HTTP response headers on every response.

    Headers applied:
      X-Content-Type-Options  — Prevents MIME-type sniffing
      X-Frame-Options         — Prevents clickjacking
      X-XSS-Protection        — Legacy XSS filter hint
      Referrer-Policy         — Controls referrer leakage
      Permissions-Policy      — Disables unused browser features
      Strict-Transport-Security — Forces HTTPS (only in production)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # Add HSTS only when running behind HTTPS (avoids breaking local dev)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


# ---------------------------------------------------------------------------
# Request ID Middleware
# ---------------------------------------------------------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique UUID to every request as X-Request-ID.
    Useful for distributed tracing and log correlation.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# Rate Limiter — Token Bucket (in-process, per-IP)
# ---------------------------------------------------------------------------

# Bucket state: {ip: (tokens, last_refill_timestamp)}
_buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (10.0, time.monotonic()))
_BUCKET_LOCK_SENTINEL = object()

# Configuration
RATE_LIMIT_RULES = {
    "/api/v1/auth/login":    {"capacity": 10, "refill_rate": 10 / 60},  # 10 req/min
    "/api/v1/auth/register": {"capacity": 5,  "refill_rate": 5 / 60},   # 5 req/min
    "/api/v1/auth/refresh":  {"capacity": 20, "refill_rate": 20 / 60},  # 20 req/min
    "/api/v1/agent/chat":    {"capacity": 30, "refill_rate": 30 / 60},  # 30 req/min
}
# Global fallback: 200 req/min for all other API endpoints
DEFAULT_CAPACITY = 200
DEFAULT_REFILL_RATE = 200 / 60


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For from reverse proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(ip: str, path: str) -> bool:
    """
    Token-bucket rate limiter.
    Returns True if request is allowed, False if rate-limited.
    """
    rule = RATE_LIMIT_RULES.get(path, {"capacity": DEFAULT_CAPACITY, "refill_rate": DEFAULT_REFILL_RATE})
    capacity = rule["capacity"]
    refill_rate = rule["refill_rate"]  # tokens per second

    bucket_key = f"{ip}:{path}"
    tokens, last_refill = _buckets[bucket_key]

    # Refill tokens based on elapsed time
    now = time.monotonic()
    elapsed = now - last_refill
    tokens = min(capacity, tokens + elapsed * refill_rate)

    if tokens >= 1.0:
        _buckets[bucket_key] = (tokens - 1.0, now)
        return True
    else:
        _buckets[bucket_key] = (tokens, now)
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiting middleware.
    Applied to auth and agent endpoints; all others use a generous default.
    Returns HTTP 429 Too Many Requests when a bucket is exhausted.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only rate-limit API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        ip = _get_client_ip(request)
        allowed = _check_rate_limit(ip, request.url.path)

        if not allowed:
            logger.warning(f"Rate limit exceeded: {ip} → {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down and try again shortly.",
                    "error": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
