"""
Enterprise Organization Management Service
Handles multi-tenancy, billing, usage tracking, and team management
"""

import secrets
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from fastapi import HTTPException, status

from ..models.enterprise_models import (
    Organization, OrganizationMember, APIKey, UsageRecord, 
    SubscriptionFeature, APIKeyUsage, SubscriptionTier, 
    OrganizationRole, APIKeyType, UsageType, DEFAULT_SUBSCRIPTION_FEATURES
)
from ..models.auth_models import User
from ..schemas.enterprise_schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationMemberInvite,
    APIKeyCreate, UsageAnalytics, BillingUsage, SubscriptionUpdate
)
from .auth_service import create_access_token
import logging

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing organizations and multi-tenancy"""
    
    @staticmethod
    def create_organization(db: Session, org_data: OrganizationCreate, owner_id: int) -> Organization:
        """Create a new organization with the user as owner"""
        try:
            # Generate slug if not provided
            if not org_data.slug:
                org_data.slug = org_data.name.lower().replace(' ', '-').replace('_', '-')
                # Ensure slug is unique
                counter = 1
                base_slug = org_data.slug
                while db.query(Organization).filter(Organization.slug == org_data.slug).first():
                    org_data.slug = f"{base_slug}-{counter}"
                    counter += 1
            
            # Check if slug is already taken
            if db.query(Organization).filter(Organization.slug == org_data.slug).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization slug already exists"
                )
            
            # Create organization
            organization = Organization(
                name=org_data.name,
                slug=org_data.slug,
                description=org_data.description,
                website_url=org_data.website_url,
                industry=org_data.industry,
                company_size=org_data.company_size,
                billing_email=org_data.billing_email or db.query(User).filter(User.id == owner_id).first().email,
                subscription_tier=SubscriptionTier.FREE
            )
            db.add(organization)
            db.flush()  # Get the ID
            
            # Add owner as member
            owner_member = OrganizationMember(
                organization_id=organization.id,
                user_id=owner_id,
                role=OrganizationRole.OWNER,
                can_manage_members=True,
                can_manage_billing=True,
                can_manage_api_keys=True,
                can_view_usage=True,
                can_create_contracts=True
            )
            db.add(owner_member)
            
            # Initialize default subscription features
            OrganizationService._initialize_subscription_features(db, organization.id, SubscriptionTier.FREE)
            
            db.commit()
            db.refresh(organization)
            
            logger.info(f"Created organization {organization.slug} for user {owner_id}")
            return organization
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
    
    @staticmethod
    def get_user_organizations(db: Session, user_id: int) -> List[Organization]:
        """Get all organizations where user is a member"""
        return db.query(Organization).join(OrganizationMember).filter(
            OrganizationMember.user_id == user_id
        ).all()
    
    @staticmethod
    def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return db.query(Organization).filter(Organization.slug == slug).first()
    
    @staticmethod
    def update_organization(db: Session, org_id: int, org_data: OrganizationUpdate, user_id: int) -> Organization:
        """Update organization (admin/owner only)"""
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Check permissions
        member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.role.in_([OrganizationRole.OWNER, OrganizationRole.ADMIN])
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Update fields
        for field, value in org_data.dict(exclude_unset=True).items():
            setattr(organization, field, value)
        
        organization.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(organization)
        
        return organization
    
    @staticmethod
    def _initialize_subscription_features(db: Session, org_id: int, tier: SubscriptionTier):
        """Initialize subscription features for an organization"""
        features = DEFAULT_SUBSCRIPTION_FEATURES.get(tier, {})
        for feature_key, config in features.items():
            feature = SubscriptionFeature(
                tier=tier,
                feature_key=feature_key,
                feature_name=feature_key.replace('_', ' ').title(),
                limit_value=config['limit'],
                enabled=config['enabled'],
                config=config
            )
            db.add(feature)

class TeamService:
    """Service for managing team members"""
    
    @staticmethod
    def invite_member(db: Session, org_id: int, invite_data: OrganizationMemberInvite, inviter_id: int) -> Dict[str, str]:
        """Invite a user to join the organization"""
        # Check inviter permissions
        inviter = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == inviter_id,
                OrganizationMember.can_manage_members == True
            )
        ).first()
        
        if not inviter:
            raise HTTPException(status_code=403, detail="Insufficient permissions to invite members")
        
        # Check if user already exists
        user = db.query(User).filter(User.email == invite_data.email).first()
        if not user:
            # For now, require user to register first
            raise HTTPException(
                status_code=404, 
                detail="User must register first before being invited"
            )
        
        # Check if already a member
        existing_member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user.id
            )
        ).first()
        
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member")
        
        # Create membership
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user.id,
            role=invite_data.role,
            can_manage_members=invite_data.can_manage_members,
            can_manage_billing=invite_data.can_manage_billing,
            can_manage_api_keys=invite_data.can_manage_api_keys,
            can_view_usage=invite_data.can_view_usage,
            can_create_contracts=invite_data.can_create_contracts,
            invited_by_id=inviter_id
        )
        db.add(member)
        db.commit()
        
        return {"message": f"User {invite_data.email} added to organization"}
    
    @staticmethod
    def get_organization_members(db: Session, org_id: int, user_id: int) -> List[OrganizationMember]:
        """Get all members of an organization"""
        # Check user has access to this organization
        member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id
        ).all()
    
    @staticmethod
    def remove_member(db: Session, org_id: int, member_id: int, remover_id: int) -> Dict[str, str]:
        """Remove a member from the organization"""
        # Check permissions
        remover = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == remover_id,
                OrganizationMember.can_manage_members == True
            )
        ).first()
        
        if not remover:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get member to remove
        member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.id == member_id
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Can't remove owner
        if member.role == OrganizationRole.OWNER:
            raise HTTPException(status_code=400, detail="Cannot remove organization owner")
        
        db.delete(member)
        db.commit()
        
        return {"message": "Member removed successfully"}

class APIKeyService:
    """Service for managing API keys"""
    
    @staticmethod
    def create_api_key(db: Session, org_id: int, key_data: APIKeyCreate, creator_id: int) -> Tuple[APIKey, str]:
        """Create a new API key"""
        # Check permissions
        member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == creator_id,
                OrganizationMember.can_manage_api_keys == True
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="Insufficient permissions to create API keys")
        
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:8]
        
        # Create API key record
        api_key_record = APIKey(
            organization_id=org_id,
            created_by_id=creator_id,
            name=key_data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            key_type=key_data.key_type,
            rate_limit_per_minute=key_data.rate_limit_per_minute,
            rate_limit_per_hour=key_data.rate_limit_per_hour,
            rate_limit_per_day=key_data.rate_limit_per_day,
            allowed_endpoints=key_data.allowed_endpoints,
            ip_whitelist=key_data.ip_whitelist,
            expires_at=key_data.expires_at
        )
        
        db.add(api_key_record)
        db.commit()
        db.refresh(api_key_record)
        
        return api_key_record, api_key
    
    @staticmethod
    def get_organization_api_keys(db: Session, org_id: int, user_id: int) -> List[APIKey]:
        """Get all API keys for an organization"""
        # Check permissions
        member = db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return db.query(APIKey).filter(APIKey.organization_id == org_id).all()
    
    @staticmethod
    def verify_api_key(db: Session, api_key: str) -> Optional[APIKey]:
        """Verify and return API key if valid"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_record = db.query(APIKey).filter(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
                or_(APIKey.expires_at.is_(None), APIKey.expires_at > datetime.utcnow())
            )
        ).first()
        
        if api_key_record:
            # Update last used timestamp
            api_key_record.last_used_at = datetime.utcnow()
            db.commit()
        
        return api_key_record
    
    @staticmethod
    def check_rate_limit(db: Session, api_key_id: int) -> bool:
        """Check if API key has exceeded rate limits"""
        now = datetime.utcnow()
        minute_bucket = now.strftime('%Y-%m-%d-%H-%M')
        hour_bucket = now.strftime('%Y-%m-%d-%H')
        day_bucket = now.strftime('%Y-%m-%d')
        
        # Get or create usage record
        usage = db.query(APIKeyUsage).filter(
            and_(
                APIKeyUsage.api_key_id == api_key_id,
                APIKeyUsage.minute_bucket == minute_bucket
            )
        ).first()
        
        if not usage:
            usage = APIKeyUsage(
                api_key_id=api_key_id,
                minute_bucket=minute_bucket,
                hour_bucket=hour_bucket,
                day_bucket=day_bucket,
                calls_this_minute=0,
                calls_this_hour=0,
                calls_this_day=0
            )
            db.add(usage)
        
        # Get API key limits
        api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        
        # Check limits
        if usage.calls_this_minute >= api_key.rate_limit_per_minute:
            return False
        if usage.calls_this_hour >= api_key.rate_limit_per_hour:
            return False
        if usage.calls_this_day >= api_key.rate_limit_per_day:
            return False
        
        # Increment counters
        usage.calls_this_minute += 1
        usage.calls_this_hour += 1
        usage.calls_this_day += 1
        usage.updated_at = now
        
        db.commit()
        return True

