"""
Enterprise Database Schemas for API requests and responses
Supports multi-tenancy, billing, and usage tracking
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class SubscriptionTierEnum(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class OrganizationRoleEnum(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class APIKeyTypeEnum(str, Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"

class UsageTypeEnum(str, Enum):
    CONTRACT_ANALYSIS = "contract_analysis"
    CONTRACT_GENERATION = "contract_generation"
    AI_ANALYSIS = "ai_analysis"
    API_CALL = "api_call"

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    slug: Optional[str] = Field(None, regex=r'^[a-z0-9-]+$', min_length=3, max_length=50)
    billing_email: Optional[str] = None
    
    @validator('slug')
    def validate_slug(cls, v):
        if v and not v.replace('-', '').isalnum():
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    billing_email: Optional[str] = None
    logo_url: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int
    slug: str
    subscription_tier: SubscriptionTierEnum
    monthly_contract_limit: int
    monthly_ai_analysis_limit: int
    monthly_api_calls_limit: int
    storage_limit_mb: int
    custom_branding: bool
    sso_enabled: bool
    audit_logging: bool
    priority_support: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Organization Member Schemas
class OrganizationMemberBase(BaseModel):
    role: OrganizationRoleEnum
    can_manage_members: bool = False
    can_manage_billing: bool = False
    can_manage_api_keys: bool = False
    can_view_usage: bool = True
    can_create_contracts: bool = True

class OrganizationMemberInvite(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: OrganizationRoleEnum
    can_manage_members: bool = False
    can_manage_billing: bool = False
    can_manage_api_keys: bool = False
    can_view_usage: bool = True
    can_create_contracts: bool = True

class OrganizationMemberUpdate(BaseModel):
    role: Optional[OrganizationRoleEnum] = None
    can_manage_members: Optional[bool] = None
    can_manage_billing: Optional[bool] = None
    can_manage_api_keys: Optional[bool] = None
    can_view_usage: Optional[bool] = None
    can_create_contracts: Optional[bool] = None

class OrganizationMemberResponse(OrganizationMemberBase):
    id: int
    user_id: int
    user_email: str
    user_name: str
    joined_at: datetime
    last_active_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# API Key Schemas
class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    key_type: APIKeyTypeEnum = APIKeyTypeEnum.READ_WRITE
    rate_limit_per_minute: int = Field(60, ge=1, le=1000)
    rate_limit_per_hour: int = Field(1000, ge=1, le=100000)
    rate_limit_per_day: int = Field(10000, ge=1, le=1000000)

class APIKeyCreate(APIKeyBase):
    allowed_endpoints: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    allowed_endpoints: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class APIKeyResponse(APIKeyBase):
    id: int
    key_prefix: str  # Only show first 8 characters
    is_active: bool
    total_calls: int
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyCreateResponse(APIKeyResponse):
    api_key: str  # Full key only shown once on creation

# Usage & Analytics Schemas
class UsageRecordResponse(BaseModel):
    id: int
    usage_type: UsageTypeEnum
    endpoint: Optional[str]
    method: Optional[str]
    tokens_used: int
    processing_time_ms: int
    cost_credits: float
    status_code: Optional[int]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UsageAnalytics(BaseModel):
    total_contract_analyses: int
    total_ai_analyses: int
    total_api_calls: int
    total_storage_used_mb: float
    current_month_usage: Dict[str, int]
    daily_usage_trend: List[Dict[str, Union[str, int]]]  # [{"date": "2024-01-01", "count": 10}]
    top_endpoints: List[Dict[str, Union[str, int]]]     # [{"endpoint": "/api/v1/analyze", "count": 100}]

class BillingUsage(BaseModel):
    current_period_start: datetime
    current_period_end: datetime
    contract_analyses_used: int
    contract_analyses_limit: int
    ai_analyses_used: int
    ai_analyses_limit: int
    api_calls_used: int
    api_calls_limit: int
    storage_used_mb: float
    storage_limit_mb: int
    overage_charges: float = 0.0

# Subscription Management Schemas
class SubscriptionUpdate(BaseModel):
    tier: SubscriptionTierEnum
    billing_email: Optional[str] = None

class SubscriptionResponse(BaseModel):
    tier: SubscriptionTierEnum
    subscription_id: Optional[str]
    billing_email: Optional[str]
    features: Dict[str, Any]
    usage: BillingUsage
    
    class Config:
        from_attributes = True

# Enterprise Settings Schemas
class EnterpriseSettings(BaseModel):
    sso_provider: Optional[str] = None
    sso_domain: Optional[str] = None
    custom_domain: Optional[str] = None
    custom_logo_url: Optional[str] = None
    custom_brand_colors: Optional[Dict[str, str]] = None
    audit_retention_days: int = 90
    ip_whitelist: Optional[List[str]] = None
    require_2fa: bool = False

class EnterpriseSettingsUpdate(BaseModel):
    sso_provider: Optional[str] = None
    sso_domain: Optional[str] = None
    custom_domain: Optional[str] = None
    custom_logo_url: Optional[str] = None
    custom_brand_colors: Optional[Dict[str, str]] = None
    audit_retention_days: Optional[int] = Field(None, ge=30, le=3650)
    ip_whitelist: Optional[List[str]] = None
    require_2fa: Optional[bool] = None

# Audit Log Schemas
class AuditLogEntry(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)

# Team Management Schemas
class TeamOverview(BaseModel):
    total_members: int
    active_members: int
    pending_invitations: int
    members_by_role: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

class TeamInvitation(BaseModel):
    id: int
    email: str
    role: OrganizationRoleEnum
    invited_by: str
    invited_at: datetime
    expires_at: datetime
    status: str  # pending, accepted, expired, revoked
    
    class Config:
        from_attributes = True

# Dashboard Schemas
class OrganizationDashboard(BaseModel):
    organization: OrganizationResponse
    subscription: SubscriptionResponse
    usage_analytics: UsageAnalytics
    team_overview: TeamOverview
    recent_contracts: List[Dict[str, Any]]
    api_key_stats: Dict[str, int]
    
class AdminDashboard(BaseModel):
    total_organizations: int
    total_users: int
    subscription_distribution: Dict[str, int]
    monthly_revenue: float
    top_organizations: List[Dict[str, Any]]
    system_health: Dict[str, Any]
