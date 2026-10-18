"""Application configuration loaded from environment variables / .env files."""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # `../.env` lets you share one .env at the project root; `.env` allows a backend-local file.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_name: str = "Smart Resume Analyzer API"
    environment: str = "development"  # development | production | test
    log_level: str = "INFO"

    # --- Database -------------------------------------------------------
    # Either set DATABASE_URL directly, or the POSTGRES_* parts below.
    database_url: Optional[str] = None
    postgres_user: str = "resume_user"
    postgres_password: str = ""
    postgres_db: str = "resume_analyzer"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- Auth -----------------------------------------------------------
    # No default on purpose: the app refuses to start without a secret.
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Uploads --------------------------------------------------------
    upload_dir: str = "uploads"
    max_upload_mb: int = 5

    # --- AI -------------------------------------------------------------
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    spacy_model_name: str = "en_core_web_sm"
    preload_models: bool = False  # load spaCy + transformer at startup
    coverage_threshold: float = 0.45  # heuristic: cosine above which a JD requirement counts as covered
    custom_skills_path: Optional[str] = None  # optional JSON file that extends the skill dictionary

    # --- CORS -----------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("jwt_secret_key")
    @classmethod
    def _secret_not_empty(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("JWT_SECRET_KEY must be at least 16 characters long")
        return v

    @model_validator(mode="after")
    def _no_placeholder_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.jwt_secret_key.startswith("change-me"):
            raise ValueError("Set a real JWT_SECRET_KEY before running in production")
        return self

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg2",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
