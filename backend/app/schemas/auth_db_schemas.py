"""
Authentication Database Schema
Enterprise-grade user management with audit trails and security features
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid

from app.schemas.contract_db_schemas import Base


class User(Base):
    """
    Core user model with enterprise features
    Includes role-based access control, audit trails, and security features
    """
    __tablename__ = "users"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Profile information
    full_name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    linkedin_profile = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Role and permissions
    role = Column(String(20), default="free", nullable=False)  # admin, premium, free, enterprise
    status = Column(String(20), default="pending_verification", nullable=False)  # active, inactive, suspended
    
    # Settings and preferences
    notification_preferences = Column(JSON, default={
        "email_notifications": True,
        "contract_analysis_complete": True,
        "system_updates": True,
        "marketing": False
    })
    
    # Security and audit
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    last_login_user_agent = Column(Text, nullable=True)
    
    # Usage statistics
    contracts_analyzed = Column(Integer, default=0, nullable=False)
    contracts_generated = Column(Integer, default=0, nullable=False)
    api_calls_total = Column(Integer, default=0, nullable=False)
    api_calls_this_month = Column(Integer, default=0, nullable=False)
    api_calls_reset_date = Column(DateTime(timezone=True), default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email_status', 'email', 'status'),
        Index('idx_user_role_status', 'role', 'status'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_last_login', 'last_login'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class OAuthAccount(Base):
    """
    OAuth account linking for social authentication
    Supports Google, GitHub, LinkedIn, etc.
    """
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, github, linkedin
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255), nullable=True)
    provider_username = Column(String(255), nullable=True)
    provider_avatar_url = Column(String(500), nullable=True)
    provider_profile_url = Column(String(500), nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional provider data
    provider_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_provider_user'),
        Index('idx_oauth_user_provider', 'user_id', 'provider'),
    )


class ApiKey(Base):
    """
    API key management for programmatic access
    Supports rate limiting and usage tracking
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key identification
    key_id = Column(String(50), unique=True, index=True, nullable=False)  # Public identifier
    key_hash = Column(String(255), nullable=False)  # Hashed secret
    name = Column(String(100), nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)
    
    # Permissions and limits
    permissions = Column(JSON, default=["read"], nullable=False)  # read, write, admin
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_day = Column(Integer, default=1000, nullable=False)
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Status and security
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_user_active', 'user_id', 'is_active'),
        Index('idx_api_key_expires', 'expires_at'),
    )


class UserSession(Base):
    """
    User session management for security and audit
    Tracks active sessions across devices
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session identification
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token_hash = Column(String(255), nullable=False)
    
    # Device and location info
    device_info = Column(JSON, nullable=True)  # Device fingerprint
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    geolocation = Column(JSON, nullable=True)  # Country, city, etc.
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Security flags
    is_remember_me = Column(Boolean, default=False, nullable=False)
    is_suspicious = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_last_activity', 'last_activity'),
    )


class AuditLog(Base):
    """
    Comprehensive audit logging for security and compliance
    Tracks all user actions and system events
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User and session info
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # login, logout, contract_analyze, etc.
    resource_type = Column(String(50), nullable=True)  # contract, user, api_key, etc.
    resource_id = Column(String(255), nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)  # For request tracing
    
    # Additional data
    metadata = Column(JSON, nullable=True)  # Action-specific data
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action_resource', 'action', 'resource_type'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
    )


class RateLimitEntry(Base):
    """
    Rate limiting tracking table
    Supports multiple rate limiting strategies
    """
    __tablename__ = "rate_limit_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rate limit identification
    identifier = Column(String(255), nullable=False)  # user_id, ip_address, api_key
    limit_type = Column(String(50), nullable=False)  # per_minute, per_hour, per_day
    resource = Column(String(100), nullable=False)  # api_endpoint, action_type
    
    # Limit tracking
    request_count = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('identifier', 'limit_type', 'resource', 'window_start', 
                        name='uq_rate_limit_window'),
        Index('idx_rate_limit_window', 'window_end'),
        Index('idx_rate_limit_identifier', 'identifier', 'limit_type'),
    )


class SecurityEvent(Base):
    """
    Security event logging for threat detection
    Tracks suspicious activities and security incidents
    """
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event classification
    event_type = Column(String(50), nullable=False)  # failed_login, suspicious_request, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    status = Column(String(20), default="open", nullable=False)  # open, investigating, resolved
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    
    # Event details
    description = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Risk assessment
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100
    false_positive = Column(Boolean, default=False, nullable=False)
    
    # Resolution
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_security_event_type_severity', 'event_type', 'severity'),
        Index('idx_security_event_status', 'status'),
        Index('idx_security_event_timestamp', 'timestamp'),
        Index('idx_security_event_ip', 'ip_address'),
    )
