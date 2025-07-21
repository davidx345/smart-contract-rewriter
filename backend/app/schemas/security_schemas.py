"""
Security and compliance related Pydantic schemas.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class SecuritySeverity(str, Enum):
    """Security severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Compliance status levels."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNDER_REVIEW = "under_review"


class VulnerabilityCategory(str, Enum):
    """Vulnerability categories."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    INPUT_VALIDATION = "input_validation"
    API_SECURITY = "api_security"
    CONFIGURATION = "configuration"
    NETWORK_SECURITY = "network_security"
    DATA_PROTECTION = "data_protection"


# Security Alert Schemas
class SecurityAlertBase(BaseModel):
    """Base security alert schema."""
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    severity: SecuritySeverity = Field(..., description="Alert severity")
    category: str = Field(..., description="Alert category")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    target_endpoint: Optional[str] = Field(None, description="Target endpoint")
    risk_score: float = Field(0.0, ge=0.0, le=10.0, description="Risk score (0-10)")


class SecurityAlertCreate(SecurityAlertBase):
    """Create security alert schema."""
    technical_details: Optional[Dict[str, Any]] = Field(None, description="Technical details")
    affected_systems: Optional[List[str]] = Field(None, description="Affected systems")


class SecurityAlertResponse(SecurityAlertBase):
    """Security alert response schema."""
    id: int
    alert_id: str
    status: str
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    
    class Config:
        from_attributes = True


# Vulnerability Assessment Schemas
class VulnerabilityBase(BaseModel):
    """Base vulnerability schema."""
    id: str = Field(..., description="Vulnerability ID")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Vulnerability description")
    severity: SecuritySeverity = Field(..., description="Vulnerability severity")
    category: VulnerabilityCategory = Field(..., description="Vulnerability category")
    recommendation: str = Field(..., description="Remediation recommendation")


class VulnerabilityDetail(VulnerabilityBase):
    """Detailed vulnerability information."""
    cve_id: Optional[str] = Field(None, description="CVE identifier")
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS score")
    affected_components: List[str] = Field(default_factory=list, description="Affected components")
    exploit_availability: bool = Field(False, description="Whether exploit is publicly available")
    remediation_effort: str = Field("medium", description="Effort required for remediation")
    
    @validator('cvss_score')
    def validate_cvss_score(cls, v):
        if v is not None and (v < 0.0 or v > 10.0):
            raise ValueError('CVSS score must be between 0.0 and 10.0')
        return v


class VulnerabilityAssessmentResponse(BaseModel):
    """Vulnerability assessment response."""
    assessment_id: str = Field(..., description="Assessment ID")
    scan_date: datetime = Field(..., description="Scan date")
    vulnerabilities_found: int = Field(..., ge=0, description="Total vulnerabilities found")
    critical_count: int = Field(0, ge=0, description="Critical vulnerabilities")
    high_risk_count: int = Field(0, ge=0, description="High risk vulnerabilities")
    medium_risk_count: int = Field(0, ge=0, description="Medium risk vulnerabilities")
    low_risk_count: int = Field(0, ge=0, description="Low risk vulnerabilities")
    overall_risk_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall risk score")
    vulnerabilities: List[VulnerabilityDetail] = Field(default_factory=list, description="Detailed vulnerabilities")


# Compliance Schemas
class ComplianceCheckBase(BaseModel):
    """Base compliance check schema."""
    check_id: str = Field(..., description="Compliance check ID")
    name: str = Field(..., description="Check name")
    description: str = Field(..., description="Check description")
    framework: str = Field(..., description="Compliance framework (GDPR, SOX, etc.)")
    category: str = Field(..., description="Compliance category")


class ComplianceCheckResult(ComplianceCheckBase):
    """Compliance check result."""
    status: ComplianceStatus = Field(..., description="Compliance status")
    score: float = Field(0.0, ge=0.0, le=100.0, description="Compliance score (0-100)")
    findings: List[str] = Field(default_factory=list, description="Findings and issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Supporting evidence")
    last_checked: datetime = Field(..., description="Last check date")


class ComplianceStatusResponse(BaseModel):
    """Overall compliance status response."""
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score")
    gdpr_compliant: bool = Field(..., description="GDPR compliance status")
    sox_compliant: bool = Field(True, description="SOX compliance status")
    pci_compliant: bool = Field(True, description="PCI compliance status")
    expired_data_count: int = Field(0, ge=0, description="Count of expired data")
    last_assessment_date: datetime = Field(..., description="Last assessment date")
    compliance_checks: List[ComplianceCheckResult] = Field(default_factory=list, description="Individual check results")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")


# Security Report Schemas
class SecurityMetricBase(BaseModel):
    """Base security metric schema."""
    metric_name: str = Field(..., description="Metric name")
    metric_value: float = Field(..., description="Metric value")
    metric_type: str = Field(..., description="Metric type (counter, gauge, histogram)")
    unit: Optional[str] = Field(None, description="Metric unit")
    timestamp: datetime = Field(..., description="Metric timestamp")


class SecurityMetricTrend(SecurityMetricBase):
    """Security metric with trend data."""
    trend_direction: str = Field(..., description="Trend direction (up, down, stable)")
    trend_percentage: float = Field(0.0, description="Trend percentage change")
    previous_value: Optional[float] = Field(None, description="Previous metric value")


class SecurityDashboardStats(BaseModel):
    """Security dashboard statistics."""
    total_alerts: int = Field(0, ge=0, description="Total alerts")
    active_alerts: int = Field(0, ge=0, description="Active alerts")
    critical_alerts: int = Field(0, ge=0, description="Critical alerts")
    resolved_alerts: int = Field(0, ge=0, description="Resolved alerts")
    false_positives: int = Field(0, ge=0, description="False positive alerts")
    average_response_time: float = Field(0.0, ge=0.0, description="Average response time in hours")
    threats_blocked_today: int = Field(0, ge=0, description="Threats blocked today")
    security_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall security score")


class SecurityReportResponse(BaseModel):
    """Security report response."""
    report_id: str = Field(..., description="Report ID")
    report_type: str = Field(..., description="Report type")
    generated_at: datetime = Field(..., description="Report generation date")
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    statistics: SecurityDashboardStats = Field(..., description="Security statistics")
    metrics: List[SecurityMetricTrend] = Field(default_factory=list, description="Security metrics")
    top_threats: List[Dict[str, Any]] = Field(default_factory=list, description="Top threats")
    recent_incidents: List[SecurityAlertResponse] = Field(default_factory=list, description="Recent incidents")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")


# Penetration Testing Schemas
class PenetrationTestBase(BaseModel):
    """Base penetration test schema."""
    test_name: str = Field(..., description="Test name")
    test_type: str = Field(..., description="Test type (black-box, white-box, gray-box)")
    scope: List[str] = Field(..., description="Test scope")
    objectives: List[str] = Field(..., description="Test objectives")


class PenetrationTestRequest(PenetrationTestBase):
    """Penetration test request."""
    scheduled_date: datetime = Field(..., description="Scheduled test date")
    duration_hours: int = Field(8, ge=1, le=168, description="Test duration in hours")
    tester_contact: str = Field(..., description="Tester contact information")
    approval_required: bool = Field(True, description="Whether approval is required")


class PenetrationTestResult(PenetrationTestBase):
    """Penetration test result."""
    test_id: str = Field(..., description="Test ID")
    start_date: datetime = Field(..., description="Test start date")
    end_date: datetime = Field(..., description="Test end date")
    tester: str = Field(..., description="Tester name/company")
    overall_risk: SecuritySeverity = Field(..., description="Overall risk level")
    vulnerabilities_found: List[VulnerabilityDetail] = Field(default_factory=list, description="Vulnerabilities found")
    executive_summary: str = Field(..., description="Executive summary")
    detailed_findings: str = Field(..., description="Detailed findings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    report_url: Optional[str] = Field(None, description="Full report URL")


# Data Privacy Schemas
class DataPrivacyAssessmentBase(BaseModel):
    """Base data privacy assessment schema."""
    assessment_id: str = Field(..., description="Assessment ID")
    data_type: str = Field(..., description="Type of data assessed")
    processing_purpose: str = Field(..., description="Purpose of data processing")
    legal_basis: str = Field(..., description="Legal basis for processing")


class DataPrivacyAssessmentResponse(DataPrivacyAssessmentBase):
    """Data privacy assessment response."""
    assessment_date: datetime = Field(..., description="Assessment date")
    privacy_score: float = Field(0.0, ge=0.0, le=100.0, description="Privacy score")
    consent_coverage: float = Field(0.0, ge=0.0, le=100.0, description="Consent coverage percentage")
    retention_compliance: bool = Field(True, description="Retention policy compliance")
    deletion_rights_enabled: bool = Field(True, description="Data deletion rights enabled")
    export_rights_enabled: bool = Field(True, description="Data export rights enabled")
    findings: List[str] = Field(default_factory=list, description="Assessment findings")
    recommendations: List[str] = Field(default_factory=list, description="Privacy recommendations")


# Audit Log Schemas
class AuditLogEntry(BaseModel):
    """Audit log entry schema."""
    id: str = Field(..., description="Log entry ID")
    timestamp: datetime = Field(..., description="Entry timestamp")
    user_id: Optional[str] = Field(None, description="User ID")
    user_email: Optional[str] = Field(None, description="User email")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    source_ip: str = Field(..., description="Source IP address")
    user_agent: str = Field(..., description="User agent")
    success: bool = Field(True, description="Whether action was successful")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class AuditLogQuery(BaseModel):
    """Audit log query parameters."""
    start_date: Optional[datetime] = Field(None, description="Start date for query")
    end_date: Optional[datetime] = Field(None, description="End date for query")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action")
    resource: Optional[str] = Field(None, description="Filter by resource")
    source_ip: Optional[str] = Field(None, description="Filter by source IP")
    success: Optional[bool] = Field(None, description="Filter by success status")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class AuditLogResponse(BaseModel):
    """Audit log response."""
    total_count: int = Field(..., ge=0, description="Total number of matching entries")
    entries: List[AuditLogEntry] = Field(..., description="Audit log entries")
    has_more: bool = Field(False, description="Whether more results are available")


# Risk Assessment Schemas
class RiskFactor(BaseModel):
    """Risk factor schema."""
    factor_id: str = Field(..., description="Risk factor ID")
    name: str = Field(..., description="Risk factor name")
    description: str = Field(..., description="Risk factor description")
    impact: SecuritySeverity = Field(..., description="Potential impact")
    likelihood: str = Field(..., description="Likelihood (low, medium, high)")
    current_controls: List[str] = Field(default_factory=list, description="Current controls in place")
    residual_risk: SecuritySeverity = Field(..., description="Residual risk after controls")


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    assessment_id: str = Field(..., description="Assessment ID")
    assessment_date: datetime = Field(..., description="Assessment date")
    scope: str = Field(..., description="Assessment scope")
    overall_risk_level: SecuritySeverity = Field(..., description="Overall risk level")
    risk_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall risk score")
    risk_factors: List[RiskFactor] = Field(..., description="Identified risk factors")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Mitigation strategies")
    next_review_date: datetime = Field(..., description="Next review date")


# Security Training Schemas
class SecurityTrainingModule(BaseModel):
    """Security training module schema."""
    module_id: str = Field(..., description="Module ID")
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module description")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    difficulty_level: str = Field(..., description="Difficulty level")
    topics: List[str] = Field(..., description="Topics covered")
    completion_rate: float = Field(0.0, ge=0.0, le=100.0, description="Completion rate percentage")


class SecurityTrainingResponse(BaseModel):
    """Security training response."""
    user_id: str = Field(..., description="User ID")
    modules_completed: int = Field(0, ge=0, description="Modules completed")
    total_modules: int = Field(..., ge=0, description="Total modules available")
    completion_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Overall completion percentage")
    certificates_earned: List[str] = Field(default_factory=list, description="Certificates earned")
    last_activity: Optional[datetime] = Field(None, description="Last training activity")
    modules: List[SecurityTrainingModule] = Field(..., description="Available modules")
