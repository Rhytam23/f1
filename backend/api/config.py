"""API and Environment Configuration for RacePulse."""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    WS_BASE_URL: str = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws/race")
    DATA_CACHE_DIR: str = os.getenv("DATA_CACHE_DIR", "data/cache")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://f1-o7v4.onrender.com",
    ]


settings = Settings()
