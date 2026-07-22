# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main / master | ✅ Yes |
| older branches | ❌ No |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report security issues privately:
- **Email:** terazionservices@gmail.com
- **Subject:** `[SECURITY] AI Agentic Assistant — <brief description>`

We aim to respond within **48 hours** and release a fix within **7 days** for critical issues.

## What to Include

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

## Security Features

### Authentication
- **JWT (HS256)** — 24-hour token expiry, workspace-scoped claims
- **Dev bypass** — `APP_ENV=development` skips auth locally (never in production)
- **Rate limiting** — SlowAPI per-endpoint limits (60 req/min default)

### Input Validation
- **Pydantic V2** on all request bodies — no raw user input reaches business logic
- **CORS** — explicit allow-list, no wildcard in production

### Data Protection
- **No secrets in code** — all sensitive values via environment variables
- **`.env` gitignored** — `.env.example` committed instead
- **Passwords** — never logged, never returned in API responses

### Known Limitations (Development / Free-tier)
- No HTTPS enforcement in local dev (use reverse proxy in production)
- SQLite not used — PostgreSQL required for production data integrity
- Redis session store — use TLS (`rediss://`) in production (Upstash)

## Responsible Disclosure

We follow responsible disclosure practices. Security researchers who report valid vulnerabilities in good faith will be acknowledged (if desired) in the release notes.

## Security Checklist for Self-Hosters

Before deploying to production:
- [ ] Change `JWT_SECRET` to a random 32+ char value (`openssl rand -hex 32`)
- [ ] Set `APP_ENV=production` (enables full JWT enforcement)
- [ ] Set `DEMO_MODE=false` (or `true` only for demo instances)
- [ ] Use `rediss://` (TLS) for Redis URL in production
- [ ] Set `CORS_ORIGINS` to your exact frontend domain (no wildcard)
- [ ] Enable HTTPS via reverse proxy (Nginx / Caddy / Render / Vercel handles this)
- [ ] Rotate all API keys (OpenAI, Groq, Razorpay, etc.) before going live
- [ ] Set up log monitoring for error spikes