class UsageService:
    """Service for tracking and analyzing usage"""
    
    @staticmethod
    def record_usage(
        db: Session, 
        org_id: int, 
        usage_type: UsageType,
        user_id: Optional[int] = None,
        api_key_id: Optional[int] = None,
        **kwargs
    ) -> UsageRecord:
        """Record a usage event"""
        usage_record = UsageRecord(
            organization_id=org_id,
            user_id=user_id,
            api_key_id=api_key_id,
            usage_type=usage_type,
            endpoint=kwargs.get('endpoint'),
            method=kwargs.get('method'),
            tokens_used=kwargs.get('tokens_used', 0),
            processing_time_ms=kwargs.get('processing_time_ms', 0),
            cost_credits=kwargs.get('cost_credits', 0.0),
            request_size_bytes=kwargs.get('request_size_bytes', 0),
            response_size_bytes=kwargs.get('response_size_bytes', 0),
            status_code=kwargs.get('status_code'),
            error_message=kwargs.get('error_message'),
            user_agent=kwargs.get('user_agent'),
            ip_address=kwargs.get('ip_address')
        )
        
        db.add(usage_record)
        db.commit()
        return usage_record
    
    @staticmethod
    def get_usage_analytics(db: Session, org_id: int, days: int = 30) -> UsageAnalytics:
        """Get usage analytics for an organization"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total counts
        total_analyses = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.CONTRACT_ANALYSIS
            )
        ).count()
        
        total_ai_analyses = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.AI_ANALYSIS
            )
        ).count()
        
        total_api_calls = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.API_CALL
            )
        ).count()
        
        # Current month usage
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_usage = {}
        
        for usage_type in UsageType:
            count = db.query(UsageRecord).filter(
                and_(
                    UsageRecord.organization_id == org_id,
                    UsageRecord.usage_type == usage_type,
                    UsageRecord.timestamp >= current_month_start
                )
            ).count()
            current_month_usage[usage_type.value] = count
        
        # Daily usage trend
        daily_usage = db.query(
            func.date(UsageRecord.timestamp).label('date'),
            func.count(UsageRecord.id).label('count')
        ).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.timestamp >= start_date
            )
        ).group_by(func.date(UsageRecord.timestamp)).all()
        
        daily_usage_trend = [
            {"date": str(record.date), "count": record.count} 
            for record in daily_usage
        ]
        
        # Top endpoints
        top_endpoints = db.query(
            UsageRecord.endpoint,
            func.count(UsageRecord.id).label('count')
        ).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.timestamp >= start_date,
                UsageRecord.endpoint.isnot(None)
            )
        ).group_by(UsageRecord.endpoint).order_by(func.count(UsageRecord.id).desc()).limit(10).all()
        
        top_endpoints_list = [
            {"endpoint": record.endpoint, "count": record.count}
            for record in top_endpoints
        ]
        
        return UsageAnalytics(
            total_contract_analyses=total_analyses,
            total_ai_analyses=total_ai_analyses,
            total_api_calls=total_api_calls,
            total_storage_used_mb=0.0,  # TODO: Implement storage tracking
            current_month_usage=current_month_usage,
            daily_usage_trend=daily_usage_trend,
            top_endpoints=top_endpoints_list
        )
    
    @staticmethod
    def get_billing_usage(db: Session, org_id: int) -> BillingUsage:
        """Get current billing period usage"""
        # Get organization
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Current billing period (monthly)
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Get usage counts for current period
        contract_analyses_used = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.CONTRACT_ANALYSIS,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp <= period_end
            )
        ).count()
        
        ai_analyses_used = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.AI_ANALYSIS,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp <= period_end
            )
        ).count()
        
        api_calls_used = db.query(UsageRecord).filter(
            and_(
                UsageRecord.organization_id == org_id,
                UsageRecord.usage_type == UsageType.API_CALL,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp <= period_end
            )
        ).count()
        
        return BillingUsage(
            current_period_start=period_start,
            current_period_end=period_end,
            contract_analyses_used=contract_analyses_used,
            contract_analyses_limit=org.monthly_contract_limit,
            ai_analyses_used=ai_analyses_used,
            ai_analyses_limit=org.monthly_ai_analysis_limit,
            api_calls_used=api_calls_used,
            api_calls_limit=org.monthly_api_calls_limit,
            storage_used_mb=0.0,  # TODO: Implement
            storage_limit_mb=org.storage_limit_mb,
            overage_charges=0.0  # TODO: Implement overage billing
        )
