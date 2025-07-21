"""
Domain entities representing the core business objects.
These are rich domain models with business logic and invariants.
"""
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class AggregateRoot(ABC):
    """Base class for aggregate roots in DDD."""
    
    def __init__(self):
        self._domain_events: List[Any] = []
    
    def raise_event(self, event: Any):
        """Add a domain event to be published."""
        self._domain_events.append(event)
    
    def clear_events(self):
        """Clear all domain events."""
        self._domain_events.clear()
    
    @property
    def domain_events(self) -> List[Any]:
        """Get all domain events."""
        return self._domain_events.copy()


class EntityId:
    """Value object for entity identifiers."""
    
    def __init__(self, value: str):
        if not value or not isinstance(value, str):
            raise ValueError("Entity ID must be a non-empty string")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def __eq__(self, other):
        return isinstance(other, EntityId) and self._value == other._value
    
    def __hash__(self):
        return hash(self._value)
    
    def __str__(self):
        return self._value


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts."""
    amount: float
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class EmailAddress:
    """Value object for email addresses."""
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email address")


class SubscriptionTier(Enum):
    """Enum for subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    
    @property
    def monthly_price(self) -> Money:
        prices = {
            self.FREE: Money(0),
            self.STARTER: Money(29),
            self.PROFESSIONAL: Money(99),
            self.ENTERPRISE: Money(299)
        }
        return prices[self]
    
    @property
    def features(self) -> Dict[str, Any]:
        features = {
            self.FREE: {
                "contract_analyses": 10,
                "ai_analyses": 5,
                "api_calls": 100,
                "storage_mb": 100,
                "team_members": 1,
                "custom_branding": False,
                "sso_enabled": False,
                "audit_logging": False,
                "priority_support": False
            },
            self.STARTER: {
                "contract_analyses": 100,
                "ai_analyses": 50,
                "api_calls": 1000,
                "storage_mb": 1024,
                "team_members": 5,
                "custom_branding": False,
                "sso_enabled": False,
                "audit_logging": False,
                "priority_support": False
            },
            self.PROFESSIONAL: {
                "contract_analyses": 500,
                "ai_analyses": 200,
                "api_calls": 10000,
                "storage_mb": 10240,
                "team_members": 20,
                "custom_branding": True,
                "sso_enabled": False,
                "audit_logging": True,
                "priority_support": False
            },
            self.ENTERPRISE: {
                "contract_analyses": -1,  # Unlimited
                "ai_analyses": -1,
                "api_calls": -1,
                "storage_mb": -1,
                "team_members": -1,
                "custom_branding": True,
                "sso_enabled": True,
                "audit_logging": True,
                "priority_support": True
            }
        }
        return features[self]


class UserRole(Enum):
    """Enum for user roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    
    def can_manage_members(self) -> bool:
        return self in [self.OWNER, self.ADMIN]
    
    def can_manage_billing(self) -> bool:
        return self in [self.OWNER, self.ADMIN]
    
    def can_manage_api_keys(self) -> bool:
        return self in [self.OWNER, self.ADMIN]
    
    def can_view_usage(self) -> bool:
        return True  # All roles can view usage
    
    def can_create_contracts(self) -> bool:
        return self != self.VIEWER


@dataclass
class User:
    """User entity."""
    id: EntityId
    email: EmailAddress
    full_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    def login(self):
        """Record user login."""
        self.last_login_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate user account."""
        self.is_active = False


@dataclass
class OrganizationMember:
    """Organization member entity."""
    id: EntityId
    user_id: EntityId
    organization_id: EntityId
    role: UserRole
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    
    def update_last_active(self):
        """Update last active timestamp."""
        self.last_active_at = datetime.utcnow()
    
    def change_role(self, new_role: UserRole):
        """Change member role."""
        if self.role == UserRole.OWNER and new_role != UserRole.OWNER:
            raise ValueError("Cannot change owner role without transferring ownership")
        self.role = new_role


