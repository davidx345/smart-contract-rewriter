from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import traceback

from app.core.settings import get_settings
from app.apis.v1.router import api_router_v1
from app.infrastructure.container import initialize_container
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuditLogMiddleware,
    DataEncryptionMiddleware,
    SecurityEventDetector
)

# Initialize settings
settings = get_settings()

# Initialize clean architecture container
initialize_container()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=f"SoliVolt API - {settings.app_name}",
    version=settings.app_version,
    description=f"{settings.app_name} - Enterprise Smart Contract Platform",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(DataEncryptionMiddleware)
app.add_middleware(SecurityEventDetector)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses"""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail}
        )
    
    # Log unexpected errors (in production, use proper logging)
    print(f"Unexpected error: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error occurred. Please try again later."
        }
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=settings.security.cors_methods,
    allow_headers=settings.security.cors_headers,
)

# Set up Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

@app.get("/")
async def read_root():
    return {
        "message": f"Welcome to SoliVolt - {settings.app_name}",
        "version": settings.app_version,
        "description": "Enterprise Smart Contract Analysis & Generation Platform",
        "docs": "/docs",
        "api": "/api/v1",
        "status": "operational",
        "environment": settings.environment.value
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "SoliVolt API",
        "version": settings.app_version,
        "timestamp": time.time(),
        "environment": settings.environment.value
    }

# Include API v1 router
app.include_router(api_router_v1, prefix="/api/v1")
