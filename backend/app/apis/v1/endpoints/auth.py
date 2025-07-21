"""
Authentication API Endpoints
Enterprise-grade authentication with comprehensive security features
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import secrets

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.core.dependencies import (
    get_current_user, get_admin_user, get_current_user_optional,
    check_rate_limit
)
from app.schemas.auth_db_schemas import User, UserSession, AuditLog, SecurityEvent
from app.models.auth_models import (
    UserRegistration, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordReset, PasswordResetConfirm, EmailVerification, ChangePassword,
    UserProfile, AuthResponse, UserStats, AuditAction, UserRole, UserStatus
)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# === Public Endpoints ===

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Register a new user
    
    - **email**: Valid email address (will be verified)
    - **password**: Strong password (8+ chars, mixed case, numbers, symbols)
    - **full_name**: User's full name
    - **company**: Optional company name
    - **linkedin_profile**: Optional LinkedIn profile URL
    
    Returns user data and sends verification email.
    """
    try:
        user = auth_service.register_user(db, user_data, request)
        
        # Send welcome email in background
        background_tasks.add_task(
            send_welcome_email, user.email, user.full_name
        )
        
        return AuthResponse(
            success=True,
            message="Registration successful. Please check your email for verification.",
            data={"user_id": user.id, "email": user.email}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Extend session duration if true
    
    Returns access token, refresh token, and user data.
    """
    try:
        token = auth_service.login_user(db, login_data, request)
        
        # Set secure HTTP-only cookie for refresh token
        if login_data.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=token.refresh_token,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                secure=True,
                samesite="strict"
            )
        
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and user data.
    """
    try:
        token = auth_service.refresh_access_token(db, token_data.refresh_token)
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=AuthResponse)
async def logout_user(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session
    
    Requires valid access token in Authorization header.
    """
    try:
        # Get refresh token from request body or cookie
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            # Try to get from request if provided
            body = await request.json() if request.headers.get("content-type") == "application/json" else {}
            refresh_token = body.get("refresh_token")
        
        if refresh_token:
            auth_service.logout_user(db, refresh_token, request)
        
        # Revoke access token
        auth_service.revoke_token(credentials.credentials)
        
        # Clear refresh token cookie
        response.delete_cookie("refresh_token")
        
        return AuthResponse(
            success=True,
            message="Logout successful"
        )
    except Exception as e:
        return AuthResponse(
            success=True,
            message="Logout completed"  # Always return success for security
        )


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(
    verification_data: EmailVerification,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify user email address
    
    - **token**: Email verification token from email
    """
    user = db.query(User).filter(
        User.email_verification_token == verification_data.token,
        User.email_verification_expires > datetime.now(timezone.utc)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user status
    user.email_verified = True
    user.status = UserStatus.ACTIVE
    user.email_verification_token = None
    user.email_verification_expires = None
    
    # Log verification
    auth_service._create_audit_log(
        db, user.id, AuditAction.EMAIL_VERIFY, request
    )
    
    db.commit()
    
    return AuthResponse(
        success=True,
        message="Email verified successfully. Your account is now active."
    )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(
    reset_data: PasswordReset,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Request password reset
    
    - **email**: User's email address
    
    Sends password reset email if user exists.
    """
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if user:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Log password reset request
        auth_service._create_audit_log(
            db, user.id, AuditAction.PASSWORD_RESET, request,
            metadata={"reset_requested": True}
        )
        
        db.commit()
        
        # Send reset email in background
        background_tasks.add_task(
            send_password_reset_email, user.email, reset_token
        )
    
    # Always return success for security (don't reveal if email exists)
    return AuthResponse(
        success=True,
        message="If an account with that email exists, you will receive a password reset link."
    )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token from email
    - **new_password**: New strong password
    """
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token,
        User.password_reset_expires > datetime.now(timezone.utc)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate password strength
    is_valid, errors = auth_service.validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors}
        )
    
    # Update password
    user.password_hash = auth_service.get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.password_changed_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0  # Reset failed attempts
    user.account_locked_until = None  # Unlock account
    
    # Invalidate all user sessions (force re-login)
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True
    ).update({"is_active": False, "ended_at": datetime.now(timezone.utc)})
    
    # Log password change
    auth_service._create_audit_log(
        db, user.id, AuditAction.PASSWORD_CHANGE, request,
        metadata={"method": "reset_token"}
    )
    
    db.commit()
    
    return AuthResponse(
        success=True,
        message="Password reset successful. Please log in with your new password."
    )


