"""
Security monitoring and alerting system.
"""
import logging
import smtplib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from enum import Enum
from pydantic import BaseModel
import redis
import asyncio
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float

from ..models.contract_models import Base
from ..core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client for real-time monitoring
redis_client = redis.Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    decode_responses=True
)


class AlertSeverity(str, Enum):
    """Security alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AlertStatus(str, Enum):
    """Alert status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# Security Models
class SecurityAlert(Base):
    """Security alerts and incidents."""
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, nullable=False)
    severity = Column(String(20), nullable=False)  # AlertSeverity
    threat_type = Column(String(50), nullable=False)  # ThreatType
    status = Column(String(20), default=AlertStatus.OPEN.value)
    source_ip = Column(String(45), nullable=True)
    target_endpoint = Column(String(500), nullable=True)
    description = Column(Text, nullable=False)
    technical_details = Column(Text, nullable=True)  # JSON
    affected_systems = Column(Text, nullable=True)  # JSON array
    risk_score = Column(Float, nullable=False, default=0.0)
    detected_at = Column(DateTime, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityMetric(Base):
    """Security metrics for monitoring."""
    __tablename__ = "security_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    tags = Column(Text, nullable=True)  # JSON for additional context
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


# Pydantic Models
class AlertCreate(BaseModel):
    """Create security alert."""
    severity: AlertSeverity
    threat_type: ThreatType
    source_ip: Optional[str] = None
    target_endpoint: Optional[str] = None
    description: str
    technical_details: Optional[Dict[str, Any]] = None
    affected_systems: Optional[List[str]] = None
    risk_score: float = 0.0


class AlertResponse(BaseModel):
    """Security alert response."""
    id: int
    alert_id: str
    severity: str
    threat_type: str
    status: str
    description: str
    risk_score: float
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]


class SecurityDashboard(BaseModel):
    """Security dashboard data."""
    active_alerts: int
    critical_alerts: int
    threats_blocked_today: int
    average_response_time: float
    top_threat_types: List[Dict[str, Any]]
    recent_alerts: List[AlertResponse]


