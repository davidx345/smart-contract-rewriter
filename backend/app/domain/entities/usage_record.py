"""
Usage Record domain entity.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import uuid
from . import EntityId


@dataclass
class UsageRecord:
    """Usage record entity for tracking organization usage."""
    id: EntityId
    organization_id: EntityId
    usage_type: str  # e.g., "contract_analysis", "ai_analysis", "api_call"
    amount: int
    timestamp: datetime
    metadata: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        organization_id: EntityId,
        usage_type: str,
        amount: int = 1,
        metadata: Dict[str, Any] = None
    ) -> 'UsageRecord':
        """Create a new usage record."""
        return cls(
            id=EntityId(str(uuid.uuid4())),
            organization_id=organization_id,
            usage_type=usage_type,
            amount=amount,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    def is_billable(self) -> bool:
        """Check if this usage record is billable."""
        billable_types = [
            "contract_analysis",
            "ai_analysis", 
            "api_call",
            "storage_usage"
        ]
        return self.usage_type in billable_types
    
    def get_cost(self, pricing_config: Dict[str, float]) -> float:
        """Calculate the cost for this usage record."""
        if not self.is_billable():
            return 0.0
        
        unit_cost = pricing_config.get(self.usage_type, 0.0)
        return unit_cost * self.amount
