# Security Policy — SwasthyaGrid AI

## Supported Versions

| Version | Supported |
|---|---|
| 2.x (Phase 2) | ✅ Active |
| 1.x (Phase 1) | ⚠ Security fixes only |

## Security Architecture

### Authentication
- JWT access tokens (HS256, 30-min expiry)
- Refresh tokens stored as SHA-256 hashes in `user_sessions` table
- bcrypt password hashing (with SHA-256 fallback for environments without passlib)
- Multi-stage RBAC with 8 role levels

### Transport Security
- All production traffic served over HTTPS (HSTS header applied)
- `X-Content-Type-Options: nosniff` on all responses
- `X-Frame-Options: DENY` to prevent clickjacking
- `Permissions-Policy` disabling camera/microphone/geolocation/payment

### Rate Limiting
| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 10 requests/minute per IP |
| `POST /auth/register` | 5 requests/minute per IP |
| `POST /auth/refresh` | 20 requests/minute per IP |
| `POST /agent/chat` | 30 requests/minute per IP |
| All other API endpoints | 200 requests/minute per IP |

### Input Validation
- All request bodies validated via Pydantic v2 schemas
- Password complexity enforced (min 8 chars, letter + digit required)
- Username pattern enforced (`^[a-zA-Z0-9_.-]+$`)
- Email validation via Pydantic `EmailStr`

### Audit Trail
Every write action creates an immutable `AuditLog` record containing:
- `user_id`, `action`, `resource`, `resource_id`
- Client IP address (IPv4/IPv6)
- Timestamp (UTC)

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Instead:
1. Email: `security@swasthyagrid.health.gov.in` (example)
2. Include: description, reproduction steps, potential impact
3. We will acknowledge within 48 hours and provide a fix timeline

## Responsible Disclosure

We follow a 90-day responsible disclosure policy. Reporters who follow this policy will be credited in release notes.
