"""
Adaptive Inspection Intelligence Platform — FastAPI Application
SIH 2026 | PS 26095 | Ministry of Social Justice and Empowerment

Main application entry point with:
- CORS configuration
- Rate limiting (SlowAPI)
- Security headers
- API router registration
- WebSocket endpoint
- Startup/shutdown events
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.v1.endpoints import (
    auth, projects, monitoring, analytics,
    inspections, evidence, cctv, followup,
    notifications, audit, websocket,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Demo mode: {settings.DEMO_MODE}")
    yield
    print("Application shutdown.")


app = FastAPI(
    title="Adaptive Inspection Intelligence Platform",
    description=(
        "SIH 2026 — PS 26095 — Ministry of Social Justice and Empowerment\n"
        "Real-time monitoring, explainable anomaly detection, "
        "controlled surprise inspections, evidence integrity."
    ),
    version="1.0.0-prototype",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    start = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2)) + "ms"
    # In production: add Strict-Transport-Security
    return response


# ─── API Routes ───────────────────────────────────────────────────────────────

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(monitoring.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(inspections.router, prefix=API_PREFIX)
app.include_router(inspections.route_router, prefix=API_PREFIX)
app.include_router(evidence.router, prefix=API_PREFIX)
app.include_router(cctv.router, prefix=API_PREFIX)
app.include_router(followup.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/")
async def root():
    return {
        "message": "Adaptive Inspection Intelligence Platform API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
