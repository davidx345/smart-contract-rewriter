"""
Enterprise Organization and Multi-Tenancy Models
Supports multiple organizations with proper data isolation
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .auth_models import User

Base = declarative_base()

class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class APIKeyType(str, Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"

class UsageType(str, Enum):
    CONTRACT_ANALYSIS = "contract_analysis"
    CONTRACT_GENERATION = "contract_generation"
    AI_ANALYSIS = "ai_analysis"
    API_CALL = "api_call"

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Subscription & Billing
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_id = Column(String)  # External billing system ID
    billing_email = Column(String)
    
    # Usage Limits
    monthly_contract_limit = Column(Integer, default=10)
    monthly_ai_analysis_limit = Column(Integer, default=5)
    monthly_api_calls_limit = Column(Integer, default=1000)
    storage_limit_mb = Column(Integer, default=100)
    
    # Enterprise Features
    custom_branding = Column(Boolean, default=False)
    sso_enabled = Column(Boolean, default=False)
    audit_logging = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    
    # Metadata
    logo_url = Column(String)
    website_url = Column(String)
    industry = Column(String)
    company_size = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="organization", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(name='{self.name}', tier='{self.subscription_tier}')>"

class OrganizationMember(Base):
    __tablename__ = "organization_members"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(OrganizationRole), nullable=False)
    
    # Permissions
    can_manage_members = Column(Boolean, default=False)
    can_manage_billing = Column(Boolean, default=False)
    can_manage_api_keys = Column(Boolean, default=False)
    can_view_usage = Column(Boolean, default=True)
    can_create_contracts = Column(Boolean, default=True)
    
    # Metadata
    invited_by_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_org_member_unique', 'organization_id', 'user_id', unique=True),
    )

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Key Details
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    key_prefix = Column(String, nullable=False)  # First 8 chars for display
    key_type = Column(SQLEnum(APIKeyType), default=APIKeyType.READ_WRITE)
    
    # Status & Limits
    is_active = Column(Boolean, default=True)
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_day = Column(Integer, default=10000)
    
    # Permissions
    allowed_endpoints = Column(JSON)  # List of allowed API endpoints
    ip_whitelist = Column(JSON)  # List of allowed IP addresses
    
    # Usage Tracking
    total_calls = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="api_keys")
    created_by = relationship("User")
    usage_records = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    
    # Usage Details
    usage_type = Column(SQLEnum(UsageType), nullable=False)
    endpoint = Column(String)
    method = Column(String)
    
    # Metrics
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    cost_credits = Column(Numeric(10, 4), default=0.0)  # Internal credits
    
    # Request Details
    request_size_bytes = Column(Integer, default=0)
    response_size_bytes = Column(Integer, default=0)
    status_code = Column(Integer)
    error_message = Column(Text)
    
    # Metadata
    user_agent = Column(String)
    ip_address = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="usage_records")
    user = relationship("User")
    api_key = relationship("APIKey")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_usage_org_timestamp', 'organization_id', 'timestamp'),
        Index('idx_usage_type_timestamp', 'usage_type', 'timestamp'),
    )

class APIKeyUsage(Base):
    __tablename__ = "api_key_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    
    # Rate Limiting Buckets
    minute_bucket = Column(String, nullable=False)  # Format: YYYY-MM-DD-HH-MM
    hour_bucket = Column(String, nullable=False)    # Format: YYYY-MM-DD-HH
    day_bucket = Column(String, nullable=False)     # Format: YYYY-MM-DD
    
    # Counters
    calls_this_minute = Column(Integer, default=0)
    calls_this_hour = Column(Integer, default=0)
    calls_this_day = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_minute', 'api_key_id', 'minute_bucket', unique=True),
        Index('idx_api_key_hour', 'api_key_id', 'hour_bucket'),
        Index('idx_api_key_day', 'api_key_id', 'day_bucket'),
    )

class SubscriptionFeature(Base):
    __tablename__ = "subscription_features"
    
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(SQLEnum(SubscriptionTier), nullable=False)
    feature_key = Column(String, nullable=False)
    feature_name = Column(String, nullable=False)
    
    # Feature Limits
    limit_value = Column(Integer)  # Numeric limit (e.g., 100 API calls)
    enabled = Column(Boolean, default=True)
    
    # Feature Configuration
    config = Column(JSON)  # Additional feature configuration
    
    # Indexes
    __table_args__ = (
        Index('idx_tier_feature', 'tier', 'feature_key', unique=True),
    )

# Define default subscription features
DEFAULT_SUBSCRIPTION_FEATURES = {
    SubscriptionTier.FREE: {
        "contract_analysis": {"limit": 10, "enabled": True},
        "ai_analysis": {"limit": 5, "enabled": True},
        "api_calls": {"limit": 1000, "enabled": True},
        "storage_mb": {"limit": 100, "enabled": True},
        "team_members": {"limit": 1, "enabled": True},
        "priority_support": {"limit": 0, "enabled": False},
        "custom_branding": {"limit": 0, "enabled": False},
        "sso": {"limit": 0, "enabled": False},
        "audit_logging": {"limit": 0, "enabled": False}
    },
    SubscriptionTier.STARTER: {
        "contract_analysis": {"limit": 100, "enabled": True},
        "ai_analysis": {"limit": 50, "enabled": True},
        "api_calls": {"limit": 10000, "enabled": True},
        "storage_mb": {"limit": 1000, "enabled": True},
        "team_members": {"limit": 5, "enabled": True},
        "priority_support": {"limit": 0, "enabled": False},
        "custom_branding": {"limit": 0, "enabled": False},
        "sso": {"limit": 0, "enabled": False},
        "audit_logging": {"limit": 1, "enabled": True}
    },
    SubscriptionTier.PROFESSIONAL: {
        "contract_analysis": {"limit": 500, "enabled": True},
        "ai_analysis": {"limit": 200, "enabled": True},
        "api_calls": {"limit": 50000, "enabled": True},
        "storage_mb": {"limit": 5000, "enabled": True},
        "team_members": {"limit": 20, "enabled": True},
        "priority_support": {"limit": 1, "enabled": True},
        "custom_branding": {"limit": 1, "enabled": True},
        "sso": {"limit": 0, "enabled": False},
        "audit_logging": {"limit": 1, "enabled": True}
    },
    SubscriptionTier.ENTERPRISE: {
        "contract_analysis": {"limit": -1, "enabled": True},  # -1 = unlimited
        "ai_analysis": {"limit": -1, "enabled": True},
        "api_calls": {"limit": -1, "enabled": True},
        "storage_mb": {"limit": -1, "enabled": True},
        "team_members": {"limit": -1, "enabled": True},
        "priority_support": {"limit": 1, "enabled": True},
        "custom_branding": {"limit": 1, "enabled": True},
        "sso": {"limit": 1, "enabled": True},
        "audit_logging": {"limit": 1, "enabled": True}
    }
}
