"""
Authentication Dependencies
FastAPI dependencies for user authentication and authorization
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.schemas.auth_db_schemas import User
from app.models.auth_models import TokenData, UserRole


# Security scheme
security = HTTPBearer()


class AuthenticationDependency:
    """Authentication dependency class"""
    
    def __init__(self, required_roles: Optional[List[UserRole]] = None, 
                 optional: bool = False):
        self.required_roles = required_roles or []
        self.optional = optional
    
    def __call__(self, 
                 request: Request,
                 credentials: HTTPAuthorizationCredentials = Depends(security),
                 db: Session = Depends(get_db)) -> Optional[User]:
        """
        Authentication dependency that validates JWT tokens
        """
        if self.optional and not credentials:
            return None
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if token is blacklisted
        if auth_service.is_token_blacklisted(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials, "access")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Check role permissions
        if self.required_roles and user.role not in [role.value for role in self.required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return user


# === Pre-configured Dependencies ===

# Basic authentication (any active user)
get_current_user = AuthenticationDependency()

# Optional authentication (for public endpoints that can benefit from user context)
get_current_user_optional = AuthenticationDependency(optional=True)

# Admin only
get_admin_user = AuthenticationDependency(required_roles=[UserRole.ADMIN])

# Premium users and above
get_premium_user = AuthenticationDependency(
    required_roles=[UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN]
)

# Enterprise users and admins
get_enterprise_user = AuthenticationDependency(
    required_roles=[UserRole.ENTERPRISE, UserRole.ADMIN]
)


# === Alternative Dependencies ===

async def get_current_active_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current active user (alternative implementation)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check blacklist
    if auth_service.is_token_blacklisted(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    token_data = auth_service.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_user_with_refresh(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[User, bool]:
    """
    Get current user and indicate if token needs refresh
    Returns (user, needs_refresh)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = auth_service.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Check if token expires soon (within 5 minutes)
    from datetime import datetime, timezone, timedelta
    needs_refresh = (
        token_data.expires_at and 
        token_data.expires_at - datetime.now(timezone.utc) < timedelta(minutes=5)
    )
    
    return user, needs_refresh


# === Role-based Dependency Factory ===

def require_roles(*roles: UserRole):
    """
    Factory function to create role-based dependencies
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(UserRole.ADMIN))):
            pass
    """
    async def role_dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        user = await get_current_active_user(request, credentials, db)
        
        if user.role not in [role.value for role in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(role.value for role in roles)}"
            )
        
        return user
    
    return role_dependency


# === Permission-based Dependencies ===

def require_permissions(*permissions: str):
    """
    Factory function to create permission-based dependencies
    
    Usage:
        @app.get("/contracts")
        async def get_contracts(user: User = Depends(require_permissions("contract:read"))):
            pass
    """
    async def permission_dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        user = await get_current_active_user(request, credentials, db)
        
        # Check user permissions (stored in user.permissions JSON field or related table)
        user_permissions = getattr(user, 'permissions', [])
        
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {permission}"
                )
        
        return user
    
    return permission_dependency


# === Rate Limiting Dependencies ===

async def check_rate_limit(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> None:
    """
    Rate limiting dependency
    """
    from app.services.rate_limit_service import rate_limiter
    
    # Determine identifier and limits based on user
    if user:
        identifier = f"user:{user.id}"
        if user.role == UserRole.FREE.value:
            limit = 100  # 100 requests per hour
        elif user.role == UserRole.PREMIUM.value:
            limit = 1000  # 1000 requests per hour
        elif user.role == UserRole.ENTERPRISE.value:
            limit = 10000  # 10000 requests per hour
        else:  # admin
            limit = 50000  # 50000 requests per hour
    else:
        # Anonymous user - limit by IP
        identifier = f"ip:{auth_service._get_client_ip(request)}"
        limit = 50  # 50 requests per hour for anonymous users
    
    # Check rate limit
    allowed = await rate_limiter.check_rate_limit(
        identifier, limit, window_seconds=3600, db=db
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


# === Audit Logging Dependency ===

async def log_api_access(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> None:
    """
    Audit logging dependency for API access
    """
    if user:
        from app.models.auth_models import AuditAction
        auth_service._create_audit_log(
            db, user.id, AuditAction.API_ACCESS, request,
            metadata={
                "endpoint": str(request.url.path),
                "method": request.method,
                "user_role": user.role
            }
        )


# === Security Headers Dependency ===

async def add_security_headers(request: Request) -> dict:
    """
    Add security headers to response
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
