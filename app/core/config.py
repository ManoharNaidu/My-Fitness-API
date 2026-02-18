from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "My Fitness API"
    api_prefix: str = "/v1"
    secret_key: str = "only_for_development"
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
