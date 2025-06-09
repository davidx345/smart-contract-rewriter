from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Union
import os

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env
    )
    
    PROJECT_NAME: str = "Smart Contract Rewriter"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered smart contract analysis and optimization"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@db:5432/smart_contract_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password123"
    POSTGRES_DB: str = "smart_contract_rewriter"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Web3
    WEB3_PROVIDER_URL: str = "https://mainnet.infura.io/v3/your-project-id"
    ETHEREUM_NETWORK: str = "mainnet"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application Configuration
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_PORT: str = "3000"
    APP_NAME: str = "Smart Contract Rewriter"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_EXTENSIONS: str = ".sol,.txt"
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 5
    ETHEREUM_NETWORK: str = "mainnet"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080"
    APP_NAME: str = "Smart Contract Rewriter"
    APP_VERSION: str = "1.0.0"
    DEBUG: str = "True"
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE: str = "10485760"
    ALLOWED_EXTENSIONS: str = ".sol,.txt"
    RATE_LIMIT_PER_MINUTE: str = "30"
    RATE_LIMIT_BURST: str = "5"

settings = Settings()
