"""
Smart Contract domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
from . import EntityId, AggregateRoot


class ContractStatus(Enum):
    """Contract analysis status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    @property
    def score(self) -> int:
        scores = {
            self.LOW: 1,
            self.MEDIUM: 2,
            self.HIGH: 3,
            self.CRITICAL: 4
        }
        return scores[self]


@dataclass(frozen=True)
class Vulnerability:
    """Value object representing a vulnerability."""
    type: str
    severity: VulnerabilitySeverity
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    
    def __post_init__(self):
        if not self.type or not self.description:
            raise ValueError("Vulnerability type and description are required")


@dataclass(frozen=True)
class GasOptimization:
    """Value object for gas optimization suggestions."""
    description: str
    potential_savings: int  # Gas units
    line_number: Optional[int] = None
    before_code: Optional[str] = None
    after_code: Optional[str] = None


@dataclass(frozen=True)
class AnalysisResult:
    """Value object containing analysis results."""
    vulnerabilities: List[Vulnerability]
    gas_optimizations: List[GasOptimization]
    security_score: int  # 0-100
    gas_efficiency_score: int  # 0-100
    complexity_score: int  # 0-100
    
    def __post_init__(self):
        if not (0 <= self.security_score <= 100):
            raise ValueError("Security score must be between 0 and 100")
        if not (0 <= self.gas_efficiency_score <= 100):
            raise ValueError("Gas efficiency score must be between 0 and 100")
        if not (0 <= self.complexity_score <= 100):
            raise ValueError("Complexity score must be between 0 and 100")
    
    @property
    def overall_score(self) -> float:
        """Calculate overall contract quality score."""
        return (self.security_score + self.gas_efficiency_score + self.complexity_score) / 3
    
    @property
    def critical_vulnerabilities_count(self) -> int:
        """Count critical vulnerabilities."""
        return sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL)
    
    @property
    def high_vulnerabilities_count(self) -> int:
        """Count high severity vulnerabilities."""
        return sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.HIGH)
    
    @property
    def total_gas_savings(self) -> int:
        """Calculate total potential gas savings."""
        return sum(opt.potential_savings for opt in self.gas_optimizations)


class SmartContract(AggregateRoot):
    """Smart Contract aggregate root."""
    
    def __init__(
        self,
        id: EntityId,
        organization_id: EntityId,
        user_id: EntityId,
        name: str,
        source_code: str,
        contract_type: str = "general",
        created_at: datetime = None
    ):
        super().__init__()
        self.id = id
        self.organization_id = organization_id
        self.user_id = user_id
        self.name = name
        self.source_code = source_code
        self.contract_type = contract_type
        self.status = ContractStatus.PENDING
        self.created_at = created_at or datetime.utcnow()
        self.analysis_result: Optional[AnalysisResult] = None
        self.rewritten_code: Optional[str] = None
        self.analysis_started_at: Optional[datetime] = None
        self.analysis_completed_at: Optional[datetime] = None
        self._version = 1
    
    @classmethod
    def create(
        cls,
        organization_id: EntityId,
        user_id: EntityId,
        name: str,
        source_code: str,
        contract_type: str = "general"
    ) -> 'SmartContract':
        """Factory method to create a new smart contract."""
        if not source_code.strip():
            raise ValueError("Source code cannot be empty")
        
        if not name.strip():
            raise ValueError("Contract name cannot be empty")
        
        contract = cls(
            id=EntityId(str(uuid.uuid4())),
            organization_id=organization_id,
            user_id=user_id,
            name=name,
            source_code=source_code,
            contract_type=contract_type
        )
        
        # Raise domain event
        contract.raise_event(ContractCreatedEvent(
            contract_id=contract.id,
            organization_id=organization_id,
            user_id=user_id,
            contract_type=contract_type
        ))
        
        return contract
    
    def start_analysis(self):
        """Start the contract analysis process."""
        if self.status != ContractStatus.PENDING:
            raise ValueError(f"Cannot start analysis. Current status: {self.status.value}")
        
        self.status = ContractStatus.ANALYZING
        self.analysis_started_at = datetime.utcnow()
        
        self.raise_event(AnalysisStartedEvent(
            contract_id=self.id,
            started_at=self.analysis_started_at
        ))
    
    def complete_analysis(self, analysis_result: AnalysisResult):
        """Complete the analysis with results."""
        if self.status != ContractStatus.ANALYZING:
            raise ValueError(f"Cannot complete analysis. Current status: {self.status.value}")
        
        self.status = ContractStatus.COMPLETED
        self.analysis_result = analysis_result
        self.analysis_completed_at = datetime.utcnow()
        
        self.raise_event(AnalysisCompletedEvent(
            contract_id=self.id,
            analysis_result=analysis_result,
            completed_at=self.analysis_completed_at
        ))
    
    def fail_analysis(self, error_message: str):
        """Mark analysis as failed."""
        if self.status != ContractStatus.ANALYZING:
            raise ValueError(f"Cannot fail analysis. Current status: {self.status.value}")
        
        self.status = ContractStatus.FAILED
        
        self.raise_event(AnalysisFailedEvent(
            contract_id=self.id,
            error_message=error_message,
            failed_at=datetime.utcnow()
        ))
    
    def apply_rewrite(self, rewritten_code: str):
        """Apply rewritten code to the contract."""
        if self.status != ContractStatus.COMPLETED:
            raise ValueError("Cannot apply rewrite to incomplete analysis")
        
        if not rewritten_code.strip():
            raise ValueError("Rewritten code cannot be empty")
        
        self.rewritten_code = rewritten_code
        self._version += 1
        
        self.raise_event(ContractRewrittenEvent(
            contract_id=self.id,
            version=self._version,
            rewritten_at=datetime.utcnow()
        ))
    
    def is_high_risk(self) -> bool:
        """Check if contract has high security risks."""
        if not self.analysis_result:
            return True  # Unknown risk is treated as high risk
        
        return (
            self.analysis_result.critical_vulnerabilities_count > 0 or
            self.analysis_result.high_vulnerabilities_count > 2 or
            self.analysis_result.security_score < 60
        )
    
    def get_analysis_duration(self) -> Optional[float]:
        """Get analysis duration in seconds."""
        if not self.analysis_started_at or not self.analysis_completed_at:
            return None
        
        return (self.analysis_completed_at - self.analysis_started_at).total_seconds()
    
    @property
    def version(self) -> int:
        """Get contract version."""
        return self._version


# Domain Events
@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ContractCreatedEvent(DomainEvent):
    contract_id: EntityId
    organization_id: EntityId
    user_id: EntityId
    contract_type: str


@dataclass(frozen=True)
class AnalysisStartedEvent(DomainEvent):
    contract_id: EntityId
    started_at: datetime


@dataclass(frozen=True)
class AnalysisCompletedEvent(DomainEvent):
    contract_id: EntityId
    analysis_result: AnalysisResult
    completed_at: datetime


@dataclass(frozen=True)
class AnalysisFailedEvent(DomainEvent):
    contract_id: EntityId
    error_message: str
    failed_at: datetime


@dataclass(frozen=True)
class ContractRewrittenEvent(DomainEvent):
    contract_id: EntityId
    version: int
    rewritten_at: datetime
