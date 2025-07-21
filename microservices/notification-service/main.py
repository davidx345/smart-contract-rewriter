"""
Notification Microservice
Handles email notifications, webhooks, and real-time updates
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import smtplib
import asyncio
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@solivolt.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SoliVolt Platform")

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt Notification Service",
    description="Notification and communication microservice",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class EmailNotification(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    body_type: str = "text"  # text or html
    template: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None

class WelcomeEmailRequest(BaseModel):
    to_email: EmailStr
    full_name: str

class PasswordResetEmailRequest(BaseModel):
    to_email: EmailStr
    reset_token: str
    full_name: str

class ContractAnalysisNotification(BaseModel):
    to_email: EmailStr
    full_name: str
    contract_name: str
    analysis_summary: str
    vulnerabilities_found: int

class NotificationResponse(BaseModel):
    success: bool
    message: str
    notification_id: Optional[str] = None

class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self):
        self.smtp_configured = bool(SMTP_USERNAME and SMTP_PASSWORD)
    
    async def send_email(self, to_email: str, subject: str, body: str, body_type: str = "text") -> bool:
        """Send email notification"""
        if not self.smtp_configured:
            print(f"Email would be sent to {to_email}: {subject}")
            return True  # Simulate success in development
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            if body_type == "html":
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            await asyncio.to_thread(self._send_smtp_email, msg, to_email)
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart, to_email: str):
        """Send email via SMTP"""
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, to_email, text)
        server.quit()
    
    def create_welcome_email(self, full_name: str) -> tuple[str, str]:
        """Create welcome email content"""
        subject = f"Welcome to SoliVolt, {full_name}!"
        
        body = f"""
        Dear {full_name},

        Welcome to SoliVolt - the enterprise smart contract analysis platform!

        We're excited to have you on board. Here's what you can do with your new account:

        🔍 Analyze Smart Contracts: Upload your Solidity contracts for comprehensive security analysis
        🤖 AI-Powered Insights: Get intelligent recommendations from our advanced AI models
        ⚡ Gas Optimization: Discover ways to reduce gas costs and improve efficiency
        📊 Track History: Monitor all your contract analyses and improvements over time

        Getting Started:
        1. Log in to your dashboard: https://solivolt.com/dashboard
        2. Upload your first smart contract for analysis
        3. Review the AI-generated security report
        4. Implement the recommended improvements

        If you have any questions or need assistance, don't hesitate to reach out to our support team.

        Best regards,
        The SoliVolt Team

        ---
        This email was sent to {full_name}. If you didn't create this account, please ignore this email.
        """
        
        return subject, body
    
    def create_password_reset_email(self, full_name: str, reset_token: str) -> tuple[str, str]:
        """Create password reset email content"""
        subject = "Reset Your SoliVolt Password"
        
        reset_url = f"https://solivolt.com/reset-password?token={reset_token}"
        
        body = f"""
        Dear {full_name},

        We received a request to reset your SoliVolt account password.

        To reset your password, click the link below:
        {reset_url}

        This link will expire in 1 hour for security reasons.

        If you didn't request this password reset, please ignore this email. Your password will remain unchanged.

        For security reasons, this link can only be used once. If you need to reset your password again, please request a new reset link.

        Best regards,
        The SoliVolt Team

        ---
        If you're having trouble with the link above, copy and paste it into your browser's address bar.
        """
        
        return subject, body
    
    def create_analysis_notification_email(self, full_name: str, contract_name: str, 
                                         analysis_summary: str, vulnerabilities_found: int) -> tuple[str, str]:
        """Create contract analysis notification email"""
        subject = f"Contract Analysis Complete: {contract_name}"
        
        vulnerability_text = "No vulnerabilities found! 🎉" if vulnerabilities_found == 0 else f"{vulnerabilities_found} potential issues identified"
        
        body = f"""
        Dear {full_name},

        Your smart contract analysis for "{contract_name}" has been completed!

        Analysis Summary:
        {analysis_summary}

        Security Assessment: {vulnerability_text}

        You can view the full detailed report and recommendations in your SoliVolt dashboard:
        https://solivolt.com/dashboard

        Key Benefits of This Analysis:
        • Security vulnerability detection
        • Gas optimization recommendations  
        • Code quality improvements
        • Best practice suggestions

        Next Steps:
        1. Review the detailed analysis report
        2. Implement the recommended security fixes
        3. Optimize gas usage based on our suggestions
        4. Consider additional testing based on our recommendations

        Thank you for using SoliVolt for your smart contract security needs!

        Best regards,
        The SoliVolt Team
        """
        
        return subject, body

# Initialize services
email_service = EmailService()

# Background task storage (in production, use a proper queue)
notification_queue = []

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "email_configured": email_service.smtp_configured
    }

@app.post("/api/v1/notifications/email", response_model=NotificationResponse)
async def send_email_notification(
    notification: EmailNotification,
    background_tasks: BackgroundTasks
):
    """Send generic email notification"""
    
    # Add to background tasks
    background_tasks.add_task(
        email_service.send_email,
        notification.to_email,
        notification.subject,
        notification.body,
        notification.body_type
    )
    
    return NotificationResponse(
        success=True,
        message="Email notification queued for delivery",
        notification_id=f"email_{datetime.now().timestamp()}"
    )

@app.post("/api/v1/notifications/welcome", response_model=NotificationResponse)
async def send_welcome_email(
    request: WelcomeEmailRequest,
    background_tasks: BackgroundTasks
):
    """Send welcome email to new users"""
    
    subject, body = email_service.create_welcome_email(request.full_name)
    
    background_tasks.add_task(
        email_service.send_email,
        request.to_email,
        subject,
        body
    )
    
    return NotificationResponse(
        success=True,
        message="Welcome email queued for delivery",
        notification_id=f"welcome_{datetime.now().timestamp()}"
    )

@app.post("/api/v1/notifications/password-reset", response_model=NotificationResponse)
async def send_password_reset_email(
    request: PasswordResetEmailRequest,
    background_tasks: BackgroundTasks
):
    """Send password reset email"""
    
    subject, body = email_service.create_password_reset_email(
        request.full_name, 
        request.reset_token
    )
    
    background_tasks.add_task(
        email_service.send_email,
        request.to_email,
        subject,
        body
    )
    
    return NotificationResponse(
        success=True,
        message="Password reset email queued for delivery",
        notification_id=f"reset_{datetime.now().timestamp()}"
    )

@app.post("/api/v1/notifications/analysis-complete", response_model=NotificationResponse)
async def send_analysis_notification(
    request: ContractAnalysisNotification,
    background_tasks: BackgroundTasks
):
    """Send contract analysis completion notification"""
    
    subject, body = email_service.create_analysis_notification_email(
        request.full_name,
        request.contract_name,
        request.analysis_summary,
        request.vulnerabilities_found
    )
    
    background_tasks.add_task(
        email_service.send_email,
        request.to_email,
        subject,
        body
    )
    
    return NotificationResponse(
        success=True,
        message="Analysis notification queued for delivery",
        notification_id=f"analysis_{datetime.now().timestamp()}"
    )

@app.get("/api/v1/notifications/status")
async def get_notification_status():
    """Get notification service status"""
    return {
        "service": "notification-service",
        "email_service": {
            "configured": email_service.smtp_configured,
            "host": SMTP_HOST,
            "port": SMTP_PORT,
            "from_email": EMAIL_FROM
        },
        "queue_length": len(notification_queue),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SoliVolt Notification Service",
        "version": "1.0.0",
        "endpoints": {
            "email": "/api/v1/notifications/email",
            "welcome": "/api/v1/notifications/welcome",
            "password_reset": "/api/v1/notifications/password-reset",
            "analysis_complete": "/api/v1/notifications/analysis-complete",
            "status": "/api/v1/notifications/status",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
