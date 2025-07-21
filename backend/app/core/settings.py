"""
Enhanced settings for the SoliVolt platform with clean architecture configuration.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, Field, validator
import secrets
import os
from enum import Enum


class EnvironmentType(str, Enum):
    """Environment types for the application."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="solivolt", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="postgres", env="DB_PASSWORD")
    
    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # SSL settings
    ssl_mode: str = Field(default="prefer", env="DB_SSL_MODE")
    
    @property
    def connection_string(self) -> str:
        """Get the database connection string."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )
    
    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # Connection pool settings
    max_connections: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    
    @property
    def connection_string(self) -> str:
        """Get the Redis connection string."""
        protocol = "rediss" if self.ssl else "redis"
        auth_part = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth_part}{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password settings
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_numbers: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_special: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    
    # API Key settings
    api_key_length: int = Field(default=32, env="API_KEY_LENGTH")
    api_key_prefix: str = Field(default="sk_", env="API_KEY_PREFIX")
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_RPM")
    rate_limit_burst: int = Field(default=100, env="RATE_LIMIT_BURST")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class AISettings(BaseSettings):
    """AI service configuration settings."""
    # Gemini API
    gemini_api_key: str = Field(env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-pro", env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.1, env="GEMINI_TEMPERATURE")
    gemini_max_tokens: int = Field(default=1000, env="GEMINI_MAX_TOKENS")
    gemini_timeout: int = Field(default=30, env="GEMINI_TIMEOUT")
    
    # Analysis settings
    max_contract_size: int = Field(default=100000, env="MAX_CONTRACT_SIZE")  # bytes
    analysis_timeout: int = Field(default=300, env="ANALYSIS_TIMEOUT")  # seconds
    max_concurrent_analyses: int = Field(default=5, env="MAX_CONCURRENT_ANALYSES")
    
    # Cache settings
    cache_analysis_results: bool = Field(default=True, env="CACHE_ANALYSIS_RESULTS")
    analysis_cache_ttl: int = Field(default=3600, env="ANALYSIS_CACHE_TTL")  # seconds
    
    class Config:
        env_prefix = "AI_"


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration settings."""
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    
    # Health checks
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Tracing
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    
    class Config:
        env_prefix = "MONITORING_"


class NotificationSettings(BaseSettings):
    """Notification service configuration settings."""
    # Email settings
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Webhook settings
    webhook_timeout: int = Field(default=30, env="WEBHOOK_TIMEOUT")
    webhook_retry_attempts: int = Field(default=3, env="WEBHOOK_RETRY_ATTEMPTS")
    
    # Notification templates
    email_templates_dir: str = Field(default="templates/email", env="EMAIL_TEMPLATES_DIR")
    
    class Config:
        env_prefix = "NOTIFICATION_"


class Settings(BaseSettings):
    """Main application settings."""
    # Application
    app_name: str = Field(default="SoliVolt", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ai: AISettings = Field(default_factory=AISettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    
    # Feature flags
    enable_subscriptions: bool = Field(default=True, env="ENABLE_SUBSCRIPTIONS")
    enable_teams: bool = Field(default=True, env="ENABLE_TEAMS")
    enable_webhooks: bool = Field(default=True, env="ENABLE_WEBHOOKS")
    enable_api_keys: bool = Field(default=True, env="ENABLE_API_KEYS")
    enable_audit_logs: bool = Field(default=True, env="ENABLE_AUDIT_LOGS")
    
    @validator('environment', pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return EnvironmentType(v.lower())
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == EnvironmentType.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == EnvironmentType.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == EnvironmentType.TESTING
    
    def get_database_url(self, async_driver: bool = False) -> str:
        """Get the database URL with optional async driver."""
        driver = "postgresql+asyncpg" if async_driver else "postgresql"
        return (
            f"{driver}://{self.database.user}:{self.database.password}@"
            f"{self.database.host}:{self.database.port}/{self.database.name}"
        )
    
    def model_dump_sensitive(self) -> Dict[str, Any]:
        """Get settings dict with sensitive values masked."""
        data = self.dict()
        
        # Mask sensitive fields
        sensitive_fields = [
            'secret_key', 'password', 'api_key', 'smtp_password'
        ]
        
        def mask_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(sensitive in key.lower() for sensitive in sensitive_fields):
                        obj[key] = "***MASKED***"
                    else:
                        mask_recursive(value, current_path)
            elif isinstance(obj, list):
                for item in obj:
                    mask_recursive(item, path)
        
        mask_recursive(data)
        return data
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
