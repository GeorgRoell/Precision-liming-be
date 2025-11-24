from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api import auth, liming
from config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="NextFarming Liming API",
    description="Secure backend for liming prescription calculations",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# CORS - Allow desktop/web app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(liming.router, prefix="/liming", tags=["Liming Calculations"])


@app.get("/")
def read_root():
    """
    Root endpoint - API information.
    """
    return {
        "service": "NextFarming Liming API",
        "status": "online",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth/login, /auth/me, /auth/register",
            "liming": "/liming/calculate/vdlufa, /liming/calculate/cec",
            "info": "/liming/methods, /liming/lime-types"
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and Cloud Run.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development"
    )
# Force rebuild Mon Nov 24 03:22:28 PM CET 2025
