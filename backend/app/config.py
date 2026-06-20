from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/elderly_canteen"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    SMS_TEST_CODE: str = "123456"
    SMS_EXPIRE_MINUTES: int = 5
    VOICE_API_KEY: Optional[str] = None
    VOICE_SECRET_KEY: Optional[str] = None
    VOICE_APP_ID: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
