from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import List, Union
import os

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env
    )
    
    # Basic Project Info
    PROJECT_NAME: str = "SoliVolt"
    API_V1_STR: str = "/api/v1"
    VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DESCRIPTION: str = "AI-powered smart contract analysis and optimization"
    
    # Database - Only need DATABASE_URL since it contains everything
    DATABASE_URL: str = Field(..., description="Full PostgreSQL connection URL")
    
    # Gemini API
    GEMINI_API_KEY: str = Field(..., description="Gemini API key for AI processing")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")
    
    # Web3
    WEB3_PROVIDER_URL: str = Field(default="https://mainnet.infura.io/v3/65f7a81362074c3cb170e6311d2438cf")
    ETHEREUM_NETWORK: str = Field(default="mainnet")
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000")
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins from environment variable"""
        if self.ALLOWED_ORIGINS:
            origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]
            return origins
        # Fallback for development
        return ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]
    
    # Security & Authentication
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    
    # Password Requirements
    MIN_PASSWORD_LENGTH: int = Field(default=8)
    REQUIRE_UPPERCASE: bool = Field(default=True)
    REQUIRE_LOWERCASE: bool = Field(default=True)
    REQUIRE_NUMBERS: bool = Field(default=True)
    REQUIRE_SYMBOLS: bool = Field(default=True)
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    ACCOUNT_LOCKOUT_DURATION: int = Field(default=300)  # 5 minutes in seconds
    SESSION_TIMEOUT_MINUTES: int = Field(default=60)
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", description="Google OAuth client secret")
    GITHUB_CLIENT_ID: str = Field(default="", description="GitHub OAuth client ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", description="GitHub OAuth client secret")
    LINKEDIN_CLIENT_ID: str = Field(default="", description="LinkedIn OAuth client ID")
    LINKEDIN_CLIENT_SECRET: str = Field(default="", description="LinkedIn OAuth client secret")
    
    # Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    EMAIL_FROM: str = Field(default="noreply@solivolt.com")
    EMAIL_FROM_NAME: str = Field(default="SoliVolt Platform")
    
    # Redis Configuration (for caching, sessions, rate limiting)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_TTL: int = Field(default=3600)  # 1 hour default cache TTL
    
    # Application Configuration
    API_BASE_URL: str = Field(default="http://localhost:8000")
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    APP_NAME: str = Field(default="SoliVolt")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(default=10485760)  # 10MB in bytes
    ALLOWED_EXTENSIONS: str = Field(default=".sol,.txt")
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(default=30)
    RATE_LIMIT_BURST: int = Field(default=5)

settings = Settings()
