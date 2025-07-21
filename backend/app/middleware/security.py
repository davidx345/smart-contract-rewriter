"""
Advanced security middleware for enterprise compliance.
"""
import time
import hashlib
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
import json
from datetime import datetime, timedelta

from ..core.settings import get_settings
from ..models.contract_models import AuditLog

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis client for rate limiting and session management
redis_client = redis.Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    decode_responses=True
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (HTTP Strict Transport Security)
        if settings.environment.value == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # CSP (Content Security Policy)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.gemini.google.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with different tiers."""
    
    def __init__(self, app, default_requests: int = 100, default_window: int = 3600):
        super().__init__(app)
        self.default_requests = default_requests
        self.default_window = default_window
        
        # Rate limits by subscription tier
        self.tier_limits = {
            "free": {"requests": 100, "window": 3600},
            "starter": {"requests": 1000, "window": 3600},
            "professional": {"requests": 10000, "window": 3600},
            "enterprise": {"requests": 100000, "window": 3600}
        }
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        user_id = await self.get_user_id(request)
        tier = await self.get_user_tier(user_id) if user_id else "free"
        
        # Check rate limit
        if not await self.check_rate_limit(client_ip, user_id, tier):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
        
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Simple token extraction (in production, verify JWT)
            token = auth_header.split(" ")[1]
            # This should decode and verify JWT in production
            return f"user_{hashlib.md5(token.encode()).hexdigest()[:8]}"
        except Exception:
            return None
    
    async def get_user_tier(self, user_id: str) -> str:
        """Get user's subscription tier."""
        try:
            # This should query the database in production
            tier_key = f"user_tier:{user_id}"
            tier = redis_client.get(tier_key)
            return tier or "free"
        except Exception:
            return "free"
    
    async def check_rate_limit(self, client_ip: str, user_id: Optional[str], tier: str) -> bool:
        """Check if request is within rate limits."""
        try:
            limits = self.tier_limits.get(tier, {
                "requests": self.default_requests,
                "window": self.default_window
            })
            
            # Use user ID if available, otherwise IP
            key = f"rate_limit:{user_id or client_ip}:{tier}"
            
            current_time = int(time.time())
            window_start = current_time - limits["window"]
            
            # Clean old entries
            redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = redis_client.zcard(key)
            
            if current_requests >= limits["requests"]:
                return False
            
            # Add current request
            redis_client.zadd(key, {str(current_time): current_time})
            redis_client.expire(key, limits["window"])
            
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Fail open in case of Redis issues


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all API requests for security auditing."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture request details
        request_data = await self.capture_request_data(request)
        
        response = await call_next(request)
        
        # Capture response details
        process_time = time.time() - start_time
        response_data = self.capture_response_data(response, process_time)
        
        # Log the audit entry
        await self.log_audit_entry(request_data, response_data)
        
        return response
    
    async def capture_request_data(self, request: Request) -> Dict[str, Any]:
        """Capture relevant request data for auditing."""
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
            "auth_header": bool(request.headers.get("Authorization")),
            "content_type": request.headers.get("Content-Type", ""),
            "content_length": request.headers.get("Content-Length", 0)
        }
    
    def capture_response_data(self, response: Response, process_time: float) -> Dict[str, Any]:
        """Capture relevant response data for auditing."""
        return {
            "status_code": response.status_code,
            "content_length": response.headers.get("Content-Length", 0),
            "process_time": round(process_time, 3)
        }
    
    async def log_audit_entry(self, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """Log audit entry to database and Redis."""
        try:
            # Create audit log entry
            audit_entry = {
                **request_data,
                **response_data,
                "event_type": "api_request",
                "severity": "info" if response_data["status_code"] < 400 else "warning"
            }
            
            # Store in Redis for real-time monitoring
            redis_key = f"audit_log:{datetime.utcnow().strftime('%Y-%m-%d')}"
            redis_client.lpush(redis_key, json.dumps(audit_entry))
            redis_client.expire(redis_key, 86400 * 7)  # Keep for 7 days
            
            # In production, also store in database
            # await store_audit_log_to_db(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")


class DataEncryptionMiddleware(BaseHTTPMiddleware):
    """Encrypt sensitive data in requests/responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_fields = {
            "password", "token", "secret", "key", "private_key",
            "wallet_address", "mnemonic", "seed"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Process request
        await self.process_request(request)
        
        response = await call_next(request)
        
        # Process response
        await self.process_response(response)
        
        return response
    
    async def process_request(self, request: Request):
        """Scan and encrypt sensitive data in requests."""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    # In production, implement actual encryption
                    pass
        except Exception as e:
            logger.error(f"Request encryption processing failed: {e}")
    
    async def process_response(self, response: Response):
        """Scan and encrypt sensitive data in responses."""
        try:
            # In production, implement response data encryption
            pass
        except Exception as e:
            logger.error(f"Response encryption processing failed: {e}")


class SecurityEventDetector(BaseHTTPMiddleware):
    """Detect and respond to security events."""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r"(?i)(select|union|insert|delete|drop|create|alter)",  # SQL injection
            r"(?i)(<script|javascript:|vbscript:|onload=|onerror=)",  # XSS
            r"(?i)(\.\.\/|\.\.\\)",  # Path traversal
            r"(?i)(eval\(|exec\(|system\()",  # Code injection
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check for suspicious activity
        security_event = await self.detect_security_event(request)
        
        if security_event:
            await self.handle_security_event(request, security_event)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Security violation detected",
                    "message": "Request blocked due to suspicious activity"
                }
            )
        
        response = await call_next(request)
        return response
    
    async def detect_security_event(self, request: Request) -> Optional[str]:
        """Detect potential security threats."""
        try:
            # Check URL path
            import re
            url_path = str(request.url.path)
            for pattern in self.suspicious_patterns:
                if re.search(pattern, url_path):
                    return f"Suspicious pattern in URL: {pattern}"
            
            # Check query parameters
            query_string = str(request.url.query)
            for pattern in self.suspicious_patterns:
                if re.search(pattern, query_string):
                    return f"Suspicious pattern in query: {pattern}"
            
            # Check for rapid requests (potential DDoS)
            client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
            rapid_requests_key = f"rapid_requests:{client_ip}"
            current_requests = redis_client.incr(rapid_requests_key)
            redis_client.expire(rapid_requests_key, 60)  # 1 minute window
            
            if current_requests > 200:  # More than 200 requests per minute
                return "Potential DDoS attack detected"
            
            return None
        except Exception as e:
            logger.error(f"Security event detection failed: {e}")
            return None
    
    async def handle_security_event(self, request: Request, event: str):
        """Handle detected security events."""
        try:
            client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
            
            # Log security event
            security_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "security_violation",
                "severity": "high",
                "client_ip": client_ip,
                "url": str(request.url),
                "method": request.method,
                "user_agent": request.headers.get("User-Agent", ""),
                "event_description": event
            }
            
            # Store in Redis for immediate alerting
            redis_client.lpush("security_events", json.dumps(security_log))
            redis_client.expire("security_events", 86400 * 30)  # Keep for 30 days
            
            # Increment threat score for IP
            threat_key = f"threat_score:{client_ip}"
            threat_score = redis_client.incr(threat_key)
            redis_client.expire(threat_key, 86400)  # 24 hour window
            
            # Auto-block if threat score is too high
            if threat_score > 10:
                redis_client.setex(f"blocked_ip:{client_ip}", 3600, "auto_blocked")  # Block for 1 hour
            
            logger.warning(f"Security event detected: {event} from {client_ip}")
            
        except Exception as e:
            logger.error(f"Security event handling failed: {e}")
