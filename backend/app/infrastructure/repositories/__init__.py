"""
SQLAlchemy repository implementations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities import EntityId, Organization, User, OrganizationMember, SubscriptionTier, UserRole
from ...domain.entities.smart_contract import SmartContract, ContractStatus
from ...domain.entities.api_key import APIKey
from ...domain.entities.usage_record import UsageRecord
from ...domain.repositories import (
    IOrganizationRepository,
    IUserRepository,
    IOrganizationMemberRepository,
    ISmartContractRepository,
    IAPIKeyRepository,
    IUsageRecordRepository,
    IUnitOfWork
)
from ...models.enterprise_models import (
    Organization as OrganizationModel,
    OrganizationMember as OrganizationMemberModel,
    APIKey as APIKeyModel,
    UsageRecord as UsageRecordModel
)
from ...schemas.auth_db_schemas import User as UserModel
from ...schemas.contract_db_schemas import ContractAnalysis as ContractModel


class SQLAlchemyOrganizationRepository(IOrganizationRepository):
    """SQLAlchemy implementation of organization repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, organization_id: EntityId) -> Optional[Organization]:
        """Get organization by ID."""
        stmt = select(OrganizationModel).where(OrganizationModel.id == int(organization_id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        stmt = select(OrganizationModel).where(OrganizationModel.slug == slug)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_by_user_id(self, user_id: EntityId) -> List[Organization]:
        """Get organizations where user is a member."""
        stmt = (
            select(OrganizationModel)
            .join(OrganizationMemberModel)
            .where(OrganizationMemberModel.user_id == int(user_id.value))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def save(self, organization: Organization) -> Organization:
        """Save organization."""
        # Check if organization exists
        stmt = select(OrganizationModel).where(OrganizationModel.id == int(organization.id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.name = organization.name
            model.slug = organization.slug
            model.subscription_tier = organization.subscription_tier.value
        else:
            # Create new
            model = OrganizationModel(
                id=int(organization.id.value) if organization.id.value.isdigit() else None,
                name=organization.name,
                slug=organization.slug,
                subscription_tier=organization.subscription_tier.value,
                created_at=organization.created_at
            )
            self._session.add(model)
        
        await self._session.flush()
        return self._to_entity(model)
    
    async def delete(self, organization_id: EntityId) -> None:
        """Delete organization."""
        stmt = delete(OrganizationModel).where(OrganizationModel.id == int(organization_id.value))
        await self._session.execute(stmt)
    
    async def exists_by_slug(self, slug: str) -> bool:
        """Check if organization exists by slug."""
        stmt = select(func.count(OrganizationModel.id)).where(OrganizationModel.slug == slug)
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    def _to_entity(self, model: OrganizationModel) -> Organization:
        """Convert model to entity."""
        return Organization(
            id=EntityId(str(model.id)),
            name=model.name,
            slug=model.slug,
            subscription_tier=SubscriptionTier(model.subscription_tier),
            created_at=model.created_at
        )


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, user_id: EntityId) -> Optional[User]:
        """Get user by ID."""
        stmt = select(UserModel).where(UserModel.id == int(user_id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def save(self, user: User) -> User:
        """Save user."""
        # Implementation would go here
        # For now, return the user as-is
        return user
    
    async def delete(self, user_id: EntityId) -> None:
        """Delete user."""
        stmt = delete(UserModel).where(UserModel.id == int(user_id.value))
        await self._session.execute(stmt)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        stmt = select(func.count(UserModel.id)).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert model to entity."""
        from ...domain.entities import EmailAddress
        
        return User(
            id=EntityId(str(model.id)),
            email=EmailAddress(model.email),
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
            last_login_at=model.last_login_at
        )


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work."""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        """Enter async context."""
        self._session = self._session_factory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        
        if self._session:
            await self._session.close()
    
    async def commit(self):
        """Commit transaction."""
        if self._session:
            await self._session.commit()
    
    async def rollback(self):
        """Rollback transaction."""
        if self._session:
            await self._session.rollback()
    
    @property
    def organizations(self) -> IOrganizationRepository:
        """Get organization repository."""
        return SQLAlchemyOrganizationRepository(self._session)
    
    @property
    def users(self) -> IUserRepository:
        """Get user repository."""
        return SQLAlchemyUserRepository(self._session)
    
    @property
    def organization_members(self) -> IOrganizationMemberRepository:
        """Get organization member repository."""
        return SQLAlchemyOrganizationMemberRepository(self._session)
    
    @property
    def smart_contracts(self) -> ISmartContractRepository:
        """Get smart contract repository."""
        return SQLAlchemySmartContractRepository(self._session)
    
    @property
    def api_keys(self) -> IAPIKeyRepository:
        """Get API key repository."""
        return SQLAlchemyAPIKeyRepository(self._session)
    
    @property
    def usage_records(self) -> IUsageRecordRepository:
        """Get usage record repository."""
        return SQLAlchemyUsageRecordRepository(self._session)


class SQLAlchemyOrganizationMemberRepository(IOrganizationMemberRepository):
    """SQLAlchemy implementation of organization member repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_organization_id(self, organization_id: EntityId) -> List[OrganizationMember]:
        """Get all members of an organization."""
        stmt = select(OrganizationMemberModel).where(
            OrganizationMemberModel.organization_id == int(organization_id.value)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def get_by_user_and_organization(
        self, 
        user_id: EntityId, 
        organization_id: EntityId
    ) -> Optional[OrganizationMember]:
        """Get specific organization membership."""
        stmt = select(OrganizationMemberModel).where(
            and_(
                OrganizationMemberModel.user_id == int(user_id.value),
                OrganizationMemberModel.organization_id == int(organization_id.value)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def save(self, member: OrganizationMember) -> OrganizationMember:
        """Save organization member."""
        # Check if member exists
        stmt = select(OrganizationMemberModel).where(OrganizationMemberModel.id == int(member.id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.role = member.role.value
            model.last_active_at = member.last_active_at
        else:
            # Create new
            model = OrganizationMemberModel(
                id=int(member.id.value) if member.id.value.isdigit() else None,
                user_id=int(member.user_id.value),
                organization_id=int(member.organization_id.value),
                role=member.role.value,
                joined_at=member.joined_at,
                last_active_at=member.last_active_at
            )
            self._session.add(model)
        
        await self._session.flush()
        return self._to_entity(model)
    
    async def delete(self, member_id: EntityId) -> None:
        """Delete organization member."""
        stmt = delete(OrganizationMemberModel).where(OrganizationMemberModel.id == int(member_id.value))
        await self._session.execute(stmt)
    
    def _to_entity(self, model: OrganizationMemberModel) -> OrganizationMember:
        """Convert model to entity."""
        return OrganizationMember(
            id=EntityId(str(model.id)),
            user_id=EntityId(str(model.user_id)),
            organization_id=EntityId(str(model.organization_id)),
            role=UserRole(model.role),
            joined_at=model.joined_at,
            last_active_at=model.last_active_at
        )


class SQLAlchemySmartContractRepository(ISmartContractRepository):
    """SQLAlchemy implementation of smart contract repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, contract_id: EntityId) -> Optional[SmartContract]:
        """Get contract by ID."""
        # Implementation would use ContractModel
        # For now, return None
        return None
    
    async def get_by_organization_id(
        self, 
        organization_id: EntityId,
        limit: int = 100,
        offset: int = 0
    ) -> List[SmartContract]:
        """Get contracts by organization."""
        # Implementation would go here
        return []
    
    async def get_by_user_id(
        self, 
        user_id: EntityId,
        limit: int = 100,
        offset: int = 0
    ) -> List[SmartContract]:
        """Get contracts by user."""
        # Implementation would go here
        return []
    
    async def save(self, contract: SmartContract) -> SmartContract:
        """Save contract."""
        # Implementation would go here
        return contract
    
    async def delete(self, contract_id: EntityId) -> None:
        """Delete contract."""
        # Implementation would go here
        pass
    
    async def get_analytics(
        self, 
        organization_id: EntityId,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get contract analytics for organization."""
        # Implementation would go here
        return {}


class SQLAlchemyAPIKeyRepository(IAPIKeyRepository):
    """SQLAlchemy implementation of API key repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, api_key_id: EntityId) -> Optional[APIKey]:
        """Get API key by ID."""
        # Implementation would go here
        return None
    
    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        # Implementation would go here
        return None
    
    async def get_by_organization_id(self, organization_id: EntityId) -> List[APIKey]:
        """Get API keys by organization."""
        # Implementation would go here
        return []
    
    async def save(self, api_key: APIKey) -> APIKey:
        """Save API key."""
        # Implementation would go here
        return api_key
    
    async def delete(self, api_key_id: EntityId) -> None:
        """Delete API key."""
        # Implementation would go here
        pass


class SQLAlchemyUsageRecordRepository(IUsageRecordRepository):
    """SQLAlchemy implementation of usage record repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, usage_record: UsageRecord) -> UsageRecord:
        """Save usage record."""
        # Implementation would go here
        return usage_record
    
    async def get_by_organization_id(
        self,
        organization_id: EntityId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        usage_type: Optional[str] = None
    ) -> List[UsageRecord]:
        """Get usage records by organization."""
        # Implementation would go here
        return []
    
    async def get_current_month_usage(
        self,
        organization_id: EntityId
    ) -> Dict[str, int]:
        """Get current month usage summary."""
        # Implementation would go here
        return {}
    
    async def get_analytics(
        self,
        organization_id: EntityId,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage analytics."""
        # Implementation would go here
        return {}
