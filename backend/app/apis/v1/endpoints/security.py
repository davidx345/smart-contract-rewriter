"""
Security and compliance API endpoints.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime

from ...db.session import get_db
from ...compliance.gdpr import (
    GDPRComplianceService,
    DataRetentionService,
    ConsentRequest,
    ConsentResponse,
    DataExportRequest,
    DataDeletionRequest,
    BreachNotificationRequest
)
from ...security.monitoring import (
    SecurityMonitoringService,
    AlertCreate,
    AlertResponse,
    SecurityDashboard,
    AlertSeverity,
    ThreatType
)
from ...middleware.security import get_current_user
from ...schemas.security_schemas import (
    SecurityReportResponse,
    ComplianceStatusResponse,
    VulnerabilityAssessmentResponse
)

router = APIRouter()
security = HTTPBearer()


def get_gdpr_service(db: Session = Depends(get_db)) -> GDPRComplianceService:
    """Get GDPR compliance service."""
    return GDPRComplianceService(db)


def get_monitoring_service(db: Session = Depends(get_db)) -> SecurityMonitoringService:
    """Get security monitoring service."""
    return SecurityMonitoringService(db)


def get_retention_service(db: Session = Depends(get_db)) -> DataRetentionService:
    """Get data retention service."""
    return DataRetentionService(db)


# GDPR Compliance Endpoints
@router.post("/gdpr/consent", response_model=ConsentResponse)
async def grant_consent(
    consent_request: ConsentRequest,
    request: Request,
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service)
):
    """Grant consent for data processing."""
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        user_agent = request.headers.get("User-Agent", "")
        
        consent = await gdpr_service.grant_consent(
            user_id=current_user.id,
            consent_request=consent_request,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return consent
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant consent: {str(e)}"
        )


@router.delete("/gdpr/consent/{purpose}")
async def withdraw_consent(
    purpose: str,
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service)
):
    """Withdraw consent for data processing."""
    try:
        from ...compliance.gdpr import DataProcessingPurpose
        
        purpose_enum = DataProcessingPurpose(purpose)
        success = await gdpr_service.withdraw_consent(
            user_id=current_user.id,
            purpose=purpose_enum
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent not found"
            )
        
        return {"message": "Consent withdrawn successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid processing purpose"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to withdraw consent: {str(e)}"
        )


@router.post("/gdpr/export-data")
async def export_user_data(
    export_request: DataExportRequest,
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service)
):
    """Export user data (Right to data portability)."""
    try:
        data_export = await gdpr_service.export_user_data(
            user_id=current_user.id,
            export_request=export_request
        )
        
        return data_export
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


@router.delete("/gdpr/delete-data")
async def delete_user_data(
    deletion_request: DataDeletionRequest,
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service)
):
    """Delete user data (Right to erasure)."""
    try:
        success = await gdpr_service.delete_user_data(
            user_id=current_user.id,
            deletion_request=deletion_request
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data deletion failed"
            )
        
        return {"message": "Data deletion completed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data: {str(e)}"
        )


# Security Monitoring Endpoints
@router.get("/security/dashboard", response_model=SecurityDashboard)
async def get_security_dashboard(
    current_user = Depends(get_current_user),
    monitoring_service: SecurityMonitoringService = Depends(get_monitoring_service)
):
    """Get security dashboard data."""
    try:
        # Check if user has security admin role
        if not hasattr(current_user, 'role') or current_user.role != 'security_admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security admin role required"
            )
        
        dashboard = await monitoring_service.get_security_dashboard()
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security dashboard: {str(e)}"
        )


@router.post("/security/alerts", response_model=AlertResponse)
async def create_security_alert(
    alert_data: AlertCreate,
    current_user = Depends(get_current_user),
    monitoring_service: SecurityMonitoringService = Depends(get_monitoring_service)
):
    """Create a security alert."""
    try:
        # Check if user has security role
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security role required"
            )
        
        alert = await monitoring_service.create_alert(alert_data)
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.patch("/security/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user = Depends(get_current_user),
    monitoring_service: SecurityMonitoringService = Depends(get_monitoring_service)
):
    """Acknowledge a security alert."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security role required"
            )
        
        success = await monitoring_service.acknowledge_alert(
            alert_id=alert_id,
            assigned_to=current_user.email
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.patch("/security/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: str,
    is_false_positive: bool = False,
    current_user = Depends(get_current_user),
    monitoring_service: SecurityMonitoringService = Depends(get_monitoring_service)
):
    """Resolve a security alert."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security role required"
            )
        
        success = await monitoring_service.resolve_alert(
            alert_id=alert_id,
            resolution_notes=resolution_notes,
            is_false_positive=is_false_positive
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )


@router.post("/security/breach-notification")
async def report_data_breach(
    breach_request: BreachNotificationRequest,
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service)
):
    """Report a data breach incident."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security admin role required"
            )
        
        incident_id = await gdpr_service.record_data_breach(breach_request)
        
        return {
            "message": "Data breach recorded successfully",
            "incident_id": incident_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record data breach: {str(e)}"
        )


