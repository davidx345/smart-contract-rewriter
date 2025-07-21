"""
Command and Query objects for the application layer.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


# Commands (Write operations)
@dataclass
class CreateOrganizationCommand:
    """Command to create a new organization."""
    name: str
    owner_user_id: str
    description: Optional[str] = None
    subscription_tier: str = "free"


@dataclass
class InviteMemberCommand:
    """Command to invite a member to organization."""
    organization_slug: str
    email: str
    role: str
    inviter_user_id: str
    permissions: Optional[Dict[str, bool]] = None


@dataclass
class CreateAPIKeyCommand:
    """Command to create an API key."""
    organization_slug: str
    name: str
    key_type: str
    creator_user_id: str
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    expires_at: Optional[datetime] = None


@dataclass
class AnalyzeContractCommand:
    """Command to analyze a smart contract."""
    organization_id: str
    user_id: str
    name: str
    source_code: str
    contract_type: str = "general"
    analysis_options: Optional[Dict[str, Any]] = None


@dataclass
class RewriteContractCommand:
    """Command to rewrite a smart contract."""
    contract_id: str
    user_id: str
    optimization_level: str = "standard"
    preserve_functionality: bool = True


@dataclass
class RecordUsageCommand:
    """Command to record usage."""
    organization_id: str
    usage_type: str
    amount: int = 1
    metadata: Optional[Dict[str, Any]] = None


# Queries (Read operations)
@dataclass
class GetOrganizationQuery:
    """Query to get organization by slug."""
    slug: str
    requesting_user_id: str


@dataclass
class GetOrganizationMembersQuery:
    """Query to get organization members."""
    organization_slug: str
    requesting_user_id: str


@dataclass
class GetAPIKeysQuery:
    """Query to get API keys for organization."""
    organization_slug: str
    requesting_user_id: str


@dataclass
class GetContractHistoryQuery:
    """Query to get contract history."""
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class GetUsageAnalyticsQuery:
    """Query to get usage analytics."""
    organization_slug: str
    requesting_user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    usage_type: Optional[str] = None


@dataclass
class GetAuditLogsQuery:
    """Query to get audit logs."""
    organization_slug: str
    requesting_user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    action_filter: Optional[str] = None
    user_filter: Optional[str] = None


# Command Results
@dataclass
class CreateOrganizationResult:
    """Result of creating an organization."""
    organization_id: str
    slug: str
    name: str
    subscription_tier: str


@dataclass
class CreateAPIKeyResult:
    """Result of creating an API key."""
    api_key_id: str
    api_key: str  # The actual key (returned only once)
    key_prefix: str
    name: str
    key_type: str


@dataclass
class AnalyzeContractResult:
    """Result of contract analysis."""
    contract_id: str
    analysis_id: str
    security_score: int
    gas_efficiency_score: int
    complexity_score: int
    vulnerabilities_count: int
    gas_optimizations_count: int
    estimated_analysis_time: float


@dataclass
class RewriteContractResult:
    """Result of contract rewrite."""
    contract_id: str
    rewrite_id: str
    rewritten_code: str
    changes_summary: List[str]
    gas_savings_estimate: int
    version: int
