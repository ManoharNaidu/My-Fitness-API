import json
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "My Fitness API"
    api_prefix: str = "/v1"
    environment: str = "development"

    secret_key: str = "dev-only-change-me"
    cors_allowed_origins: list[str] = []

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    supabase_url: str
    # Prefer service role key for backend-to-Supabase server operations.
    supabase_service_role_key: str | None = None
    # Legacy/support keys:
    supabase_key: str | None = None
    supabase_anon_key: str | None = None

    @property
    def resolved_supabase_key(self) -> str:
        return (
            self.supabase_service_role_key
            or self.supabase_key
            or self.supabase_anon_key
            or ""
        )

    @property
    def is_production(self) -> bool:
        return self.environment in {"prod", "production"}

    @property
    def allowed_cors_origins(self) -> list[str]:
        if self.cors_allowed_origins:
            return self.cors_allowed_origins
        if self.is_production:
            return []
        return [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    @field_validator("environment", mode="before")
    @classmethod
    def _normalize_environment(cls, value: Any) -> str:
        return str(value or "development").strip().lower()

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_allowed_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        raise TypeError("cors_allowed_origins must be a list or comma-separated string")

    @model_validator(mode="after")
    def _validate_security_settings(self):
        if self.is_production and self.secret_key == "dev-only-change-me":
            raise ValueError(
                "SECRET_KEY must be set to a non-default value when ENVIRONMENT=production"
            )
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
