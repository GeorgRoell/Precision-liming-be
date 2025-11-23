from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # NextFarming API credentials (from .env)
    NEXTFARMING_CLIENT_ID: str = ""
    NEXTFARMING_CLIENT_SECRET: str = ""
    NEXTFARMING_REDIRECT_URI: str = "http://localhost:8080/callback"
    NEXTFARMING_AUTH_BASE: str = "https://test-account-service.nextfarming.dev/realms/account-service/protocol/openid-connect"
    NEXTFARMING_API_BASE: str = "https://test-farmmanagement.nextfarming.dev/v2"

    # Server security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated ALLOWED_ORIGINS to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
