from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Embedding & Matching System"
    VERSION: str = "1.0.0"
    
    UPSTASH_REDIS_HOST: str = os.getenv("UPSTASH_REDIS_HOST")
    UPSTASH_REDIS_PORT: int = int(os.getenv("UPSTASH_REDIS_PORT", "6379"))
    UPSTASH_REDIS_PASSWORD: str = os.getenv("UPSTASH_REDIS_PASSWORD")
    REDIS_TASKS_QUEUE: str = os.getenv("CELERY_TASK_QUEUE", "celery")
    REDIS_USE_SSL: bool = True
    
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_MIN_CONNECTIONS: int = int(os.getenv("DATABASE_MIN_CONNECTIONS", "1"))
    DATABASE_MAX_CONNECTIONS: int = int(os.getenv("DATABASE_MAX_CONNECTIONS", "10"))
    
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT")
    
    CELERY_BROKER_URL: Optional[str] = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800"))  # 30 minutes
    
    MAX_JOBS_PER_SITE: int = int(os.getenv("MAX_JOBS_PER_SITE", "20"))
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "30"))
    USER_AGENT: str = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use Redis URL for Celery if not explicitly set
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.UPSTASH_REDIS_HOST
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.UPSTASH_REDIS_HOST

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def redis_config(self) -> dict:
        """Return Redis configuration as a dictionary"""
        return {
            "host": self.UPSTASH_REDIS_HOST,
            "password": self.UPSTASH_REDIS_PASSWORD,
            "port": self.UPSTASH_REDIS_PORT,
            "ssl": self.REDIS_USE_SSL,
            "ssl_cert_reqs": None,
            "decode_responses": True
        }
    @property
    def celery_broker_url(self) -> str:
        """Return Redis URL formatted for Celery broker"""
        return f"rediss://:{self.UPSTASH_REDIS_PASSWORD}@{self.UPSTASH_REDIS_HOST}:{self.UPSTASH_REDIS_PORT}/0?ssl_cert_reqs=CERT_NONE"

    @property
    def celery_result_backend_url(self) -> str:
        """Return Redis URL formatted for Celery result backend, we are using the same redis as backend"""
        return f"rediss://:{self.UPSTASH_REDIS_PASSWORD}@{self.UPSTASH_REDIS_HOST}:{self.UPSTASH_REDIS_PORT}/0?ssl_cert_reqs=CERT_REQUIRED"

    @property
    def database_config(self) -> dict:
        """Return database configuration as a dictionary"""
        return {
            "dsn": self.DATABASE_URL,
            "minconn": self.DATABASE_MIN_CONNECTIONS,
            "maxconn": self.DATABASE_MAX_CONNECTIONS
        }

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Raises:
        ValidationError: If required environment variables are missing
    """
    return Settings()

try:
    settings = get_settings()
except Exception as e:
    print("Error loading configuration in config.py:")
    print(e)
    raise SystemExit(1)

def verify_environment():
    """Verify all required environment variables are set correctly"""
    required_vars = [
        ("UPSTASH_REDIS_HOST", settings.UPSTASH_REDIS_HOST),
        ("UPSTASH_REDIS_PASSWORD", settings.UPSTASH_REDIS_PASSWORD),
        ("UPSTASH_REDIS_PORT", settings.UPSTASH_REDIS_PORT),
        ("DATABASE_URL", settings.DATABASE_URL),
        ("PINECONE_API_KEY", settings.PINECONE_API_KEY),
        ("PINECONE_INDEX_NAME", settings.PINECONE_INDEX_NAME)
    ]
    
    missing = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing.append(var_name)
    
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            f"{', '.join(missing)}"
        )

# Verify environment variables on import
verify_environment()
