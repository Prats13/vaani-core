"""
Vaani — The Farmer Buddy
=========================
FastAPI application entry point.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from api.sip_routes import router as sip_router
from core.livekit_manager import livekit_manager
from contextlib import asynccontextmanager

# ---------------------------------------------------------------------------
# Data-service model imports — ensure tables are registered before create_all
# ---------------------------------------------------------------------------
import data_service.weather.models   # noqa: F401
import data_service.crop.models      # noqa: F401
import data_service.mandi.models     # noqa: F401

from data_service.weather import routers as weather_routers
from data_service.crop import routers as crop_routers
from data_service.mandi import routers as mandi_routers
from data_service.search import routers as search_routers
from data_service.core.db import engine, Base
from data_service.core.cache_service import close_redis
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Database schema & table creation (synchronous, runs at import time)
# ---------------------------------------------------------------------------
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS weather"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS crop"))

Base.metadata.create_all(bind=engine)
data_service.crop.models.CropBase.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    await livekit_manager.initialize()
    yield
    await livekit_manager.close()
    await close_redis()


# Create FastAPI application
app = FastAPI(
    title="Vaani - The Farmer Buddy",
    description="Voice-first AI decision support system for farmers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(sip_router, prefix="/api/v1")

# Include data-service routers (weather, crop, mandi, search)
app.include_router(weather_routers.router)
app.include_router(crop_routers.router)
app.include_router(mandi_routers.router)
app.include_router(search_routers.router)


# Explicit CORS preflight handler
@app.options("/{full_path:path}")
async def options_handler(request: Request) -> Response:
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010
    )
