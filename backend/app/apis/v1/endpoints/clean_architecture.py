"""
Clean Architecture API controllers.
These are thin adapters that delegate to use cases.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
import logging

from ....application.commands import (
    CreateOrganizationCommand,
    InviteMemberCommand,
    CreateAPIKeyCommand,
    AnalyzeContractCommand,
    GetOrganizationQuery,
    GetOrganizationMembersQuery,
    GetAPIKeysQuery
)
from ....application.use_cases import (
    OrganizationUseCases,
    ContractUseCases,
    APIKeyUseCases
)
from ....infrastructure.container import get_container
from ....schemas.enterprise_schemas import (
    OrganizationCreate,
    OrganizationResponse,
    MemberInvite,
    APIKeyCreate,
    APIKeyResponse,
    ContractAnalysisRequest,
    ContractAnalysisResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# Dependency injection helpers
def get_organization_use_cases() -> OrganizationUseCases:
    """Get organization use cases."""
    container = get_container()
    return container.get(OrganizationUseCases)


def get_contract_use_cases() -> ContractUseCases:
    """Get contract use cases."""
    container = get_container()
    return container.get(ContractUseCases)


def get_api_key_use_cases() -> APIKeyUseCases:
    """Get API key use cases."""
    container = get_container()
    return container.get(APIKeyUseCases)


def get_current_user_id(token: str = Depends(security)) -> str:
    """Extract user ID from JWT token."""
    # Implementation would decode JWT and extract user ID
    # For now, return a mock user ID
    return "1"


# Organization endpoints
@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreate,
    current_user_id: str = Depends(get_current_user_id),
    org_use_cases: OrganizationUseCases = Depends(get_organization_use_cases)
):
    """Create a new organization."""
    try:
        command = CreateOrganizationCommand(
            name=request.name,
            owner_user_id=current_user_id,
            description=request.description,
            subscription_tier=request.subscription_tier or "free"
        )
        
        result = await org_use_cases.create_organization(command)
        
        return OrganizationResponse(
            id=result.organization_id,
            name=result.name,
            slug=result.slug,
            subscription_tier=result.subscription_tier,
            created_at=None,  # Would be populated from database
            monthly_contract_limit=100,  # Would be calculated from tier
            monthly_ai_analysis_limit=50,
            monthly_api_calls_limit=1000,
            storage_limit_mb=1024,
            custom_branding=False,
            sso_enabled=False,
            audit_logging=False,
            priority_support=False
        )
        
    except ValueError as e:
        logger.warning(f"Invalid organization creation request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/organizations/{slug}", response_model=OrganizationResponse)
async def get_organization(
    slug: str,
    current_user_id: str = Depends(get_current_user_id),
    org_use_cases: OrganizationUseCases = Depends(get_organization_use_cases)
):
    """Get organization by slug."""
    try:
        query = GetOrganizationQuery(
            slug=slug,
            requesting_user_id=current_user_id
        )
        
        result = await org_use_cases.get_organization(query)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        features = result.get("features", {})
        
        return OrganizationResponse(
            id=result["id"],
            name=result["name"],
            slug=result["slug"],
            subscription_tier=result["subscription_tier"],
            created_at=result["created_at"],
            monthly_contract_limit=features.get("contract_analyses", 0),
            monthly_ai_analysis_limit=features.get("ai_analyses", 0),
            monthly_api_calls_limit=features.get("api_calls", 0),
            storage_limit_mb=features.get("storage_mb", 0),
            custom_branding=features.get("custom_branding", False),
            sso_enabled=features.get("sso_enabled", False),
            audit_logging=features.get("audit_logging", False),
            priority_support=features.get("priority_support", False)
        )
        
    except ValueError as e:
        logger.warning(f"Access denied for organization {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get organization {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization"
        )


@router.post("/organizations/{slug}/members")
async def invite_member(
    slug: str,
    request: MemberInvite,
    current_user_id: str = Depends(get_current_user_id),
    org_use_cases: OrganizationUseCases = Depends(get_organization_use_cases)
):
    """Invite a member to the organization."""
    try:
        command = InviteMemberCommand(
            organization_slug=slug,
            email=request.email,
            role=request.role,
            inviter_user_id=current_user_id,
            permissions=request.permissions
        )
        
        await org_use_cases.invite_member(command)
        
        return {"message": "Member invited successfully"}
        
    except ValueError as e:
        logger.warning(f"Invalid member invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to invite member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite member"
        )


# API Key endpoints
@router.post("/organizations/{slug}/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    slug: str,
    request: APIKeyCreate,
    current_user_id: str = Depends(get_current_user_id),
    api_key_use_cases: APIKeyUseCases = Depends(get_api_key_use_cases)
):
    """Create a new API key."""
    try:
        command = CreateAPIKeyCommand(
            organization_slug=slug,
            name=request.name,
            key_type=request.key_type,
            creator_user_id=current_user_id,
            rate_limit_per_minute=request.rate_limit_per_minute,
            rate_limit_per_hour=request.rate_limit_per_hour,
            rate_limit_per_day=request.rate_limit_per_day,
            expires_at=request.expires_at
        )
        
        result = await api_key_use_cases.create_api_key(command)
        
        return APIKeyResponse(
            id=result.api_key_id,
            name=result.name,
            key_prefix=result.key_prefix,
            key_type=result.key_type,
            api_key=result.api_key,  # Only returned once
            rate_limit_per_minute=60,  # Would come from result
            rate_limit_per_hour=1000,
            rate_limit_per_day=10000,
            is_active=True,
            total_calls=0,
            created_at=None  # Would be populated
        )
        
    except ValueError as e:
        logger.warning(f"Invalid API key creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


# Contract analysis endpoints
@router.post("/contracts/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    request: ContractAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
    contract_use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    """Analyze a smart contract."""
    try:
        command = AnalyzeContractCommand(
            organization_id=request.organization_id,
            user_id=current_user_id,
            name=request.name,
            source_code=request.source_code,
            contract_type=request.contract_type or "general",
            analysis_options=request.analysis_options
        )
        
        result = await contract_use_cases.analyze_contract(command)
        
        return ContractAnalysisResponse(
            contract_id=result.contract_id,
            analysis_id=result.analysis_id,
            status="completed",
            security_score=result.security_score,
            gas_efficiency_score=result.gas_efficiency_score,
            complexity_score=result.complexity_score,
            vulnerabilities=["Reentrancy vulnerability found"],  # Mock data
            gas_optimizations=["Use ++i instead of i++"],  # Mock data
            recommendations=["Implement reentrancy guard"],  # Mock data
            estimated_gas_cost=250000,
            analysis_duration=result.estimated_analysis_time
        )
        
    except ValueError as e:
        logger.warning(f"Invalid contract analysis request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to analyze contract: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze contract"
        )


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "architecture": "clean",
        "patterns": ["DDD", "CQRS", "Repository", "Unit of Work"],
        "message": "Clean Architecture API is running"
    }
