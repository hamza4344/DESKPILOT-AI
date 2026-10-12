"""Modified for DeskPilot AI: typed operational configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "DeskPilot AI"
    app_env: str = "development"
    openai_api_key: str = ""
    tavily_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "deskpilot-it-support"
    pinecone_namespace: str = "company-it-kb"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    index_ready_timeout_seconds: float = Field(default=60, gt=0, le=300)
    embedding_model: str = "text-embedding-3-small"
    openai_model: str = "gpt-4o-mini"
    provider_timeout_seconds: float = Field(default=30, gt=0, le=120)
    top_k: int = Field(default=4, ge=1, le=20)
    max_retries: int = Field(default=1, ge=0, le=3)
    enable_web_search: bool = False
    admin_api_key: str = ""
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    audit_store_questions: bool = False
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    sample_kb_dir: str = str(BASE_DIR / "data" / "sample_kb")
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
