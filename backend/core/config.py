"""
Configuration settings for MindWise backend.
Uses environment variables for sensitive data.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    user: str
    password: str
    host: str
    port: str
    dbname: str

    # Google Gemini API
    GEMINI_API_KEY: str

    # CORS (comma-separated origins)
    ALLOWED_ORIGINS: str

    # Application
    APP_NAME: str = "MindWise"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
