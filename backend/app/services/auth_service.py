"""
Enterprise Authentication Service
JWT-based authentication with advanced security features
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import json
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib

from app.core.config import settings
from app.schemas.auth_db_schemas import User, UserSession, AuditLog, SecurityEvent, RateLimitEntry
from app.models.auth_models import (
    UserRegistration, UserLogin, UserResponse, Token, TokenData,
    UserRole, UserStatus, AuditAction
)


class SecurityConfig:
    """Security configuration and constants"""
    
    # Password policy
    MIN_PASSWORD_LENGTH = 8
    MAX_FAILED_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    
    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    EMAIL_VERIFICATION_EXPIRE_HOURS = 24
    PASSWORD_RESET_EXPIRE_HOURS = 1
    
    # Rate limiting
    LOGIN_RATE_LIMIT = 5  # attempts per minute
    API_RATE_LIMIT_FREE = 100  # requests per hour
    API_RATE_LIMIT_PREMIUM = 1000  # requests per hour
    API_RATE_LIMIT_ENTERPRISE = 10000  # requests per hour
    
    # Security thresholds
    SUSPICIOUS_LOGIN_THRESHOLD = 3  # failed attempts from same IP
    GEOLOCATION_CHANGE_THRESHOLD = 1000  # km difference for flagging


class AuthenticationService:
    """
    Enterprise-grade authentication service
    Handles user registration, login, JWT tokens, and security features
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL) if hasattr(settings, 'REDIS_URL') else None
        self.security_config = SecurityConfig()
    
    # === Password Management ===
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against security policy
        Returns (is_valid, error_messages)
        """
        errors = []
        
        if len(password) < self.security_config.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {self.security_config.MIN_PASSWORD_LENGTH} characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    # === JWT Token Management ===
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.security_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.security_config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, expected_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if payload.get("type") != expected_type:
                return None
            
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            expires_at = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            
            if user_id is None:
                return None
            
            token_data = TokenData(
                user_id=user_id,
                email=email,
                role=role,
                expires_at=expires_at
            )
            return token_data
        except jwt.PyJWTError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Add token to blacklist (requires Redis)"""
        if not self.redis_client:
            return False
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp = payload.get("exp")
            if exp:
                ttl = exp - datetime.now(timezone.utc).timestamp()
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{token}", int(ttl), "1")
            return True
        except jwt.PyJWTError:
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        return self.redis_client.exists(f"blacklist:{token}")
    
    # === User Registration ===
    
    def register_user(self, db: Session, user_data: UserRegistration, request: Request) -> UserResponse:
        """
        Register new user with comprehensive validation
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        is_valid, errors = self.validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet security requirements", "errors": errors}
            )
        
        # Create user
        password_hash = self.get_password_hash(user_data.password)
        email_verification_token = secrets.token_urlsafe(32)
        
        db_user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            company=user_data.company,
            linkedin_profile=user_data.linkedin_profile,
            email_verification_token=email_verification_token,
            email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=self.security_config.EMAIL_VERIFICATION_EXPIRE_HOURS),
            role=UserRole.FREE,
            status=UserStatus.PENDING_VERIFICATION
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Send verification email
        self._send_verification_email(db_user.email, email_verification_token)
        
        # Log registration
        self._create_audit_log(
            db, db_user.id, AuditAction.REGISTER, request,
            metadata={"email": user_data.email, "role": UserRole.FREE}
        )
        
        return UserResponse.from_orm(db_user)
    
    # === User Authentication ===
    
    def authenticate_user(self, db: Session, email: str, password: str, request: Request) -> Optional[User]:
        """
        Authenticate user with security checks
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Log failed login attempt
            self._create_audit_log(
                db, None, AuditAction.LOGIN, request,
                success=False, error_message="User not found",
                metadata={"email": email}
            )
            return None
        
        # Check account status
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended"
            )
        
        if user.status == UserStatus.PENDING_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        
        # Check account lockout
        if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to failed login attempts"
            )
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if threshold exceeded
            if user.failed_login_attempts >= self.security_config.MAX_FAILED_ATTEMPTS:
                user.account_locked_until = datetime.now(timezone.utc) + self.security_config.ACCOUNT_LOCKOUT_DURATION
                
                # Create security event
                self._create_security_event(
                    db, "account_locked", "medium", user.id,
                    self._get_client_ip(request),
                    f"Account locked after {user.failed_login_attempts} failed attempts"
                )
            
            db.commit()
            
            # Log failed login
            self._create_audit_log(
                db, user.id, AuditAction.LOGIN, request,
                success=False, error_message="Invalid password",
                metadata={"failed_attempts": user.failed_login_attempts}
            )
            
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.now(timezone.utc)
        user.last_login_ip = self._get_client_ip(request)
        user.last_login_user_agent = request.headers.get("user-agent", "")
        
        db.commit()
        
        # Log successful login
        self._create_audit_log(
            db, user.id, AuditAction.LOGIN, request,
            metadata={"login_method": "password"}
        )
        
        return user
    
    def login_user(self, db: Session, login_data: UserLogin, request: Request) -> Token:
        """
        Complete login process with token generation
        """
        user = self.authenticate_user(db, login_data.email, login_data.password, request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        # Create session record
        session = self._create_user_session(
            db, user.id, refresh_token, request, login_data.remember_me
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.security_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    # === Session Management ===
    
    def _create_user_session(self, db: Session, user_id: int, refresh_token: str, 
                           request: Request, remember_me: bool = False) -> UserSession:
        """Create user session record"""
        session_id = secrets.token_urlsafe(32)
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        expire_delta = timedelta(days=30) if remember_me else timedelta(days=7)
        
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            refresh_token_hash=refresh_token_hash,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.now(timezone.utc) + expire_delta,
            is_remember_me=remember_me,
            device_info=self._extract_device_info(request)
        )
        
        db.add(session)
        db.commit()
        return session
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        token_data = self.verify_token(refresh_token, "refresh")
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify session exists and is active
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = db.query(UserSession).filter(
            UserSession.user_id == token_data.user_id,
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )
        
        # Get user
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        # Create new access token
        new_token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        access_token = self.create_access_token(new_token_data)
        
        # Update session activity
        session.last_activity = datetime.now(timezone.utc)
        db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=self.security_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def logout_user(self, db: Session, refresh_token: str, request: Request) -> bool:
        """Logout user and invalidate session"""
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        session = db.query(UserSession).filter(
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            session.ended_at = datetime.now(timezone.utc)
            
            # Log logout
            self._create_audit_log(
                db, session.user_id, AuditAction.LOGOUT, request,
                metadata={"session_id": session.session_id}
            )
            
            db.commit()
            return True
        
        return False
    
    # === Utility Methods ===
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _extract_device_info(self, request: Request) -> Dict[str, Any]:
        """Extract device information from request"""
        user_agent = request.headers.get("user-agent", "")
        return {
            "user_agent": user_agent,
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
            "fingerprint": hashlib.md5(user_agent.encode()).hexdigest()[:16]
        }
    
    def _create_audit_log(self, db: Session, user_id: Optional[int], action: AuditAction,
                         request: Request, success: bool = True, error_message: str = None,
                         metadata: Dict[str, Any] = None) -> AuditLog:
        """Create audit log entry"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action.value,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        db.add(audit_log)
        db.commit()
        return audit_log
    
    def _create_security_event(self, db: Session, event_type: str, severity: str,
                              user_id: Optional[int], ip_address: str, description: str,
                              metadata: Dict[str, Any] = None) -> SecurityEvent:
        """Create security event entry"""
        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            metadata=metadata
        )
        
        db.add(security_event)
        db.commit()
        return security_event
    
    def _send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification email"""
        # Implementation depends on email service (SendGrid, AWS SES, etc.)
        # For now, just log the token
        print(f"Verification email for {email}: {token}")
        return True


# === Global Authentication Instance ===
auth_service = AuthenticationService()
