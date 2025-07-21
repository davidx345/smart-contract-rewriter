"""
GDPR Compliance features for enterprise data protection.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..models.contract_models import Base
from ..core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DataProcessingPurpose(str, Enum):
    """Legal purposes for data processing under GDPR."""
    CONTRACT_ANALYSIS = "contract_analysis"
    USER_AUTHENTICATION = "user_authentication"
    BILLING_PAYMENT = "billing_payment"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class ConsentStatus(str, Enum):
    """GDPR consent status."""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"


class DataCategory(str, Enum):
    """Categories of personal data."""
    IDENTIFICATION = "identification"  # Name, email, ID
    CONTACT = "contact"  # Phone, address
    AUTHENTICATION = "authentication"  # Passwords, tokens
    BEHAVIORAL = "behavioral"  # Usage patterns, preferences
    TECHNICAL = "technical"  # IP addresses, device info
    FINANCIAL = "financial"  # Payment info, billing
    CONTRACTUAL = "contractual"  # Smart contracts, analysis results


# GDPR Models
class GDPRConsent(Base):
    """Track user consent for data processing."""
    __tablename__ = "gdpr_consents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    purpose = Column(String(50), nullable=False)  # DataProcessingPurpose
    status = Column(String(20), nullable=False)  # ConsentStatus
    granted_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    consent_text = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="gdpr_consents")


class DataProcessingRecord(Base):
    """Record of data processing activities (GDPR Article 30)."""
    __tablename__ = "data_processing_records"
    
    id = Column(Integer, primary_key=True, index=True)
    processing_purpose = Column(String(50), nullable=False)
    data_categories = Column(Text, nullable=False)  # JSON array of categories
    data_subjects = Column(String(100), nullable=False)  # e.g., "customers", "employees"
    recipients = Column(Text, nullable=True)  # Who receives the data
    retention_period = Column(String(100), nullable=False)
    security_measures = Column(Text, nullable=False)
    legal_basis = Column(String(100), nullable=False)
    third_country_transfers = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataBreachRecord(Base):
    """Record data breaches for GDPR compliance."""
    __tablename__ = "data_breach_records"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), unique=True, nullable=False)
    detected_at = Column(DateTime, nullable=False)
    reported_to_authority_at = Column(DateTime, nullable=True)
    reported_to_subjects_at = Column(DateTime, nullable=True)
    breach_type = Column(String(50), nullable=False)  # confidentiality, integrity, availability
    affected_data_categories = Column(Text, nullable=False)  # JSON array
    affected_subjects_count = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high
    description = Column(Text, nullable=False)
    containment_measures = Column(Text, nullable=True)
    notification_required = Column(Boolean, default=True)
    authority_notified = Column(Boolean, default=False)
    subjects_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataRetentionPolicy(Base):
    """Data retention policies per data category."""
    __tablename__ = "data_retention_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    data_category = Column(String(50), nullable=False)
    processing_purpose = Column(String(50), nullable=False)
    retention_period_days = Column(Integer, nullable=False)
    legal_basis = Column(String(100), nullable=False)
    deletion_criteria = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class ConsentRequest(BaseModel):
    """Request model for granting consent."""
    purpose: DataProcessingPurpose
    consent_text: str
    expires_in_days: Optional[int] = None


class ConsentResponse(BaseModel):
    """Response model for consent."""
    id: int
    purpose: str
    status: str
    granted_at: Optional[datetime]
    expires_at: Optional[datetime]
    consent_text: str


class DataExportRequest(BaseModel):
    """Request for data export (Right to data portability)."""
    data_categories: List[DataCategory]
    format: str = Field(default="json", regex="^(json|xml|csv)$")


class DataDeletionRequest(BaseModel):
    """Request for data deletion (Right to erasure)."""
    reason: str
    data_categories: Optional[List[DataCategory]] = None
    confirm_deletion: bool = False


class BreachNotificationRequest(BaseModel):
    """Data breach notification model."""
    breach_type: str
    affected_data_categories: List[str]
    affected_subjects_count: int
    risk_level: str
    description: str
    containment_measures: Optional[str] = None


# GDPR Service Classes
class GDPRComplianceService:
    """Service for GDPR compliance operations."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def grant_consent(self, user_id: int, consent_request: ConsentRequest, 
                          ip_address: str, user_agent: str) -> ConsentResponse:
        """Grant user consent for data processing."""
        try:
            # Check if consent already exists
            existing_consent = self.db.query(GDPRConsent).filter(
                GDPRConsent.user_id == user_id,
                GDPRConsent.purpose == consent_request.purpose.value
            ).first()
            
            if existing_consent:
                # Update existing consent
                existing_consent.status = ConsentStatus.GIVEN.value
                existing_consent.granted_at = datetime.utcnow()
                existing_consent.consent_text = consent_request.consent_text
                existing_consent.ip_address = ip_address
                existing_consent.user_agent = user_agent
                
                if consent_request.expires_in_days:
                    existing_consent.expires_at = datetime.utcnow() + timedelta(days=consent_request.expires_in_days)
                
                consent = existing_consent
            else:
                # Create new consent
                expires_at = None
                if consent_request.expires_in_days:
                    expires_at = datetime.utcnow() + timedelta(days=consent_request.expires_in_days)
                
                consent = GDPRConsent(
                    user_id=user_id,
                    purpose=consent_request.purpose.value,
                    status=ConsentStatus.GIVEN.value,
                    granted_at=datetime.utcnow(),
                    expires_at=expires_at,
                    consent_text=consent_request.consent_text,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                self.db.add(consent)
            
            self.db.commit()
            self.db.refresh(consent)
            
            return ConsentResponse(
                id=consent.id,
                purpose=consent.purpose,
                status=consent.status,
                granted_at=consent.granted_at,
                expires_at=consent.expires_at,
                consent_text=consent.consent_text
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to grant consent: {e}")
            raise
    
    async def withdraw_consent(self, user_id: int, purpose: DataProcessingPurpose) -> bool:
        """Withdraw user consent."""
        try:
            consent = self.db.query(GDPRConsent).filter(
                GDPRConsent.user_id == user_id,
                GDPRConsent.purpose == purpose.value
            ).first()
            
            if consent:
                consent.status = ConsentStatus.WITHDRAWN.value
                consent.withdrawn_at = datetime.utcnow()
                self.db.commit()
                
                # Trigger data processing stop for this purpose
                await self._stop_data_processing(user_id, purpose)
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to withdraw consent: {e}")
            raise
    
    async def export_user_data(self, user_id: int, export_request: DataExportRequest) -> Dict[str, Any]:
        """Export user data (Right to data portability)."""
        try:
            data_export = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data_categories": [cat.value for cat in export_request.data_categories],
                "data": {}
            }
            
            # Export data by category
            for category in export_request.data_categories:
                data_export["data"][category.value] = await self._export_data_category(user_id, category)
            
            # Log the export request
            await self._log_data_access("export", user_id, export_request.data_categories)
            
            return data_export
            
        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            raise
    
    async def delete_user_data(self, user_id: int, deletion_request: DataDeletionRequest) -> bool:
        """Delete user data (Right to erasure)."""
        try:
            if not deletion_request.confirm_deletion:
                raise ValueError("Deletion must be confirmed")
            
            categories_to_delete = deletion_request.data_categories or list(DataCategory)
            
            # Check if deletion is legally permissible
            can_delete = await self._check_deletion_permissibility(user_id, categories_to_delete)
            if not can_delete:
                raise ValueError("Data deletion not permitted due to legal obligations")
            
            # Perform deletion by category
            for category in categories_to_delete:
                await self._delete_data_category(user_id, category)
            
            # Log the deletion
            await self._log_data_access("deletion", user_id, categories_to_delete, deletion_request.reason)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            raise
    
    async def record_data_breach(self, breach_request: BreachNotificationRequest) -> str:
        """Record a data breach incident."""
        try:
            incident_id = f"BR-{datetime.utcnow().strftime('%Y%m%d')}-{self.db.query(DataBreachRecord).count() + 1:04d}"
            
            breach = DataBreachRecord(
                incident_id=incident_id,
                detected_at=datetime.utcnow(),
                breach_type=breach_request.breach_type,
                affected_data_categories=",".join(breach_request.affected_data_categories),
                affected_subjects_count=breach_request.affected_subjects_count,
                risk_level=breach_request.risk_level,
                description=breach_request.description,
                containment_measures=breach_request.containment_measures,
                notification_required=breach_request.risk_level in ["medium", "high"]
            )
            
            self.db.add(breach)
            self.db.commit()
            
            # If high risk, schedule immediate notifications
            if breach_request.risk_level == "high":
                await self._schedule_breach_notifications(incident_id)
            
            return incident_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record data breach: {e}")
            raise
    
    async def _export_data_category(self, user_id: int, category: DataCategory) -> Dict[str, Any]:
        """Export data for a specific category."""
        # This would implement actual data export logic based on category
        # For now, return placeholder structure
        return {
            "category": category.value,
            "exported_at": datetime.utcnow().isoformat(),
            "records": []  # Would contain actual data
        }
    
    async def _delete_data_category(self, user_id: int, category: DataCategory):
        """Delete data for a specific category."""
        # This would implement actual data deletion logic based on category
        pass
    
    async def _check_deletion_permissibility(self, user_id: int, categories: List[DataCategory]) -> bool:
        """Check if data deletion is legally permissible."""
        # Check retention policies and legal obligations
        return True  # Simplified for demo
    
    async def _stop_data_processing(self, user_id: int, purpose: DataProcessingPurpose):
        """Stop data processing for a specific purpose after consent withdrawal."""
        # Implement logic to stop automated processing
        pass
    
    async def _log_data_access(self, access_type: str, user_id: int, categories: List[DataCategory], reason: str = None):
        """Log data access for audit purposes."""
        pass
    
    async def _schedule_breach_notifications(self, incident_id: str):
        """Schedule notifications to authorities and data subjects."""
        # Implement notification scheduling
        pass


class DataRetentionService:
    """Service for managing data retention policies."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_retention_policy(self, category: DataCategory, purpose: DataProcessingPurpose,
                                    retention_days: int, legal_basis: str, deletion_criteria: str) -> int:
        """Create a new data retention policy."""
        try:
            policy = DataRetentionPolicy(
                data_category=category.value,
                processing_purpose=purpose.value,
                retention_period_days=retention_days,
                legal_basis=legal_basis,
                deletion_criteria=deletion_criteria
            )
            
            self.db.add(policy)
            self.db.commit()
            self.db.refresh(policy)
            
            return policy.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create retention policy: {e}")
            raise
    
    async def check_expired_data(self) -> List[Dict[str, Any]]:
        """Check for data that has exceeded retention periods."""
        try:
            expired_items = []
            policies = self.db.query(DataRetentionPolicy).filter(DataRetentionPolicy.is_active == True).all()
            
            for policy in policies:
                # Check for expired data based on policy
                # This would implement actual expiration checking logic
                pass
            
            return expired_items
            
        except Exception as e:
            logger.error(f"Failed to check expired data: {e}")
            raise
    
    async def auto_delete_expired_data(self) -> int:
        """Automatically delete data that has exceeded retention periods."""
        try:
            expired_items = await self.check_expired_data()
            deleted_count = 0
            
            for item in expired_items:
                # Implement actual deletion logic
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to auto-delete expired data: {e}")
            raise
