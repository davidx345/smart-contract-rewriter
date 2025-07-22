"""
Main Microservices Application
Orchestrates all microservices to run as a single Heroku app
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import os
import sys
from contextlib import asynccontextmanager

# Add all service paths
auth_service_path = os.path.join(os.path.dirname(__file__), 'auth-service')
contract_service_path = os.path.join(os.path.dirname(__file__), 'contract-service')
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')

sys.path.extend([auth_service_path, contract_service_path, backend_path])

# Import services
from auth_service.main import app as auth_app
from contract_service.main import app as contract_app

# Background tasks storage
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and background services"""
    
    # Start background microservices
    auth_task = asyncio.create_task(run_auth_service())
    contract_task = asyncio.create_task(run_contract_service())
    
    background_tasks.extend([auth_task, contract_task])
    
    yield
    
    # Cleanup: Cancel background tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

# Main FastAPI app
app = FastAPI(
    title="SoliVolt Microservices Platform",
    description="Unified microservices application for enterprise smart contract platform",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware with secure origins
ALLOWED_ORIGINS = [
    "https://smart-contract-rewriter.vercel.app",  # Your Vercel frontend
    "https://your-frontend.vercel.app",            # Replace with any additional domains
    "https://solivolt.vercel.app",                 # Alternative production frontend
    "http://localhost:3000",                       # Local development
    "http://localhost:5173",                       # Vite dev server
]

# Add development origins if in development
if os.getenv("ENVIRONMENT") == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3001",
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins instead of "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key"
    ],
)

# Service discovery and routing
SERVICES = {
    "auth": {"port": 8001, "base_path": "/auth", "health": "/auth/health"},
    "contracts": {"port": 8002, "base_path": "/contracts", "health": "/contracts/health"},
}

async def run_auth_service():
    """Run authentication service"""
    try:
        config = uvicorn.Config(
            "auth_service.main:app",
            host="0.0.0.0",
            port=int(os.getenv("AUTH_SERVICE_PORT", 8001)),
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        print(f"Auth service error: {e}")

async def run_contract_service():
    """Run contract service"""
    try:
        config = uvicorn.Config(
            "contract_service.main:app",
            host="0.0.0.0", 
            port=int(os.getenv("CONTRACT_SERVICE_PORT", 8002)),
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        print(f"Contract service error: {e}")

@app.get("/")
async def root():
    """Main service registry endpoint"""
    return {
        "message": "SoliVolt Microservices Platform",
        "version": "1.0.0",
        "services": SERVICES,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "service_registry": "/services"
        }
    }

@app.get("/health")
async def health_check():
    """Health check for the entire platform"""
    import httpx
    
    health_status = {
        "platform": "healthy",
        "services": {}
    }
    
    # Check each service health
    for service_name, config in SERVICES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{config['port']}{config['health']}", 
                    timeout=5.0
                )
                health_status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "port": config["port"],
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e),
                "port": config["port"]
            }
    
    return health_status

@app.get("/services")
async def service_registry():
    """Service registry endpoint"""
    return {
        "services": SERVICES,
        "discovery": {
            "auth_service": f"http://localhost:{SERVICES['auth']['port']}",
            "contract_service": f"http://localhost:{SERVICES['contracts']['port']}"
        }
    }

# API Gateway - Route requests to appropriate services
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_gateway(path: str, request):
    """Gateway to authentication service"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        # Forward request to auth service
        response = await client.request(
            method=request.method,
            url=f"http://localhost:{SERVICES['auth']['port']}/api/v1/{path}",
            headers=dict(request.headers),
            content=await request.body()
        )
        
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/contracts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def contracts_gateway(path: str, request):
    """Gateway to contract service"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        # Forward request to contract service
        response = await client.request(
            method=request.method,
            url=f"http://localhost:{SERVICES['contracts']['port']}/api/v1/{path}",
            headers=dict(request.headers),
            content=await request.body()
        )
        
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Heroku provides PORT env var
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
