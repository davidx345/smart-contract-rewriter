"""
API Key domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
from .import EntityId, AggregateRoot


class APIKeyType:
    """API Key types."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


@dataclass
class RateLimit:
    """Value object for rate limiting."""
    per_minute: int
    per_hour: int
    per_day: int
    
    def __post_init__(self):
        if any(limit < 0 for limit in [self.per_minute, self.per_hour, self.per_day]):
            raise ValueError("Rate limits cannot be negative")


class APIKey(AggregateRoot):
    """API Key aggregate root."""
    
    def __init__(
        self,
        id: EntityId,
        organization_id: EntityId,
        name: str,
        key_type: str,
        key_hash: str,
        key_prefix: str,
        rate_limit: RateLimit,
        is_active: bool = True,
        expires_at: Optional[datetime] = None,
        created_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.organization_id = organization_id
        self.name = name
        self.key_type = key_type
        self.key_hash = key_hash
        self.key_prefix = key_prefix
        self.rate_limit = rate_limit
        self.is_active = is_active
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()
        self.total_calls = 0
        self.last_used_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        organization_id: EntityId,
        name: str,
        key_type: str,
        rate_limit: Optional[RateLimit] = None,
        expires_at: Optional[datetime] = None
    ) -> tuple['APIKey', str]:
        """Create a new API key and return both the entity and the raw key."""
        import uuid
        
        # Generate raw API key
        raw_key = f"sk_{secrets.token_urlsafe(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Extract prefix for display
        key_prefix = raw_key[:12]
        
        # Set default rate limits based on key type
        if rate_limit is None:
            if key_type == APIKeyType.READ_ONLY:
                rate_limit = RateLimit(per_minute=60, per_hour=1000, per_day=5000)
            elif key_type == APIKeyType.READ_WRITE:
                rate_limit = RateLimit(per_minute=100, per_hour=2000, per_day=10000)
            else:  # ADMIN
                rate_limit = RateLimit(per_minute=200, per_hour=5000, per_day=25000)
        
        api_key = cls(
            id=EntityId(str(uuid.uuid4())),
            organization_id=organization_id,
            name=name,
            key_type=key_type,
            key_hash=key_hash,
            key_prefix=key_prefix,
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        return api_key, raw_key
    
    def verify_key(self, raw_key: str) -> bool:
        """Verify if the provided raw key matches this API key."""
        return hashlib.sha256(raw_key.encode()).hexdigest() == self.key_hash
    
    def record_usage(self):
        """Record API key usage."""
        self.total_calls += 1
        self.last_used_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the API key."""
        self.is_active = False
    
    def update_rate_limit(self, new_rate_limit: RateLimit):
        """Update rate limits for the API key."""
        self.rate_limit = new_rate_limit
    
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
    
    def can_perform_action(self, action: str) -> bool:
        """Check if the API key can perform a specific action."""
        if not self.is_valid():
            return False
        
        read_actions = ["read", "get", "list", "view"]
        write_actions = ["create", "update", "delete", "modify"]
        admin_actions = ["admin", "manage", "configure"]
        
        if self.key_type == APIKeyType.READ_ONLY:
            return any(read_action in action.lower() for read_action in read_actions)
        elif self.key_type == APIKeyType.READ_WRITE:
            return any(
                action_type in action.lower() 
                for action_type in read_actions + write_actions
            )
        else:  # ADMIN
            return True  # Admin keys can perform all actions
