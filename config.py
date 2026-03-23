from pydantic_settings import BaseSettings
from functools import lru_cache
 
 
class Settings(BaseSettings):
    # JWT
    JWT_SECRET_KEY: str = "change-this-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
 
    # Gemini
    GEMINI_API_KEY: str = ""
 
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 5       # max requests
    RATE_LIMIT_WINDOW_SECONDS: int = 3600  # per hour
 
    # App
    APP_TITLE: str = "Trade Opportunities API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
 
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
 
 
@lru_cache()
def get_settings() -> Settings:
    return Settings()
 