class Organization(AggregateRoot):
    """Organization aggregate root."""
    
    def __init__(
        self,
        id: EntityId,
        name: str,
        slug: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        created_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.name = name
        self.slug = slug
        self.subscription_tier = subscription_tier
        self.created_at = created_at or datetime.utcnow()
        self._members: List[OrganizationMember] = []
        self._api_keys: List['APIKey'] = []
        self._usage_records: List['UsageRecord'] = []
    
    def add_member(self, user_id: EntityId, role: UserRole) -> OrganizationMember:
        """Add a new member to the organization."""
        # Check if user is already a member
        existing_member = next((m for m in self._members if m.user_id == user_id), None)
        if existing_member:
            raise ValueError("User is already a member of this organization")
        
        # Check team size limits
        if self.subscription_tier != SubscriptionTier.ENTERPRISE:
            max_members = self.subscription_tier.features["team_members"]
            if len(self._members) >= max_members:
                raise ValueError(f"Team size limit reached for {self.subscription_tier.value} plan")
        
        member = OrganizationMember(
            id=EntityId(str(uuid.uuid4())),
            user_id=user_id,
            organization_id=self.id,
            role=role
        )
        self._members.append(member)
        
        # Raise domain event
        self.raise_event(MemberAddedEvent(self.id, user_id, role))
        
        return member
    
    def remove_member(self, user_id: EntityId):
        """Remove a member from the organization."""
        member = next((m for m in self._members if m.user_id == user_id), None)
        if not member:
            raise ValueError("User is not a member of this organization")
        
        if member.role == UserRole.OWNER:
            raise ValueError("Cannot remove the owner")
        
        self._members.remove(member)
        self.raise_event(MemberRemovedEvent(self.id, user_id))
    
    def upgrade_subscription(self, new_tier: SubscriptionTier):
        """Upgrade organization subscription."""
        if new_tier.value <= self.subscription_tier.value:
            raise ValueError("Can only upgrade to a higher tier")
        
        old_tier = self.subscription_tier
        self.subscription_tier = new_tier
        
        self.raise_event(SubscriptionUpgradedEvent(self.id, old_tier, new_tier))
    
    def create_api_key(self, name: str, key_type: str) -> 'APIKey':
        """Create a new API key for the organization."""
        from .api_key import APIKey  # Import here to avoid circular imports
        
        api_key = APIKey.create(
            organization_id=self.id,
            name=name,
            key_type=key_type
        )
        self._api_keys.append(api_key)
        
        self.raise_event(APIKeyCreatedEvent(self.id, api_key.id))
        
        return api_key
    
    def record_usage(self, usage_type: str, amount: int = 1):
        """Record usage for billing and analytics."""
        from .usage_record import UsageRecord  # Import here to avoid circular imports
        
        # Check usage limits
        limits = self.subscription_tier.features
        current_usage = self.get_current_month_usage()
        
        if limits.get(usage_type, -1) != -1:  # -1 means unlimited
            if current_usage.get(usage_type, 0) + amount > limits[usage_type]:
                raise ValueError(f"Usage limit exceeded for {usage_type}")
        
        usage_record = UsageRecord.create(
            organization_id=self.id,
            usage_type=usage_type,
            amount=amount
        )
        self._usage_records.append(usage_record)
        
        self.raise_event(UsageRecordedEvent(self.id, usage_type, amount))
    
    def get_current_month_usage(self) -> Dict[str, int]:
        """Get current month usage statistics."""
        from datetime import datetime, timezone
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage = {}
        for record in self._usage_records:
            if record.timestamp >= current_month:
                usage[record.usage_type] = usage.get(record.usage_type, 0) + record.amount
        
        return usage
    
    @property
    def members(self) -> List[OrganizationMember]:
        """Get organization members."""
        return self._members.copy()
    
    @property
    def api_keys(self) -> List['APIKey']:
        """Get organization API keys."""
        return self._api_keys.copy()


# Domain Events
@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class MemberAddedEvent(DomainEvent):
    organization_id: EntityId
    user_id: EntityId
    role: UserRole


@dataclass(frozen=True)
class MemberRemovedEvent(DomainEvent):
    organization_id: EntityId
    user_id: EntityId


@dataclass(frozen=True)
class SubscriptionUpgradedEvent(DomainEvent):
    organization_id: EntityId
    old_tier: SubscriptionTier
    new_tier: SubscriptionTier


@dataclass(frozen=True)
class APIKeyCreatedEvent(DomainEvent):
    organization_id: EntityId
    api_key_id: EntityId


@dataclass(frozen=True)
class UsageRecordedEvent(DomainEvent):
    organization_id: EntityId
    usage_type: str
    amount: int
