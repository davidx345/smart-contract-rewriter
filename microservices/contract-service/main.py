"""
Contract Analysis Microservice
Handles smart contract analysis, storage, and retrieval
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the main backend to path to reuse components
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.append(backend_path)

from app.apis.v1.endpoints.contracts import router as contracts_router

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt Contract Service",
    description="Smart contract analysis and management microservice",
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

# Include contract routes
app.include_router(contracts_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "contract-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SoliVolt Contract Service",
        "version": "1.0.0",
        "endpoints": {
            "contracts": "/api/v1/contracts/*",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
