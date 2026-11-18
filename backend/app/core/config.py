from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
    env_file=Path(__file__).resolve().parents[3] / ".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
)

    PROJECT_NAME: str = "AI-Powered Researcher–Student Collaboration System"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "t", "debug", "dev", "development")
        return bool(v)

    # Database
    POSTGRES_USER: str = "collab_user"
    POSTGRES_PASSWORD: str = "collab_secure_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434
    POSTGRES_DB: str = "collab_matcher"

    # Async & Sync SQLAlchemy URLs (using psycopg3 which provides both async and sync engines)
    DATABASE_URL: str = (
        "postgresql+psycopg://collab_user:collab_secure_password@localhost:5434/collab_matcher"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg://collab_user:collab_secure_password@localhost:5434/collab_matcher"
    )

    # Security
    SECRET_KEY: str = "changethisinproduction_super_secret_jwt_key_at_least_32_chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.ENVIRONMENT.lower() in {"production", "prod"} and (
            self.SECRET_KEY == "changethisinproduction_super_secret_jwt_key_at_least_32_chars"
            or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "Production requires an explicitly configured SECRET_KEY of at least 32 characters."
            )
        return self

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # Scholarly Metadata APIs (OpenAlex & Crossref)
    OPENALEX_BASE_URL: str = "https://api.openalex.org"
    OPENALEX_MAILTO: str = "admin@collabmatch.internal"
    OPENALEX_API_KEY: str = ""
    CROSSREF_BASE_URL: str = "https://api.crossref.org"
    CROSSREF_MAILTO: str = "admin@collabmatch.internal"
    SCHOLARLY_REQUEST_TIMEOUT_SECONDS: int = 15


settings = Settings()