# Security Monitoring Service
class SecurityMonitoringService:
    """Service for security monitoring and alerting."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.alert_handlers = {
            AlertSeverity.CRITICAL: self._handle_critical_alert,
            AlertSeverity.HIGH: self._handle_high_alert,
            AlertSeverity.MEDIUM: self._handle_medium_alert,
            AlertSeverity.LOW: self._handle_low_alert
        }
    
    async def create_alert(self, alert_data: AlertCreate) -> AlertResponse:
        """Create a new security alert."""
        try:
            alert_id = f"SEC-{datetime.utcnow().strftime('%Y%m%d')}-{self.db.query(SecurityAlert).count() + 1:06d}"
            
            alert = SecurityAlert(
                alert_id=alert_id,
                severity=alert_data.severity.value,
                threat_type=alert_data.threat_type.value,
                source_ip=alert_data.source_ip,
                target_endpoint=alert_data.target_endpoint,
                description=alert_data.description,
                technical_details=json.dumps(alert_data.technical_details) if alert_data.technical_details else None,
                affected_systems=json.dumps(alert_data.affected_systems) if alert_data.affected_systems else None,
                risk_score=alert_data.risk_score,
                detected_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            # Handle alert based on severity
            await self.alert_handlers[alert_data.severity](alert)
            
            # Store in Redis for real-time monitoring
            await self._store_alert_in_redis(alert)
            
            return AlertResponse(
                id=alert.id,
                alert_id=alert.alert_id,
                severity=alert.severity,
                threat_type=alert.threat_type,
                status=alert.status,
                description=alert.description,
                risk_score=alert.risk_score,
                detected_at=alert.detected_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create security alert: {e}")
            raise
    
    async def get_security_dashboard(self) -> SecurityDashboard:
        """Get security dashboard data."""
        try:
            # Get active alerts
            active_alerts = self.db.query(SecurityAlert).filter(
                SecurityAlert.status.in_([AlertStatus.OPEN.value, AlertStatus.INVESTIGATING.value])
            ).count()
            
            # Get critical alerts
            critical_alerts = self.db.query(SecurityAlert).filter(
                SecurityAlert.severity == AlertSeverity.CRITICAL.value,
                SecurityAlert.status.in_([AlertStatus.OPEN.value, AlertStatus.INVESTIGATING.value])
            ).count()
            
            # Get threats blocked today
            today = datetime.utcnow().date()
            threats_blocked = self.db.query(SecurityAlert).filter(
                SecurityAlert.detected_at >= today,
                SecurityAlert.threat_type.in_([
                    ThreatType.SQL_INJECTION.value,
                    ThreatType.XSS.value,
                    ThreatType.DDOS.value
                ])
            ).count()
            
            # Calculate average response time
            resolved_alerts = self.db.query(SecurityAlert).filter(
                SecurityAlert.resolved_at.isnot(None),
                SecurityAlert.detected_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            avg_response_time = 0.0
            if resolved_alerts:
                total_response_time = sum([
                    (alert.resolved_at - alert.detected_at).total_seconds()
                    for alert in resolved_alerts
                ])
                avg_response_time = total_response_time / len(resolved_alerts) / 3600  # Convert to hours
            
            # Get top threat types
            top_threats = await self._get_top_threat_types()
            
            # Get recent alerts
            recent_alerts = self.db.query(SecurityAlert).order_by(
                SecurityAlert.detected_at.desc()
            ).limit(10).all()
            
            recent_alert_responses = [
                AlertResponse(
                    id=alert.id,
                    alert_id=alert.alert_id,
                    severity=alert.severity,
                    threat_type=alert.threat_type,
                    status=alert.status,
                    description=alert.description,
                    risk_score=alert.risk_score,
                    detected_at=alert.detected_at,
                    acknowledged_at=alert.acknowledged_at,
                    resolved_at=alert.resolved_at
                )
                for alert in recent_alerts
            ]
            
            return SecurityDashboard(
                active_alerts=active_alerts,
                critical_alerts=critical_alerts,
                threats_blocked_today=threats_blocked,
                average_response_time=round(avg_response_time, 2),
                top_threat_types=top_threats,
                recent_alerts=recent_alert_responses
            )
            
        except Exception as e:
            logger.error(f"Failed to get security dashboard: {e}")
            raise
    
    async def acknowledge_alert(self, alert_id: str, assigned_to: str) -> bool:
        """Acknowledge a security alert."""
        try:
            alert = self.db.query(SecurityAlert).filter(SecurityAlert.alert_id == alert_id).first()
            if alert:
                alert.status = AlertStatus.INVESTIGATING.value
                alert.acknowledged_at = datetime.utcnow()
                alert.assigned_to = assigned_to
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to acknowledge alert: {e}")
            raise
    
    async def resolve_alert(self, alert_id: str, resolution_notes: str, is_false_positive: bool = False) -> bool:
        """Resolve a security alert."""
        try:
            alert = self.db.query(SecurityAlert).filter(SecurityAlert.alert_id == alert_id).first()
            if alert:
                alert.status = AlertStatus.FALSE_POSITIVE.value if is_false_positive else AlertStatus.RESOLVED.value
                alert.resolved_at = datetime.utcnow()
                alert.resolution_notes = resolution_notes
                alert.false_positive = is_false_positive
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to resolve alert: {e}")
            raise
    
    async def _handle_critical_alert(self, alert: SecurityAlert):
        """Handle critical security alerts."""
        try:
            # Immediate email notification
            await self._send_email_alert(alert, urgent=True)
            
            # SMS notification (if configured)
            await self._send_sms_alert(alert)
            
            # Auto-escalate to security team
            await self._escalate_to_security_team(alert)
            
            # Log to security event system
            await self._log_security_event(alert, "CRITICAL_ALERT_CREATED")
            
        except Exception as e:
            logger.error(f"Failed to handle critical alert: {e}")
    
    async def _handle_high_alert(self, alert: SecurityAlert):
        """Handle high priority security alerts."""
        try:
            # Email notification
            await self._send_email_alert(alert)
            
            # Log to security event system
            await self._log_security_event(alert, "HIGH_ALERT_CREATED")
            
        except Exception as e:
            logger.error(f"Failed to handle high alert: {e}")
    
    async def _handle_medium_alert(self, alert: SecurityAlert):
        """Handle medium priority security alerts."""
        try:
            # Queue for review
            await self._queue_for_review(alert)
            
            # Log to security event system
            await self._log_security_event(alert, "MEDIUM_ALERT_CREATED")
            
        except Exception as e:
            logger.error(f"Failed to handle medium alert: {e}")
    
    async def _handle_low_alert(self, alert: SecurityAlert):
        """Handle low priority security alerts."""
        try:
            # Just log for now
            await self._log_security_event(alert, "LOW_ALERT_CREATED")
            
        except Exception as e:
            logger.error(f"Failed to handle low alert: {e}")
    
    async def _send_email_alert(self, alert: SecurityAlert, urgent: bool = False):
        """Send email notification for security alert."""
        try:
            if not settings.smtp.enabled:
                logger.warning("SMTP not configured, skipping email alert")
                return
            
            subject = f"{'🚨 URGENT' if urgent else '⚠️'} Security Alert: {alert.threat_type} - {alert.severity.upper()}"
            
            body = f"""
            Security Alert Details:
            
            Alert ID: {alert.alert_id}
            Severity: {alert.severity.upper()}
            Threat Type: {alert.threat_type}
            Detected: {alert.detected_at}
            Source IP: {alert.source_ip or 'Unknown'}
            Target: {alert.target_endpoint or 'Unknown'}
            
            Description:
            {alert.description}
            
            Risk Score: {alert.risk_score}/10
            
            Please investigate immediately.
            
            SoliVolt Security Team
            """
            
            # Send to security team email
            security_emails = ["security@company.com", "admin@company.com"]  # Configure these
            for email in security_emails:
                await self._send_email(email, subject, body)
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using SMTP."""
        try:
            msg = MimeMultipart()
            msg['From'] = settings.smtp.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(settings.smtp.host, settings.smtp.port)
            if settings.smtp.use_tls:
                server.starttls()
            if settings.smtp.username:
                server.login(settings.smtp.username, settings.smtp.password)
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    async def _send_sms_alert(self, alert: SecurityAlert):
        """Send SMS alert for critical incidents."""
        # Implement SMS service integration (Twilio, AWS SNS, etc.)
        logger.info(f"SMS alert would be sent for critical alert: {alert.alert_id}")
    
    async def _escalate_to_security_team(self, alert: SecurityAlert):
        """Escalate critical alerts to security team."""
        # Implement escalation logic (PagerDuty, Slack, etc.)
        logger.info(f"Alert {alert.alert_id} escalated to security team")
    
    async def _queue_for_review(self, alert: SecurityAlert):
        """Queue alert for manual review."""
        redis_client.lpush("security_review_queue", json.dumps({
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "queued_at": datetime.utcnow().isoformat()
        }))
    
    async def _log_security_event(self, alert: SecurityAlert, event_type: str):
        """Log security event for audit."""
        event = {
            "event_type": event_type,
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "threat_type": alert.threat_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": alert.source_ip,
            "target": alert.target_endpoint
        }
        
        redis_client.lpush("security_audit_log", json.dumps(event))
        redis_client.expire("security_audit_log", 86400 * 90)  # Keep for 90 days
    
    async def _store_alert_in_redis(self, alert: SecurityAlert):
        """Store alert in Redis for real-time monitoring."""
        alert_data = {
            "id": alert.id,
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "threat_type": alert.threat_type,
            "status": alert.status,
            "detected_at": alert.detected_at.isoformat(),
            "risk_score": alert.risk_score
        }
        
        # Store in active alerts
        redis_client.hset("active_alerts", alert.alert_id, json.dumps(alert_data))
        
        # Store in severity-based lists
        redis_client.lpush(f"alerts_{alert.severity}", json.dumps(alert_data))
        redis_client.expire(f"alerts_{alert.severity}", 86400)  # Keep for 24 hours
    
    async def _get_top_threat_types(self) -> List[Dict[str, Any]]:
        """Get top threat types from the last 30 days."""
        try:
            since_date = datetime.utcnow() - timedelta(days=30)
            
            # This would be more complex with actual database queries
            # For now, return sample data
            return [
                {"threat_type": "brute_force", "count": 45, "percentage": 35.0},
                {"threat_type": "sql_injection", "count": 28, "percentage": 22.0},
                {"threat_type": "ddos", "count": 25, "percentage": 19.0},
                {"threat_type": "xss", "count": 18, "percentage": 14.0},
                {"threat_type": "suspicious_activity", "count": 13, "percentage": 10.0}
            ]
            
        except Exception as e:
            logger.error(f"Failed to get top threat types: {e}")
            return []


