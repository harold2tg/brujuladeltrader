"""FastAPI application entry point for La Brújula del Trader."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.uploads.router import router as uploads_router
from app.modules.analytics.router import router as analytics_router
from app.modules.ctrader.router import router as ctrader_router
from app.modules.reports.router import router as reports_router
from app.modules.ai_engine.router import router as ai_router
from app.modules.alerts.router import router as alerts_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="La Brújula del Trader API",
    description="Plataforma de análisis estadístico para traders de XAUUSD",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(uploads_router)
app.include_router(analytics_router)
app.include_router(ctrader_router)
app.include_router(reports_router)
app.include_router(ai_router)
app.include_router(alerts_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "brujula-api"}


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "La Brújula del Trader API",
        "version": "0.1.0",
        "docs": "/docs",
    }
