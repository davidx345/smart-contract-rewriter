"""
Enterprise API Endpoints
Organization management, team collaboration, billing, and usage analytics
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...db.session import get_db
from ...services.enterprise_service import OrganizationService, TeamService, APIKeyService, UsageService
from ...services.auth_service import get_current_user
from ...models.auth_models import User
from ...models.enterprise_models import Organization, OrganizationMember, APIKey
from ...schemas.enterprise_schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationMemberInvite, OrganizationMemberResponse, OrganizationMemberUpdate,
    APIKeyCreate, APIKeyCreateResponse, APIKeyResponse, APIKeyUpdate,
    UsageAnalytics, BillingUsage, SubscriptionUpdate, SubscriptionResponse,
    OrganizationDashboard, TeamOverview
)

router = APIRouter(prefix="/enterprise", tags=["enterprise"])

# Organization Management
@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    return OrganizationService.create_organization(db, org_data, current_user.id)

@router.get("/organizations", response_model=List[OrganizationResponse])
async def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all organizations where user is a member"""
    return OrganizationService.get_user_organizations(db, current_user.id)

@router.get("/organizations/{org_slug}", response_model=OrganizationResponse)
async def get_organization(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization by slug"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if user is a member
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return organization

@router.put("/organizations/{org_slug}", response_model=OrganizationResponse)
async def update_organization(
    org_slug: str,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update organization (admin/owner only)"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return OrganizationService.update_organization(db, organization.id, org_data, current_user.id)

@router.get("/organizations/{org_slug}/dashboard", response_model=OrganizationDashboard)
async def get_organization_dashboard(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive organization dashboard data"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check access
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get analytics and stats
    usage_analytics = UsageService.get_usage_analytics(db, organization.id)
    billing_usage = UsageService.get_billing_usage(db, organization.id)
    
    # Team overview
    members = TeamService.get_organization_members(db, organization.id, current_user.id)
    team_overview = TeamOverview(
        total_members=len(members),
        active_members=len([m for m in members if m.last_active_at]),
        pending_invitations=0,  # TODO: Implement invitations
        members_by_role={
            "owner": len([m for m in members if m.role == "owner"]),
            "admin": len([m for m in members if m.role == "admin"]),
            "member": len([m for m in members if m.role == "member"]),
            "viewer": len([m for m in members if m.role == "viewer"])
        },
        recent_activity=[]  # TODO: Implement activity feed
    )
    
    # API key stats
    api_keys = APIKeyService.get_organization_api_keys(db, organization.id, current_user.id)
    api_key_stats = {
        "total": len(api_keys),
        "active": len([k for k in api_keys if k.is_active]),
        "inactive": len([k for k in api_keys if not k.is_active])
    }
    
    return OrganizationDashboard(
        organization=organization,
        subscription=SubscriptionResponse(
            tier=organization.subscription_tier,
            subscription_id=organization.subscription_id,
            billing_email=organization.billing_email,
            features={},  # TODO: Load from subscription features
            usage=billing_usage
        ),
        usage_analytics=usage_analytics,
        team_overview=team_overview,
        recent_contracts=[],  # TODO: Load recent contracts
        api_key_stats=api_key_stats
    )

# Team Management
@router.post("/organizations/{org_slug}/members")
async def invite_member(
    org_slug: str,
    invite_data: OrganizationMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join the organization"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return TeamService.invite_member(db, organization.id, invite_data, current_user.id)

@router.get("/organizations/{org_slug}/members", response_model=List[OrganizationMemberResponse])
async def get_organization_members(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all members of the organization"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    members = TeamService.get_organization_members(db, organization.id, current_user.id)
    
    # Convert to response format with user details
    response_members = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        response_members.append(OrganizationMemberResponse(
            id=member.id,
            user_id=member.user_id,
            user_email=user.email,
            user_name=f"{user.first_name} {user.last_name}".strip() or user.email,
            role=member.role,
            can_manage_members=member.can_manage_members,
            can_manage_billing=member.can_manage_billing,
            can_manage_api_keys=member.can_manage_api_keys,
            can_view_usage=member.can_view_usage,
            can_create_contracts=member.can_create_contracts,
            joined_at=member.joined_at,
            last_active_at=member.last_active_at
        ))
    
    return response_members

@router.delete("/organizations/{org_slug}/members/{member_id}")
async def remove_member(
    org_slug: str,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return TeamService.remove_member(db, organization.id, member_id, current_user.id)

# API Key Management
@router.post("/organizations/{org_slug}/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    org_slug: str,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    api_key_record, api_key = APIKeyService.create_api_key(db, organization.id, key_data, current_user.id)
    
    return APIKeyCreateResponse(
        id=api_key_record.id,
        name=api_key_record.name,
        key_prefix=api_key_record.key_prefix,
        key_type=api_key_record.key_type,
        rate_limit_per_minute=api_key_record.rate_limit_per_minute,
        rate_limit_per_hour=api_key_record.rate_limit_per_hour,
        rate_limit_per_day=api_key_record.rate_limit_per_day,
        is_active=api_key_record.is_active,
        total_calls=api_key_record.total_calls,
        last_used_at=api_key_record.last_used_at,
        expires_at=api_key_record.expires_at,
        created_at=api_key_record.created_at,
        api_key=api_key  # Full key only shown once
    )

@router.get("/organizations/{org_slug}/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for the organization"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    api_keys = APIKeyService.get_organization_api_keys(db, organization.id, current_user.id)
    
    return [APIKeyResponse(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        key_type=key.key_type,
        rate_limit_per_minute=key.rate_limit_per_minute,
        rate_limit_per_hour=key.rate_limit_per_hour,
        rate_limit_per_day=key.rate_limit_per_day,
        is_active=key.is_active,
        total_calls=key.total_calls,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at,
        created_at=key.created_at
    ) for key in api_keys]

@router.put("/organizations/{org_slug}/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    org_slug: str,
    key_id: int,
    key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API key"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.can_manage_api_keys == True
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get and update API key
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.organization_id == organization.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Update fields
    for field, value in key_data.dict(exclude_unset=True).items():
        setattr(api_key, field, value)
    
    db.commit()
    db.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key_type=api_key.key_type,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        rate_limit_per_day=api_key.rate_limit_per_day,
        is_active=api_key.is_active,
        total_calls=api_key.total_calls,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at
    )

@router.delete("/organizations/{org_slug}/api-keys/{key_id}")
async def delete_api_key(
    org_slug: str,
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.can_manage_api_keys == True
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Delete API key
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.organization_id == organization.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}

# Usage Analytics
@router.get("/organizations/{org_slug}/analytics", response_model=UsageAnalytics)
async def get_usage_analytics(
    org_slug: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage analytics for the organization"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.can_view_usage == True
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return UsageService.get_usage_analytics(db, organization.id, days)

@router.get("/organizations/{org_slug}/billing", response_model=BillingUsage)
async def get_billing_usage(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current billing period usage"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.can_manage_billing == True
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return UsageService.get_billing_usage(db, organization.id)

# Subscription Management
@router.put("/organizations/{org_slug}/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    org_slug: str,
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update organization subscription"""
    organization = OrganizationService.get_organization_by_slug(db, org_slug)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.can_manage_billing == True
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Update subscription tier
    organization.subscription_tier = subscription_data.tier
    if subscription_data.billing_email:
        organization.billing_email = subscription_data.billing_email
    
    # Update limits based on tier
    tier_limits = {
        "free": {"contracts": 10, "ai": 5, "api": 1000, "storage": 100},
        "starter": {"contracts": 100, "ai": 50, "api": 10000, "storage": 1000},
        "professional": {"contracts": 500, "ai": 200, "api": 50000, "storage": 5000},
        "enterprise": {"contracts": -1, "ai": -1, "api": -1, "storage": -1}
    }
    
    limits = tier_limits.get(subscription_data.tier.value, tier_limits["free"])
    organization.monthly_contract_limit = limits["contracts"]
    organization.monthly_ai_analysis_limit = limits["ai"]
    organization.monthly_api_calls_limit = limits["api"]
    organization.storage_limit_mb = limits["storage"]
    
    # Enable enterprise features
    if subscription_data.tier == "enterprise":
        organization.custom_branding = True
        organization.sso_enabled = True
        organization.audit_logging = True
        organization.priority_support = True
    elif subscription_data.tier == "professional":
        organization.custom_branding = True
        organization.audit_logging = True
        organization.priority_support = True
    
    db.commit()
    db.refresh(organization)
    
    billing_usage = UsageService.get_billing_usage(db, organization.id)
    
    return SubscriptionResponse(
        tier=organization.subscription_tier,
        subscription_id=organization.subscription_id,
        billing_email=organization.billing_email,
        features={},  # TODO: Load from subscription features
        usage=billing_usage
    )
