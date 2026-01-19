"""
Configuration settings for MindWise backend.
Uses environment variables for sensitive data.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # Google Gemini API
    GEMINI_API_KEY: str
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Application
    APP_NAME: str = "MindWise"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
