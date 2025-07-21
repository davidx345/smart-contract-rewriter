"""
Authentication and User Management Models
Enterprise-grade user authentication with role-based access control
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User role enumeration for RBAC"""
    ADMIN = "admin"
    PREMIUM = "premium"
    FREE = "free"
    ENTERPRISE = "enterprise"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# === Authentication Request/Response Models ===

class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    linkedin_profile: Optional[str] = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('linkedin_profile')
    def validate_linkedin_url(cls, v):
        """Validate LinkedIn profile URL format"""
        if v and not re.match(r'https?://(www\.)?linkedin\.com/in/[\w-]+/?', v):
            raise ValueError('Invalid LinkedIn profile URL format')
        return v


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False


class PasswordReset(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class EmailVerification(BaseModel):
    """Email verification model"""
    token: str


class ChangePassword(BaseModel):
    """Change password model"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


# === User Profile Models ===

class UserProfile(BaseModel):
    """User profile update model"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    linkedin_profile: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = "UTC"
    notification_preferences: Optional[Dict[str, bool]] = {
        "email_notifications": True,
        "contract_analysis_complete": True,
        "system_updates": True,
        "marketing": False
    }
    
    @validator('linkedin_profile')
    def validate_linkedin_url(cls, v):
        """Validate LinkedIn profile URL format"""
        if v and not re.match(r'https?://(www\.)?linkedin\.com/in/[\w-]+/?', v):
            raise ValueError('Invalid LinkedIn profile URL format')
        return v


class UserResponse(BaseModel):
    """User response model (safe for API responses)"""
    id: int
    email: str
    full_name: str
    company: Optional[str]
    linkedin_profile: Optional[str]
    bio: Optional[str]
    role: UserRole
    status: UserStatus
    is_verified: bool
    timezone: str
    notification_preferences: Dict[str, bool]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    # Usage statistics
    contracts_analyzed: int = 0
    contracts_generated: int = 0
    api_calls_this_month: int = 0
    
    class Config:
        orm_mode = True


class UserStats(BaseModel):
    """User statistics model"""
    total_contracts_analyzed: int
    total_contracts_generated: int
    total_api_calls: int
    monthly_api_calls: int
    contracts_this_week: int
    average_analysis_time: float
    most_used_features: List[str]
    registration_date: datetime
    last_activity: Optional[datetime]


# === JWT Token Models ===

class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefresh(BaseModel):
    """Token refresh request model"""
    refresh_token: str


class TokenData(BaseModel):
    """Token data for internal use"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    expires_at: Optional[datetime] = None


# === OAuth Models ===

class OAuthProvider(str, Enum):
    """OAuth provider enumeration"""
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"


class OAuthCallback(BaseModel):
    """OAuth callback model"""
    code: str
    state: Optional[str] = None
    provider: OAuthProvider


class OAuthUser(BaseModel):
    """OAuth user data model"""
    provider: OAuthProvider
    provider_id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None


# === API Response Models ===

class AuthResponse(BaseModel):
    """Standard authentication response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# === Rate Limiting Models ===

class RateLimitInfo(BaseModel):
    """Rate limiting information"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


# === Audit Log Models ===

class AuditAction(str, Enum):
    """Audit action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFY = "email_verify"
    PROFILE_UPDATE = "profile_update"
    ROLE_CHANGE = "role_change"
    ACCOUNT_SUSPEND = "account_suspend"
    ACCOUNT_ACTIVATE = "account_activate"
    CONTRACT_ANALYZE = "contract_analyze"
    CONTRACT_GENERATE = "contract_generate"
    API_KEY_CREATE = "api_key_create"
    API_KEY_DELETE = "api_key_delete"


class AuditLog(BaseModel):
    """Audit log entry model"""
    id: int
    user_id: Optional[int]
    action: AuditAction
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: str
    user_agent: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        orm_mode = True
