from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "CHANGE-ME-TO-A-LONG-RANDOM-SECRET-AT-LEAST-32-CHARS"  # nosec B105 - rejected in production by the validator below


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )
    app_name: str = "Drama Bénin API"
    # Fail closed: a missing or misspelled ENVIRONMENT behaves as production and refuses unsafe defaults.
    environment: str = "production"
    database_url: str = "sqlite:///./drama.db"
    redis_url: str = "redis://redis:6379/0"
    # JWT_SECRET_KEY is accepted too: it used to be silently ignored, which left the public default secret active.
    jwt_secret: str = Field(
        default=DEFAULT_SECRET,
        validation_alias=AliasChoices("jwt_secret", "jwt_secret_key"),
    )
    jwt_issuer: str = "drama-benin"
    access_token_minutes: int = Field(
        default=20,
        validation_alias=AliasChoices("access_token_minutes", "access_token_expire_minutes"),
    )
    refresh_token_days: int = 30
    public_api_url: str = ""
    payment_return_url: str = ""
    fedapay_secret_key: str = ""
    fedapay_webhook_secret: str = ""
    fedapay_environment: str = "sandbox"
    cinetpay_api_key: str = ""
    cinetpay_api_password: str = ""
    cinetpay_environment: str = "sandbox"
    cinetpay_base_url: str = ""
    tmdb_api_key: str = ""
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.frontend_origins.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _normalise_and_guard(self) -> "Settings":
        self.environment = {"prod": "production"}.get(self.environment.lower(), self.environment.lower())
        # The code uses a synchronous SQLAlchemy engine with psycopg: accept asyncpg/postgres:// URLs
        # copied from other configs instead of crashing at startup.
        for prefix in ("postgresql+asyncpg://", "postgres://", "postgresql://"):
            if self.database_url.startswith(prefix):
                self.database_url = "postgresql+psycopg://" + self.database_url[len(prefix) :]
                break
        if self.is_production:
            problems = []
            if self.jwt_secret == DEFAULT_SECRET or len(self.jwt_secret) < 32:
                problems.append("JWT_SECRET must be a random string of at least 32 characters")
            if self.access_token_minutes > 60:
                problems.append("ACCESS_TOKEN_MINUTES must be <= 60 (use the refresh token for long sessions)")
            if not self.database_url.startswith("postgresql"):
                problems.append("DATABASE_URL must point to PostgreSQL in production")
            if self.fedapay_secret_key and not self.fedapay_webhook_secret:
                problems.append("FEDAPAY_WEBHOOK_SECRET is required when FEDAPAY_SECRET_KEY is set")
            if problems:
                raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
