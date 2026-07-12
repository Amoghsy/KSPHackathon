"""
app/config.py — centralised settings for the SCRB backend.

All values are loaded from the .env file (or real environment variables).
Import `settings` anywhere you need configuration:

    from app.config import settings
    print(settings.app_name)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application identity
    app_name: str = "SCRB Intelligence Platform"
    app_env: str = "local"
    secret_key: str = "change-me"

    # Database
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/scrb"

    # Cache
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
    )


# Single module-level instance — import this everywhere.
settings = Settings()
