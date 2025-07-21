"""
Repository interfaces for the domain layer.
These define the contracts that infrastructure implementations must fulfill.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities import EntityId, Organization, User, OrganizationMember
from ..entities.smart_contract import SmartContract
from ..entities.api_key import APIKey
from ..entities.usage_record import UsageRecord


class IOrganizationRepository(ABC):
    """Interface for organization repository."""
    
    @abstractmethod
    async def get_by_id(self, organization_id: EntityId) -> Optional[Organization]:
        """Get organization by ID."""
        pass
    
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: EntityId) -> List[Organization]:
        """Get organizations where user is a member."""
        pass
    
    @abstractmethod
    async def save(self, organization: Organization) -> Organization:
        """Save organization."""
        pass
    
    @abstractmethod
    async def delete(self, organization_id: EntityId) -> None:
        """Delete organization."""
        pass
    
    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool:
        """Check if organization exists by slug."""
        pass


class IUserRepository(ABC):
    """Interface for user repository."""
    
    @abstractmethod
    async def get_by_id(self, user_id: EntityId) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: EntityId) -> None:
        """Delete user."""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        pass


class IOrganizationMemberRepository(ABC):
    """Interface for organization member repository."""
    
    @abstractmethod
    async def get_by_organization_id(self, organization_id: EntityId) -> List[OrganizationMember]:
        """Get all members of an organization."""
        pass
    
    @abstractmethod
    async def get_by_user_and_organization(
        self, 
        user_id: EntityId, 
        organization_id: EntityId
    ) -> Optional[OrganizationMember]:
        """Get specific organization membership."""
        pass
    
    @abstractmethod
    async def save(self, member: OrganizationMember) -> OrganizationMember:
        """Save organization member."""
        pass
    
    @abstractmethod
    async def delete(self, member_id: EntityId) -> None:
        """Delete organization member."""
        pass


class ISmartContractRepository(ABC):
    """Interface for smart contract repository."""
    
    @abstractmethod
    async def get_by_id(self, contract_id: EntityId) -> Optional[SmartContract]:
        """Get contract by ID."""
        pass
    
    @abstractmethod
    async def get_by_organization_id(
        self, 
        organization_id: EntityId,
        limit: int = 100,
        offset: int = 0
    ) -> List[SmartContract]:
        """Get contracts by organization."""
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self, 
        user_id: EntityId,
        limit: int = 100,
        offset: int = 0
    ) -> List[SmartContract]:
        """Get contracts by user."""
        pass
    
    @abstractmethod
    async def save(self, contract: SmartContract) -> SmartContract:
        """Save contract."""
        pass
    
    @abstractmethod
    async def delete(self, contract_id: EntityId) -> None:
        """Delete contract."""
        pass
    
    @abstractmethod
    async def get_analytics(
        self, 
        organization_id: EntityId,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get contract analytics for organization."""
        pass


class IAPIKeyRepository(ABC):
    """Interface for API key repository."""
    
    @abstractmethod
    async def get_by_id(self, api_key_id: EntityId) -> Optional[APIKey]:
        """Get API key by ID."""
        pass
    
    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        pass
    
    @abstractmethod
    async def get_by_organization_id(self, organization_id: EntityId) -> List[APIKey]:
        """Get API keys by organization."""
        pass
    
    @abstractmethod
    async def save(self, api_key: APIKey) -> APIKey:
        """Save API key."""
        pass
    
    @abstractmethod
    async def delete(self, api_key_id: EntityId) -> None:
        """Delete API key."""
        pass


class IUsageRecordRepository(ABC):
    """Interface for usage record repository."""
    
    @abstractmethod
    async def save(self, usage_record: UsageRecord) -> UsageRecord:
        """Save usage record."""
        pass
    
    @abstractmethod
    async def get_by_organization_id(
        self,
        organization_id: EntityId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        usage_type: Optional[str] = None
    ) -> List[UsageRecord]:
        """Get usage records by organization."""
        pass
    
    @abstractmethod
    async def get_current_month_usage(
        self,
        organization_id: EntityId
    ) -> Dict[str, int]:
        """Get current month usage summary."""
        pass
    
    @abstractmethod
    async def get_analytics(
        self,
        organization_id: EntityId,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage analytics."""
        pass


class IUnitOfWork(ABC):
    """Unit of Work interface for transaction management."""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter async context."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit transaction."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback transaction."""
        pass
    
    # Repository properties
    @property
    @abstractmethod
    def organizations(self) -> IOrganizationRepository:
        pass
    
    @property
    @abstractmethod
    def users(self) -> IUserRepository:
        pass
    
    @property
    @abstractmethod
    def organization_members(self) -> IOrganizationMemberRepository:
        pass
    
    @property
    @abstractmethod
    def smart_contracts(self) -> ISmartContractRepository:
        pass
    
    @property
    @abstractmethod
    def api_keys(self) -> IAPIKeyRepository:
        pass
    
    @property
    @abstractmethod
    def usage_records(self) -> IUsageRecordRepository:
        pass