# Background monitoring tasks
class SecurityMonitoringTasks:
    """Background tasks for security monitoring."""
    
    def __init__(self, monitoring_service: SecurityMonitoringService):
        self.monitoring_service = monitoring_service
    
    async def monitor_failed_logins(self):
        """Monitor for suspicious login patterns."""
        try:
            # Check Redis for failed login attempts
            failed_logins = redis_client.hgetall("failed_logins")
            
            for ip, count in failed_logins.items():
                if int(count) > 10:  # More than 10 failed attempts
                    await self.monitoring_service.create_alert(AlertCreate(
                        severity=AlertSeverity.MEDIUM,
                        threat_type=ThreatType.BRUTE_FORCE,
                        source_ip=ip,
                        description=f"Suspicious login activity: {count} failed attempts from {ip}",
                        risk_score=6.0
                    ))
                    
                    # Clear the counter after alerting
                    redis_client.hdel("failed_logins", ip)
                    
        except Exception as e:
            logger.error(f"Failed to monitor failed logins: {e}")
    
    async def monitor_api_abuse(self):
        """Monitor for API abuse patterns."""
        try:
            # Check for unusual API usage patterns
            # This would analyze request patterns, endpoints hit, etc.
            pass
            
        except Exception as e:
            logger.error(f"Failed to monitor API abuse: {e}")
    
    async def monitor_system_health(self):
        """Monitor system health and security metrics."""
        try:
            # Check system resources, unusual processes, etc.
            # This would integrate with system monitoring tools
            pass
            
        except Exception as e:
            logger.error(f"Failed to monitor system health: {e}")
    
    async def run_security_scans(self):
        """Run automated security scans."""
        try:
            # This would run various security scans:
            # - Port scans
            # - Vulnerability scans
            # - Configuration audits
            # - Log analysis
            pass
            
        except Exception as e:
            logger.error(f"Failed to run security scans: {e}")