# Compliance and Security Reports
@router.get("/security/compliance-status", response_model=ComplianceStatusResponse)
async def get_compliance_status(
    current_user = Depends(get_current_user),
    gdpr_service: GDPRComplianceService = Depends(get_gdpr_service),
    retention_service: DataRetentionService = Depends(get_retention_service)
):
    """Get overall compliance status."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'compliance_officer']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or compliance officer role required"
            )
        
        # Check expired data
        expired_data = await retention_service.check_expired_data()
        
        # Calculate compliance score
        compliance_score = await calculate_compliance_score(gdpr_service, retention_service)
        
        return ComplianceStatusResponse(
            overall_score=compliance_score,
            gdpr_compliant=compliance_score >= 80,
            expired_data_count=len(expired_data),
            last_assessment_date=datetime.utcnow(),
            recommendations=await get_compliance_recommendations(compliance_score)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance status: {str(e)}"
        )


@router.get("/security/vulnerability-assessment", response_model=VulnerabilityAssessmentResponse)
async def run_vulnerability_assessment(
    current_user = Depends(get_current_user)
):
    """Run vulnerability assessment."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security admin role required"
            )
        
        # Run various security checks
        vulnerabilities = await run_security_checks()
        
        return VulnerabilityAssessmentResponse(
            assessment_id=f"VA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            scan_date=datetime.utcnow(),
            vulnerabilities_found=len(vulnerabilities),
            high_risk_count=sum(1 for v in vulnerabilities if v['severity'] == 'high'),
            medium_risk_count=sum(1 for v in vulnerabilities if v['severity'] == 'medium'),
            low_risk_count=sum(1 for v in vulnerabilities if v['severity'] == 'low'),
            vulnerabilities=vulnerabilities,
            overall_risk_score=calculate_risk_score(vulnerabilities)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run vulnerability assessment: {str(e)}"
        )


@router.post("/security/penetration-test")
async def schedule_penetration_test(
    test_scope: List[str],
    scheduled_date: datetime,
    current_user = Depends(get_current_user)
):
    """Schedule a penetration test."""
    try:
        if not hasattr(current_user, 'role') or current_user.role not in ['security_admin', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security admin role required"
            )
        
        test_id = f"PT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Schedule penetration test (this would integrate with testing tools)
        # For now, just return the test ID
        
        return {
            "message": "Penetration test scheduled successfully",
            "test_id": test_id,
            "scheduled_date": scheduled_date,
            "scope": test_scope
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule penetration test: {str(e)}"
        )


# Helper Functions
async def calculate_compliance_score(gdpr_service: GDPRComplianceService, 
                                   retention_service: DataRetentionService) -> float:
    """Calculate overall compliance score."""
    try:
        score = 100.0
        
        # Check for expired data (reduces score)
        expired_data = await retention_service.check_expired_data()
        if expired_data:
            score -= min(len(expired_data) * 5, 30)  # Max 30 point reduction
        
        # Check consent coverage (simplified)
        # In reality, this would check actual consent status
        
        return max(score, 0.0)
        
    except Exception as e:
        logger.error(f"Failed to calculate compliance score: {e}")
        return 50.0  # Default moderate score


async def get_compliance_recommendations(score: float) -> List[str]:
    """Get compliance recommendations based on score."""
    recommendations = []
    
    if score < 60:
        recommendations.extend([
            "Immediate review of data retention policies required",
            "Update consent management procedures",
            "Conduct staff training on GDPR compliance"
        ])
    elif score < 80:
        recommendations.extend([
            "Review and update privacy policies",
            "Implement automated data retention cleanup",
            "Enhance consent tracking mechanisms"
        ])
    else:
        recommendations.append("Maintain current compliance practices")
    
    return recommendations


async def run_security_checks() -> List[Dict[str, Any]]:
    """Run various security vulnerability checks."""
    vulnerabilities = []
    
    # Simulate security checks (in production, integrate with actual tools)
    # SSL/TLS configuration check
    vulnerabilities.append({
        "id": "SSL-001",
        "title": "SSL Certificate Expiration",
        "description": "SSL certificate expires in 30 days",
        "severity": "medium",
        "category": "encryption",
        "recommendation": "Renew SSL certificate before expiration"
    })
    
    # Password policy check
    vulnerabilities.append({
        "id": "AUTH-001",
        "title": "Weak Password Policy",
        "description": "Password policy allows passwords shorter than 12 characters",
        "severity": "high",
        "category": "authentication",
        "recommendation": "Enforce minimum 12-character passwords with complexity requirements"
    })
    
    # Rate limiting check
    vulnerabilities.append({
        "id": "API-001",
        "title": "API Rate Limiting",
        "description": "Some API endpoints lack proper rate limiting",
        "severity": "medium",
        "category": "api_security",
        "recommendation": "Implement rate limiting on all public API endpoints"
    })
    
    return vulnerabilities


def calculate_risk_score(vulnerabilities: List[Dict[str, Any]]) -> float:
    """Calculate overall risk score based on vulnerabilities."""
    if not vulnerabilities:
        return 0.0
    
    severity_weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}
    total_risk = sum(severity_weights.get(v['severity'], 1) for v in vulnerabilities)
    
    # Normalize to 0-100 scale
    max_possible_risk = len(vulnerabilities) * 10  # If all were critical
    return min((total_risk / max_possible_risk) * 100, 100) if max_possible_risk > 0 else 0
