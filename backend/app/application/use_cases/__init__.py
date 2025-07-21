"""
Use case implementations for the application layer.
These orchestrate domain services and repositories to fulfill business requirements.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..commands import (
    CreateOrganizationCommand,
    CreateOrganizationResult,
    InviteMemberCommand,
    CreateAPIKeyCommand,
    CreateAPIKeyResult,
    AnalyzeContractCommand,
    AnalyzeContractResult,
    RewriteContractCommand,
    RewriteContractResult,
    RecordUsageCommand,
    GetOrganizationQuery,
    GetOrganizationMembersQuery,
    GetAPIKeysQuery,
    GetContractHistoryQuery,
    GetUsageAnalyticsQuery
)
from ...domain.entities import EntityId, SubscriptionTier, UserRole
from ...domain.entities.smart_contract import SmartContract
from ...domain.entities.api_key import APIKey
from ...domain.repositories import IUnitOfWork
from ...domain.services import (
    IOrganizationDomainService,
    IContractAnalysisDomainService,
    ISecurityDomainService
)


logger = logging.getLogger(__name__)


class OrganizationUseCases:
    """Use cases for organization management."""
    
    def __init__(
        self,
        uow: IUnitOfWork,
        org_domain_service: IOrganizationDomainService,
        security_service: ISecurityDomainService
    ):
        self._uow = uow
        self._org_domain_service = org_domain_service
        self._security_service = security_service
    
    async def create_organization(
        self,
        command: CreateOrganizationCommand
    ) -> CreateOrganizationResult:
        """Create a new organization."""
        async with self._uow:
            try:
                # Validate subscription tier
                try:
                    subscription_tier = SubscriptionTier(command.subscription_tier)
                except ValueError:
                    raise ValueError(f"Invalid subscription tier: {command.subscription_tier}")
                
                # Create organization using domain service
                organization = await self._org_domain_service.create_organization(
                    name=command.name,
                    owner_user_id=EntityId(command.owner_user_id),
                    subscription_tier=subscription_tier
                )
                
                # Save organization
                saved_org = await self._uow.organizations.save(organization)
                
                # Save organization members
                for member in organization.members:
                    await self._uow.organization_members.save(member)
                
                # Audit the action
                await self._security_service.audit_action(
                    organization_id=saved_org.id,
                    user_id=EntityId(command.owner_user_id),
                    action="organization_created",
                    resource_type="organization",
                    resource_id=saved_org.id.value,
                    details={"name": command.name, "subscription_tier": command.subscription_tier}
                )
                
                await self._uow.commit()
                
                logger.info(f"Organization created: {saved_org.slug}")
                
                return CreateOrganizationResult(
                    organization_id=saved_org.id.value,
                    slug=saved_org.slug,
                    name=saved_org.name,
                    subscription_tier=saved_org.subscription_tier.value
                )
                
            except Exception as e:
                await self._uow.rollback()
                logger.error(f"Failed to create organization: {e}")
                raise
    
    async def invite_member(
        self,
        command: InviteMemberCommand
    ) -> bool:
        """Invite a member to organization."""
        async with self._uow:
            try:
                # Get organization
                organization = await self._uow.organizations.get_by_slug(command.organization_slug)
                if not organization:
                    raise ValueError("Organization not found")
                
                # Validate inviter permissions
                inviter_member = await self._uow.organization_members.get_by_user_and_organization(
                    user_id=EntityId(command.inviter_user_id),
                    organization_id=organization.id
                )
                
                if not inviter_member or not inviter_member.role.can_manage_members():
                    raise ValueError("Insufficient permissions to invite members")
                
                # Get user by email
                user = await self._uow.users.get_by_email(command.email)
                if not user:
                    raise ValueError("User not found")
                
                # Validate role
                try:
                    role = UserRole(command.role)
                except ValueError:
                    raise ValueError(f"Invalid role: {command.role}")
                
                # Check if user can be added
                can_add, reason = await self._org_domain_service.can_add_member(
                    organization, user.id
                )
                if not can_add:
                    raise ValueError(reason)
                
                # Add member
                member = organization.add_member(user.id, role)
                
                # Save changes
                await self._uow.organizations.save(organization)
                await self._uow.organization_members.save(member)
                
                # Audit the action
                await self._security_service.audit_action(
                    organization_id=organization.id,
                    user_id=EntityId(command.inviter_user_id),
                    action="member_invited",
                    resource_type="organization_member",
                    resource_id=member.id.value,
                    details={"email": command.email, "role": command.role}
                )
                
                await self._uow.commit()
                
                logger.info(f"Member invited to {organization.slug}: {command.email}")
                return True
                
            except Exception as e:
                await self._uow.rollback()
                logger.error(f"Failed to invite member: {e}")
                raise
    
    async def get_organization(
        self,
        query: GetOrganizationQuery
    ) -> Optional[Dict[str, Any]]:
        """Get organization details."""
        async with self._uow:
            organization = await self._uow.organizations.get_by_slug(query.slug)
            if not organization:
                return None
            
            # Check if user has access
            member = await self._uow.organization_members.get_by_user_and_organization(
                user_id=EntityId(query.requesting_user_id),
                organization_id=organization.id
            )
            
            if not member:
                raise ValueError("Access denied")
            
            return {
                "id": organization.id.value,
                "name": organization.name,
                "slug": organization.slug,
                "subscription_tier": organization.subscription_tier.value,
                "created_at": organization.created_at.isoformat(),
                "features": organization.subscription_tier.features,
                "member_role": member.role.value,
                "member_permissions": {
                    "can_manage_members": member.role.can_manage_members(),
                    "can_manage_billing": member.role.can_manage_billing(),
                    "can_manage_api_keys": member.role.can_manage_api_keys(),
                    "can_view_usage": member.role.can_view_usage(),
                    "can_create_contracts": member.role.can_create_contracts()
                }
            }


class ContractUseCases:
    """Use cases for contract management."""
    
    def __init__(
        self,
        uow: IUnitOfWork,
        analysis_service: IContractAnalysisDomainService,
        security_service: ISecurityDomainService
    ):
        self._uow = uow
        self._analysis_service = analysis_service
        self._security_service = security_service
    
    async def analyze_contract(
        self,
        command: AnalyzeContractCommand
    ) -> AnalyzeContractResult:
        """Analyze a smart contract."""
        async with self._uow:
            try:
                # Validate organization access
                organization = await self._uow.organizations.get_by_id(
                    EntityId(command.organization_id)
                )
                if not organization:
                    raise ValueError("Organization not found")
                
                # Check usage limits
                organization.record_usage("contract_analysis")
                
                # Create contract entity
                contract = SmartContract.create(
                    organization_id=EntityId(command.organization_id),
                    user_id=EntityId(command.user_id),
                    name=command.name,
                    source_code=command.source_code,
                    contract_type=command.contract_type
                )
                
                # Start analysis
                contract.start_analysis()
                
                # Save contract
                saved_contract = await self._uow.smart_contracts.save(contract)
                
                # Record usage
                usage_command = RecordUsageCommand(
                    organization_id=command.organization_id,
                    usage_type="contract_analysis",
                    amount=1,
                    metadata={"contract_id": saved_contract.id.value}
                )
                await self.record_usage(usage_command)
                
                # Perform analysis (async in background in real implementation)
                analysis_result = await self._analysis_service.analyze_contract(contract)
                
                # Complete analysis
                contract.complete_analysis(analysis_result)
                
                # Save updated contract
                await self._uow.smart_contracts.save(contract)
                
                # Audit the action
                await self._security_service.audit_action(
                    organization_id=organization.id,
                    user_id=EntityId(command.user_id),
                    action="contract_analyzed",
                    resource_type="smart_contract",
                    resource_id=saved_contract.id.value,
                    details={
                        "contract_name": command.name,
                        "contract_type": command.contract_type,
                        "security_score": analysis_result.security_score
                    }
                )
                
                await self._uow.commit()
                
                logger.info(f"Contract analyzed: {saved_contract.id.value}")
                
                return AnalyzeContractResult(
                    contract_id=saved_contract.id.value,
                    analysis_id=saved_contract.id.value,  # Same as contract ID for now
                    security_score=analysis_result.security_score,
                    gas_efficiency_score=analysis_result.gas_efficiency_score,
                    complexity_score=analysis_result.complexity_score,
                    vulnerabilities_count=len(analysis_result.vulnerabilities),
                    gas_optimizations_count=len(analysis_result.gas_optimizations),
                    estimated_analysis_time=contract.get_analysis_duration() or 0.0
                )
                
            except Exception as e:
                await self._uow.rollback()
                logger.error(f"Failed to analyze contract: {e}")
                raise
    
    async def record_usage(
        self,
        command: RecordUsageCommand
    ) -> bool:
        """Record usage for billing and analytics."""
        async with self._uow:
            try:
                from ...domain.entities.usage_record import UsageRecord
                
                # Create usage record
                usage_record = UsageRecord.create(
                    organization_id=EntityId(command.organization_id),
                    usage_type=command.usage_type,
                    amount=command.amount,
                    metadata=command.metadata or {}
                )
                
                # Save usage record
                await self._uow.usage_records.save(usage_record)
                
                await self._uow.commit()
                
                logger.debug(f"Usage recorded: {command.usage_type} x{command.amount}")
                return True
                
            except Exception as e:
                await self._uow.rollback()
                logger.error(f"Failed to record usage: {e}")
                raise


class APIKeyUseCases:
    """Use cases for API key management."""
    
    def __init__(
        self,
        uow: IUnitOfWork,
        security_service: ISecurityDomainService
    ):
        self._uow = uow
        self._security_service = security_service
    
    async def create_api_key(
        self,
        command: CreateAPIKeyCommand
    ) -> CreateAPIKeyResult:
        """Create a new API key."""
        async with self._uow:
            try:
                # Get organization
                organization = await self._uow.organizations.get_by_slug(command.organization_slug)
                if not organization:
                    raise ValueError("Organization not found")
                
                # Validate creator permissions
                creator_member = await self._uow.organization_members.get_by_user_and_organization(
                    user_id=EntityId(command.creator_user_id),
                    organization_id=organization.id
                )
                
                if not creator_member or not creator_member.role.can_manage_api_keys():
                    raise ValueError("Insufficient permissions to create API keys")
                
                # Create API key
                from ...domain.entities.api_key import RateLimit
                
                rate_limit = RateLimit(
                    per_minute=command.rate_limit_per_minute or 60,
                    per_hour=command.rate_limit_per_hour or 1000,
                    per_day=command.rate_limit_per_day or 10000
                )
                
                api_key, raw_key = APIKey.create(
                    organization_id=organization.id,
                    name=command.name,
                    key_type=command.key_type,
                    rate_limit=rate_limit,
                    expires_at=command.expires_at
                )
                
                # Save API key
                saved_key = await self._uow.api_keys.save(api_key)
                
                # Audit the action
                await self._security_service.audit_action(
                    organization_id=organization.id,
                    user_id=EntityId(command.creator_user_id),
                    action="api_key_created",
                    resource_type="api_key",
                    resource_id=saved_key.id.value,
                    details={"name": command.name, "key_type": command.key_type}
                )
                
                await self._uow.commit()
                
                logger.info(f"API key created: {saved_key.id.value}")
                
                return CreateAPIKeyResult(
                    api_key_id=saved_key.id.value,
                    api_key=raw_key,
                    key_prefix=saved_key.key_prefix,
                    name=saved_key.name,
                    key_type=saved_key.key_type
                )
                
            except Exception as e:
                await self._uow.rollback()
                logger.error(f"Failed to create API key: {e}")
                raise