# Automated threat response
class AutomatedThreatResponse:
    """Automated responses to security threats."""
    
    def __init__(self):
        self.response_rules = {
            ThreatType.SQL_INJECTION: self._block_ip_temporarily,
            ThreatType.XSS: self._block_ip_temporarily,
            ThreatType.DDOS: self._activate_ddos_protection,
            ThreatType.BRUTE_FORCE: self._implement_progressive_delay,
        }
    
    async def respond_to_threat(self, alert: SecurityAlert):
        """Automatically respond to security threats."""
        try:
            threat_type = ThreatType(alert.threat_type)
            if threat_type in self.response_rules:
                await self.response_rules[threat_type](alert)
                
        except Exception as e:
            logger.error(f"Failed to respond to threat: {e}")
    
    async def _block_ip_temporarily(self, alert: SecurityAlert):
        """Temporarily block suspicious IP address."""
        if alert.source_ip:
            # Add to blocked IPs in Redis
            redis_client.setex(f"blocked_ip:{alert.source_ip}", 3600, "auto_blocked")
            logger.info(f"Temporarily blocked IP {alert.source_ip} due to {alert.threat_type}")
    
    async def _activate_ddos_protection(self, alert: SecurityAlert):
        """Activate DDoS protection measures."""
        # This would activate rate limiting, captcha, etc.
        logger.info("DDoS protection activated")
    
    async def _implement_progressive_delay(self, alert: SecurityAlert):
        """Implement progressive delays for brute force attempts."""
        if alert.source_ip:
            # Increase delay for subsequent requests from this IP
            delay_key = f"progressive_delay:{alert.source_ip}"
            current_delay = redis_client.get(delay_key) or "0"
            new_delay = min(int(current_delay) + 5, 60)  # Max 60 second delay
            redis_client.setex(delay_key, 3600, str(new_delay))
            logger.info(f"Progressive delay of {new_delay}s set for IP {alert.source_ip}")
