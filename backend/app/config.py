"""
Configuration settings for the application
Loads environment variables and provides app-wide settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # Capgemini AI
    CAPGEMINI_API_KEY: str
    CAPGEMINI_API_ENDPOINT: str
    CAPGEMINI_MODEL: str
    AI_CALLS_PER_WEEK: int = 100
    AI_CALLS_RESET_DAY: str = "monday"
    
    # Application
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG_MODE: bool = True
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # File Paths
    INITIAL_DATA_PATH: str = "./data/initial_data.csv"
    EXPORT_TEMP_DIR: str = "./exports"
    
    # Computed properties
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Create export directory if it doesn't exist
os.makedirs(settings.EXPORT_TEMP_DIR, exist_ok=True)