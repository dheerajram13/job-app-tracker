# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str
    
    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth settings
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except json.JSONDecodeError:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Updated Config syntax for Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

settings = Settings()