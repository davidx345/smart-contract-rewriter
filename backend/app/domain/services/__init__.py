"""
Domain services containing business logic that doesn't belong to a single entity.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import secrets

from ..entities import EntityId, Organization, User, SubscriptionTier, UserRole
from ..entities.smart_contract import SmartContract, AnalysisResult
from ..entities.api_key import APIKey, RateLimit
from ..repositories import IOrganizationRepository, IUserRepository


class IOrganizationDomainService(ABC):
    """Interface for organization domain service."""
    
    @abstractmethod
    async def create_organization(
        self,
        name: str,
        owner_user_id: EntityId,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> Organization:
        """Create a new organization with owner."""
        pass
    
    @abstractmethod
    async def generate_unique_slug(self, name: str) -> str:
        """Generate a unique slug for organization."""
        pass
    
    @abstractmethod
    async def can_add_member(
        self,
        organization: Organization,
        user_id: EntityId
    ) -> tuple[bool, str]:
        """Check if a user can be added as a member."""
        pass


class IContractAnalysisDomainService(ABC):
    """Interface for contract analysis domain service."""
    
    @abstractmethod
    async def analyze_contract(
        self,
        contract: SmartContract
    ) -> AnalysisResult:
        """Analyze a smart contract for vulnerabilities and optimizations."""
        pass
    
    @abstractmethod
    async def rewrite_contract(
        self,
        contract: SmartContract,
        optimization_level: str = "standard"
    ) -> str:
        """Generate an optimized version of the contract."""
        pass
    
    @abstractmethod
    async def estimate_gas_cost(
        self,
        contract_code: str,
        network: str = "ethereum"
    ) -> Dict[str, Any]:
        """Estimate gas costs for contract deployment and operations."""
        pass


class ISecurityDomainService(ABC):
    """Interface for security domain service."""
    
    @abstractmethod
    async def validate_api_key(
        self,
        raw_key: str,
        required_permissions: List[str]
    ) -> tuple[bool, Optional[APIKey]]:
        """Validate API key and check permissions."""
        pass
    
    @abstractmethod
    async def check_rate_limit(
        self,
        api_key: APIKey,
        action: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if API key has exceeded rate limits."""
        pass
    
    @abstractmethod
    async def audit_action(
        self,
        organization_id: EntityId,
        user_id: EntityId,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an audit log entry."""
        pass


class OrganizationDomainService(IOrganizationDomainService):
    """Implementation of organization domain service."""
    
    def __init__(
        self,
        org_repository: IOrganizationRepository,
        user_repository: IUserRepository
    ):
        self._org_repository = org_repository
        self._user_repository = user_repository
    
    async def create_organization(
        self,
        name: str,
        owner_user_id: EntityId,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> Organization:
        """Create a new organization with owner."""
        # Validate owner exists
        owner = await self._user_repository.get_by_id(owner_user_id)
        if not owner:
            raise ValueError("Owner user not found")
        
        # Generate unique slug
        slug = await self.generate_unique_slug(name)
        
        # Create organization
        organization = Organization(
            id=EntityId(secrets.token_urlsafe(16)),
            name=name,
            slug=slug,
            subscription_tier=subscription_tier
        )
        
        # Add owner as first member
        organization.add_member(owner_user_id, UserRole.OWNER)
        
        return organization
    
    async def generate_unique_slug(self, name: str) -> str:
        """Generate a unique slug for organization."""
        import re
        
        # Create base slug from name
        base_slug = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
        base_slug = re.sub(r'-+', '-', base_slug).strip('-')
        
        if not base_slug:
            base_slug = "org"
        
        # Check if slug is unique
        slug = base_slug
        counter = 1
        
        while await self._org_repository.exists_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def can_add_member(
        self,
        organization: Organization,
        user_id: EntityId
    ) -> tuple[bool, str]:
        """Check if a user can be added as a member."""
        # Check if user exists
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Check if user is already a member
        existing_member = next(
            (m for m in organization.members if m.user_id == user_id), 
            None
        )
        if existing_member:
            return False, "User is already a member"
        
        # Check subscription limits
        if organization.subscription_tier != SubscriptionTier.ENTERPRISE:
            max_members = organization.subscription_tier.features["team_members"]
            current_members = len(organization.members)
            
            if current_members >= max_members:
                return False, f"Team size limit reached for {organization.subscription_tier.value} plan"
        
        return True, "User can be added"


class ContractAnalysisDomainService(IContractAnalysisDomainService):
    """Implementation of contract analysis domain service."""
    
    def __init__(self, ai_service):
        self._ai_service = ai_service
    
    async def analyze_contract(
        self,
        contract: SmartContract
    ) -> AnalysisResult:
        """Analyze a smart contract for vulnerabilities and optimizations."""
        # This would integrate with the AI service
        # For now, return a mock analysis
        from ..entities.smart_contract import (
            AnalysisResult, 
            Vulnerability, 
            VulnerabilitySeverity, 
            GasOptimization
        )
        
        # Mock vulnerabilities
        vulnerabilities = [
            Vulnerability(
                type="reentrancy",
                severity=VulnerabilitySeverity.HIGH,
                description="Potential reentrancy vulnerability in withdraw function",
                line_number=45,
                suggestion="Use reentrancy guard or checks-effects-interactions pattern"
            )
        ]
        
        # Mock gas optimizations
        gas_optimizations = [
            GasOptimization(
                description="Use ++i instead of i++ in loops",
                potential_savings=5,
                line_number=23
            )
        ]
        
        return AnalysisResult(
            vulnerabilities=vulnerabilities,
            gas_optimizations=gas_optimizations,
            security_score=75,
            gas_efficiency_score=80,
            complexity_score=70
        )
    
    async def rewrite_contract(
        self,
        contract: SmartContract,
        optimization_level: str = "standard"
    ) -> str:
        """Generate an optimized version of the contract."""
        # This would integrate with the AI service
        # For now, return the original code with comments
        return f"// Optimized version (level: {optimization_level})\n{contract.source_code}"
    
    async def estimate_gas_cost(
        self,
        contract_code: str,
        network: str = "ethereum"
    ) -> Dict[str, Any]:
        """Estimate gas costs for contract deployment and operations."""
        # Mock gas estimation
        return {
            "deployment_cost": 2500000,
            "transaction_costs": {
                "transfer": 21000,
                "approve": 45000,
                "swap": 150000
            },
            "network": network
        }


class SecurityDomainService(ISecurityDomainService):
    """Implementation of security domain service."""
    
    def __init__(self, api_key_repository, audit_repository, cache_service):
        self._api_key_repository = api_key_repository
        self._audit_repository = audit_repository
        self._cache_service = cache_service
    
    async def validate_api_key(
        self,
        raw_key: str,
        required_permissions: List[str]
    ) -> tuple[bool, Optional[APIKey]]:
        """Validate API key and check permissions."""
        # Hash the raw key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Get API key from repository
        api_key = await self._api_key_repository.get_by_hash(key_hash)
        
        if not api_key:
            return False, None
        
        # Check if key is valid
        if not api_key.is_valid():
            return False, api_key
        
        # Check permissions
        for permission in required_permissions:
            if not api_key.can_perform_action(permission):
                return False, api_key
        
        return True, api_key
    
    async def check_rate_limit(
        self,
        api_key: APIKey,
        action: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if API key has exceeded rate limits."""
        cache_key = f"rate_limit:{api_key.id.value}"
        
        # Get current usage from cache
        current_usage = await self._cache_service.get(cache_key) or {
            "minute": 0,
            "hour": 0,
            "day": 0,
            "last_reset": datetime.utcnow()
        }
        
        # Check limits
        if current_usage["minute"] >= api_key.rate_limit.per_minute:
            return False, {"limit_type": "minute", "retry_after": 60}
        
        if current_usage["hour"] >= api_key.rate_limit.per_hour:
            return False, {"limit_type": "hour", "retry_after": 3600}
        
        if current_usage["day"] >= api_key.rate_limit.per_day:
            return False, {"limit_type": "day", "retry_after": 86400}
        
        # Increment usage
        current_usage["minute"] += 1
        current_usage["hour"] += 1
        current_usage["day"] += 1
        
        # Update cache
        await self._cache_service.set(cache_key, current_usage, ttl=86400)
        
        return True, {"remaining": {
            "minute": api_key.rate_limit.per_minute - current_usage["minute"],
            "hour": api_key.rate_limit.per_hour - current_usage["hour"],
            "day": api_key.rate_limit.per_day - current_usage["day"]
        }}
    
    async def audit_action(
        self,
        organization_id: EntityId,
        user_id: EntityId,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an audit log entry."""
        # This would save to audit log repository
        audit_entry = {
            "organization_id": organization_id.value,
            "user_id": user_id.value,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "ip_address": "127.0.0.1",  # Would be extracted from request context
            "user_agent": "API"  # Would be extracted from request context
        }
        
        # Save audit entry (mock implementation)
        await self._audit_repository.save(audit_entry)
