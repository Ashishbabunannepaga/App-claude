from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (or a local, git-ignored .env).

    Nothing secret has a usable default: production startup fails if secrets are missing.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "InsureIQ API"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = []

    database_url: str = "postgresql+psycopg://insure:insure@localhost:5432/insure"
    redis_url: str = "redis://localhost:6379/0"
    tasks_eager: bool = True  # run background jobs inline (dev/test). False in staging/production.

    # Auth
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    otp_hmac_secret: str = "dev-only-insecure-otp-secret"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 30
    otp_max_requests_per_hour: int = 5
    otp_sender: Literal["console", "msg91"] = "console"
    msg91_auth_key: str | None = None
    msg91_template_id: str | None = None
    # Store-review demo login. Set ONLY via environment in the review environment.
    review_login_identifier: str | None = None
    review_login_code: str | None = None
    privacy_policy_version: str = "2026-10-01"

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: str = "./var/storage"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None  # set for Cloudflare R2
    s3_region: str = "ap-south-1"
    signed_url_ttl_seconds: int = 300
    max_upload_bytes: int = 20 * 1024 * 1024
    max_pdf_pages: int = 60

    # AI
    ai_provider: Literal["claude", "openai", "gemini", "mock"] = "mock"
    anthropic_api_key: str | None = None
    claude_model: str = "claude-sonnet-5-5"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    embedding_provider: Literal["openai", "hashing"] = "hashing"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    ai_timeout_seconds: float = 60.0
    rag_top_k: int = 6

    # Notifications
    push_sender: Literal["log", "fcm"] = "log"
    fcm_project_id: str | None = None
    fcm_service_account_json: str | None = None  # JSON contents, injected from the secrets manager
    renewal_reminder_days: list[int] = [90, 60, 30, 15, 7, 1]

    # Rate limiting: "memory" (single process) or "redis" (shared across replicas)
    rate_limit_backend: Literal["memory", "redis"] = "memory"

    # Admin API (read-mostly ops view). Unset = admin disabled.
    admin_api_token: str | None = None

    # OCR
    ocr_provider: Literal["tesseract", "none"] = "tesseract"

    @model_validator(mode="after")
    def _guard_production(self) -> "Settings":
        if self.env == "production":
            problems = []
            if self.jwt_secret.startswith("dev-only") or len(self.jwt_secret) < 32:
                problems.append("JWT_SECRET must be a strong secret")
            if self.otp_hmac_secret.startswith("dev-only"):
                problems.append("OTP_HMAC_SECRET must be set")
            if self.ai_provider == "mock" or self.embedding_provider == "hashing":
                problems.append("MOCK AI/embedding providers are not allowed in production")
            if self.otp_sender == "console":
                problems.append("console OTP sender is not allowed in production")
            if self.storage_backend == "local":
                problems.append("local storage is not allowed in production")
            if self.push_sender == "log":
                problems.append("PUSH_SENDER=fcm is required in production")
            if self.rate_limit_backend == "memory":
                problems.append("RATE_LIMIT_BACKEND=redis is required in production")
            if self.admin_api_token is not None and len(self.admin_api_token) < 32:
                problems.append("ADMIN_API_TOKEN must be at least 32 characters")
            if self.tasks_eager:
                problems.append("TASKS_EAGER must be false in production")
            if problems:
                raise ValueError("; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
