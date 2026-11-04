"""
config.py
---------
Reads all settings from environment variables / the .env file.
Nothing secret is hardcoded in the code.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database settings ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "auth_db"
    db_user: str = "postgres"
    db_password: str  # required, no default on purpose

    # --- JWT settings ---
    jwt_secret_key: str  # required, no default on purpose
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Tell pydantic-settings to read the ".env" file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("jwt_secret_key")
    @classmethod
    def secret_must_be_strong(cls, value: str) -> str:
        # A short secret can be guessed/brute-forced, so we refuse to start.
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        return value


# One shared settings object used by the whole app
settings = Settings()
