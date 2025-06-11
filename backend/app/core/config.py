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
    PROJECT_NAME: str = "Smart Contract Rewriter"
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
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Application Configuration
    API_BASE_URL: str = Field(default="http://localhost:8000")
    APP_NAME: str = Field(default="Smart Contract Rewriter")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(default=10485760)  # 10MB in bytes
    ALLOWED_EXTENSIONS: str = Field(default=".sol,.txt")
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(default=30)
    RATE_LIMIT_BURST: int = Field(default=5)

settings = Settings()
