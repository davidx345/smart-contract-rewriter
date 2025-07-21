"""
SoliVolt API Gateway - Enterprise Microservices Gateway
Handles routing, authentication, rate limiting, and service discovery
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
import time
import json
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
from enum import Enum

# Configuration
class ServiceConfig:
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    CONTRACT_SERVICE_URL = os.getenv("CONTRACT_SERVICE_URL", "http://contract-service:8002")
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8003")
    NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8004")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

@dataclass
class ServiceRoute:
    service_name: str
    base_url: str
    health_endpoint: str
    timeout: float = 30.0
    retry_count: int = 3

class ServiceRegistry:
    """Service discovery and health checking"""
    
    def __init__(self):
        self.services = {
            "auth": ServiceRoute("auth-service", ServiceConfig.AUTH_SERVICE_URL, "/health"),
            "contracts": ServiceRoute("contract-service", ServiceConfig.CONTRACT_SERVICE_URL, "/health"),
            "ai": ServiceRoute("ai-service", ServiceConfig.AI_SERVICE_URL, "/health"),
            "notifications": ServiceRoute("notification-service", ServiceConfig.NOTIFICATION_SERVICE_URL, "/health"),
        }
        self.health_status = {}
        
    async def health_check(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        if service_name not in self.services:
            return False
            
        service = self.services[service_name]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service.base_url}{service.health_endpoint}")
                is_healthy = response.status_code == 200
                self.health_status[service_name] = {
                    "healthy": is_healthy,
                    "last_check": time.time(),
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
                }
                return is_healthy
        except Exception as e:
            self.health_status[service_name] = {
                "healthy": False,
                "last_check": time.time(),
                "error": str(e)
            }
            return False
    
    async def get_healthy_service_url(self, service_name: str) -> str:
        """Get URL for a healthy service instance"""
        if await self.health_check(service_name):
            return self.services[service_name].base_url
        raise HTTPException(status_code=503, detail=f"Service {service_name} is unavailable")

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt API Gateway",
    description="Enterprise microservices gateway for smart contract platform",
    version="1.0.0",
    docs_url="/gateway/docs",
    openapi_url="/gateway/openapi.json"
)

# Initialize service registry
service_registry = ServiceRegistry()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

async def rate_limit_check(request: Request):
    """Simple rate limiting"""
    client_ip = request.client.host
    current_time = time.time()
    window_start = current_time - ServiceConfig.RATE_LIMIT_WINDOW
    
    # Clean old entries
    if client_ip in rate_limit_storage:
        rate_limit_storage[client_ip] = [
            timestamp for timestamp in rate_limit_storage[client_ip] 
            if timestamp > window_start
        ]
    else:
        rate_limit_storage[client_ip] = []
    
    # Check limit
    if len(rate_limit_storage[client_ip]) >= ServiceConfig.RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)

async def proxy_request(
    request: Request,
    service_name: str,
    path: str,
    method: str = "GET"
) -> JSONResponse:
    """Proxy request to microservice"""
    
    # Get service URL
    service_url = await service_registry.get_healthy_service_url(service_name)
    target_url = f"{service_url}{path}"
    
    # Prepare request data
    headers = dict(request.headers)
    headers.pop('host', None)  # Remove host header
    
    # Get request body if present
    body = None
    if method.upper() in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Make the proxied request
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )
            
            # Return response
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to {service_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

# Gateway health check
@app.get("/health")
async def gateway_health():
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": time.time(),
        "services": service_registry.health_status
    }

# Service health checks
@app.get("/gateway/services/health")
async def services_health():
    """Check health of all services"""
    health_checks = {}
    for service_name in service_registry.services.keys():
        health_checks[service_name] = await service_registry.health_check(service_name)
    
    return {
        "gateway": "healthy",
        "services": health_checks,
        "details": service_registry.health_status
    }

# Authentication service routes
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(request: Request, path: str):
    """Proxy to authentication service"""
    await rate_limit_check(request)
    return await proxy_request(request, "auth", f"/api/v1/auth/{path}", request.method)

# Contract service routes
@app.api_route("/api/v1/contracts/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def contract_proxy(request: Request, path: str):
    """Proxy to contract service"""
    await rate_limit_check(request)
    return await proxy_request(request, "contracts", f"/api/v1/contracts/{path}", request.method)

# AI service routes
@app.api_route("/api/v1/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ai_proxy(request: Request, path: str):
    """Proxy to AI service"""
    await rate_limit_check(request)
    return await proxy_request(request, "ai", f"/api/v1/ai/{path}", request.method)

# Notification service routes
@app.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def notification_proxy(request: Request, path: str):
    """Proxy to notification service"""
    await rate_limit_check(request)
    return await proxy_request(request, "notifications", f"/api/v1/notifications/{path}", request.method)

# Root endpoint
@app.get("/")
async def root():
    """Gateway root endpoint"""
    return {
        "message": "SoliVolt API Gateway",
        "version": "1.0.0",
        "services": {
            "auth": "/api/v1/auth/*",
            "contracts": "/api/v1/contracts/*",
            "ai": "/api/v1/ai/*",
            "notifications": "/api/v1/notifications/*"
        },
        "docs": "/gateway/docs",
        "health": "/health"
    }

# Background task for periodic health checks
@app.on_event("startup")
async def startup_event():
    """Start periodic health checks"""
    async def periodic_health_checks():
        while True:
            for service_name in service_registry.services.keys():
                await service_registry.health_check(service_name)
            await asyncio.sleep(30)  # Check every 30 seconds
    
    # Start background task
    asyncio.create_task(periodic_health_checks())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
