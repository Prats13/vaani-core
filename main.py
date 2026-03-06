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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    await livekit_manager.initialize()
    yield
    await livekit_manager.close()


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
        port=8003
    )
