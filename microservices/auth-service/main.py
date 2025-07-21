"""
Authentication Microservice
Handles all authentication, authorization, and user management
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the main backend to path to reuse our auth components
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.append(backend_path)

from app.core.config import settings
from app.apis.v1.endpoints.auth import router as auth_router
from app.db.session import get_db

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt Authentication Service",
    description="Enterprise authentication and user management microservice",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SoliVolt Authentication Service",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth/*",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