# === Protected Endpoints ===

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Requires authentication. Returns detailed user profile.
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile
    
    - **full_name**: Updated full name
    - **company**: Updated company name
    - **linkedin_profile**: Updated LinkedIn profile URL
    - **bio**: User bio/description
    - **timezone**: User timezone
    - **notification_preferences**: Email notification settings
    """
    # Update user fields
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Log profile update
    auth_service._create_audit_log(
        db, current_user.id, AuditAction.PROFILE_UPDATE, request,
        metadata={"updated_fields": list(update_data.keys())}
    )
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)


@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    password_data: ChangePassword,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    - **current_password**: Current password for verification
    - **new_password**: New strong password
    
    Requires authentication and current password verification.
    """
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, errors = auth_service.validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors}
        )
    
    # Update password
    current_user.password_hash = auth_service.get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    
    # Log password change
    auth_service._create_audit_log(
        db, current_user.id, AuditAction.PASSWORD_CHANGE, request,
        metadata={"method": "user_initiated"}
    )
    
    db.commit()
    
    return AuthResponse(
        success=True,
        message="Password changed successfully"
    )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics and usage analytics
    
    Returns comprehensive usage statistics for the current user.
    """
    # Calculate statistics
    most_used_features = ["contract_analysis", "code_generation"]  # Placeholder
    
    stats = UserStats(
        total_contracts_analyzed=current_user.contracts_analyzed,
        total_contracts_generated=current_user.contracts_generated,
        total_api_calls=current_user.api_calls_total,
        monthly_api_calls=current_user.api_calls_this_month,
        contracts_this_week=0,  # Calculate from recent activity
        average_analysis_time=2.5,  # Calculate from audit logs
        most_used_features=most_used_features,
        registration_date=current_user.created_at,
        last_activity=current_user.last_login
    )
    
    return stats


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's active sessions
    
    Returns list of active sessions across all devices.
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    return [
        {
            "id": session.id,
            "device_info": session.device_info,
            "ip_address": session.ip_address,
            "location": session.geolocation,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "is_current": False  # TODO: Detect current session
        }
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", response_model=AuthResponse)
async def revoke_session(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific user session
    
    - **session_id**: ID of session to revoke
    """
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Revoke session
    session.is_active = False
    session.ended_at = datetime.now(timezone.utc)
    
    # Log session revocation
    auth_service._create_audit_log(
        db, current_user.id, AuditAction.LOGOUT, request,
        metadata={"session_id": session_id, "method": "user_revoked"}
    )
    
    db.commit()
    
    return AuthResponse(
        success=True,
        message="Session revoked successfully"
    )


# === Admin Endpoints ===

@router.get("/admin/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    
    - **skip**: Number of users to skip
    - **limit**: Maximum number of users to return
    - **role**: Filter by user role
    - **status**: Filter by user status
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role.value)
    if status:
        query = query.filter(User.status == status.value)
    
    users = query.offset(skip).limit(limit).all()
    return [UserResponse.from_orm(user) for user in users]


@router.put("/admin/users/{user_id}/role", response_model=AuthResponse)
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user role (Admin only)
    
    - **user_id**: ID of user to update
    - **new_role**: New role to assign
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_role = user.role
    user.role = new_role.value
    user.updated_at = datetime.now(timezone.utc)
    
    # Log role change
    auth_service._create_audit_log(
        db, admin_user.id, AuditAction.ROLE_CHANGE, request,
        metadata={
            "target_user_id": user_id,
            "old_role": old_role,
            "new_role": new_role.value
        }
    )
    
    db.commit()
    
    return AuthResponse(
        success=True,
        message=f"User role updated to {new_role.value}"
    )


# === Background Tasks ===

async def send_welcome_email(email: str, name: str):
    """Send welcome email to new user"""
    print(f"Sending welcome email to {email} (Name: {name})")
    # Implement actual email sending


async def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    print(f"Sending password reset email to {email} with token: {token}")
    # Implement actual email sending
