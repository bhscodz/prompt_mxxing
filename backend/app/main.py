# File: backend/app/main.py
# Description: FastAPI Application Entry Point for SwasthyaGrid AI Phase 2
# Phase 2 adds: Auth/RBAC, Leave Management, Forecasting Engine, AI Agent, Economics Dashboard
# Integrates REST API routes, High-Speed JSON-RPC 2.0, Real-Time WebSockets, and PyTorch AI Time Series Forecasting

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.utils.seed_data import seed_database
from app.utils.websocket_manager import ws_manager

# ── Phase 1: Import API Routers ────────────────────────────────────────────────
from app.api.facilities import router as facilities_router
from app.api.inventory import router as inventory_router
from app.api.footfall_crm import router as crm_router
from app.api.beds import router as beds_router
from app.api.attendance import router as attendance_router
from app.api.tests_audit import router as tests_router
from app.api.ai_forecasts import router as ai_router
from app.api.redistribution import router as redistribution_router
from app.api.interventions import router as interventions_router
from app.rpc.jsonrpc_server import rpc_router

# ── Phase 2: Import API Routers ────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.leave_management import router as leave_router
from app.api.forecasting import router as forecasting_router
from app.api.ai_agent import router as agent_router, agent_ws_router
from app.api.economics import router as economics_router

# ── Security Middleware ────────────────────────────────────────────────────────
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RateLimitMiddleware,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("swasthya.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle events."""
    logger.info("Initializing SwasthyaGrid AI database and models (Phase 2)...")
    await init_db()
    # Auto-seed Phase 1 + Phase 2 data if database is empty
    try:
        await seed_database()
    except Exception as e:
        logger.warning(f"Database seeder note: {e}")
    logger.info("SwasthyaGrid AI backend started successfully (Phase 2).")
    yield
    logger.info("Shutting down SwasthyaGrid AI backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Multilingual AI Platform for Real-Time District PHC/CHC Health Centre Management — "
        "Phase 2: Auth/RBAC · Leave Management · Advanced Forecasting · Multilingual AI Agent · Economics Dashboard"
    ),
    lifespan=lifespan
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Hardening Middleware (innermost → outermost execution order) ──────
app.add_middleware(SecurityHeadersMiddleware)   # Adds security response headers
app.add_middleware(RequestIDMiddleware)         # X-Request-ID tracing
app.add_middleware(RateLimitMiddleware)         # Token-bucket rate limiting

# ── Register REST Routers ──────────────────────────────────────────────────────
api_prefix = settings.API_V1_STR

# Phase 1 routers
app.include_router(facilities_router, prefix=api_prefix)
app.include_router(inventory_router, prefix=api_prefix)
app.include_router(crm_router, prefix=api_prefix)
app.include_router(beds_router, prefix=api_prefix)
app.include_router(attendance_router, prefix=api_prefix)
app.include_router(tests_router, prefix=api_prefix)
app.include_router(ai_router, prefix=api_prefix)
app.include_router(redistribution_router, prefix=api_prefix)
app.include_router(interventions_router, prefix=api_prefix)

# Phase 2 routers
app.include_router(auth_router, prefix=api_prefix)           # /api/v1/auth/*
app.include_router(leave_router, prefix=api_prefix)          # /api/v1/leave/*
app.include_router(forecasting_router, prefix=api_prefix)    # /api/v1/forecasting/*
app.include_router(agent_router, prefix=api_prefix)          # /api/v1/agent/*
app.include_router(agent_ws_router, prefix=api_prefix)       # /api/v1/agent/ws/* (HTTP upgrade)
app.include_router(economics_router, prefix=api_prefix)      # /api/v1/economics/*

# ── High-Speed RPC Router ──────────────────────────────────────────────────────
app.include_router(rpc_router)

# ── Real-Time WebSocket: District Live Feed ────────────────────────────────────
@app.websocket("/ws/live-district")
async def websocket_district_endpoint(websocket: WebSocket):
    """Broadcasts real-time district health events to all connected dashboard clients."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive; clients send "ping" to check connectivity
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)


# ── Real-Time WebSocket: AI Agent Chat ────────────────────────────────────────
@app.websocket("/ws/agent-chat")
async def websocket_agent_chat(websocket: WebSocket):
    """
    Bidirectional WebSocket for the Multilingual AI Agent.
    Clients send JSON: {query: str, language: str, facility_id: int | null}
    Server streams back: {type: 'token'|'final'|'error', content: str, intent: str}
    """
    await websocket.accept()
    logger.info("AI Agent WebSocket client connected.")
    try:
        while True:
            # Receive client message as JSON text
            raw = await websocket.receive_text()
            # Import here to avoid circular import at module load
            from app.ai_agent.handler import handle_agent_ws_message
            await handle_agent_ws_message(websocket, raw)
    except WebSocketDisconnect:
        logger.info("AI Agent WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"AI Agent WebSocket error: {e}")
        try:
            await websocket.send_text(f'{{"type":"error","content":"Internal agent error: {e}"}}')
        except Exception:
            pass


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Lightweight liveness probe for load balancers and k8s."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "district": settings.DEFAULT_DISTRICT,
        "phase": "2"
    }


@app.get("/")
async def root():
    """API discovery root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "rpc_endpoint": "/api/rpc/v1",
        "websocket_district": "/ws/live-district",
        "websocket_agent": "/ws/agent-chat",
        "phase": "2"
    }
