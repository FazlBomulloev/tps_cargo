from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode

_DEFAULT_JWT_SECRET_KEY = "change-me-in-production"
_DEFAULT_API_BOT_SECRET = "shared-secret-for-bot-to-api"
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    DATABASE_URL: str = ""

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "cargo_tps"
    POSTGRES_USER: str = "cargo"
    POSTGRES_PASSWORD: str = "secret"

    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    BOT_TOKEN: str = ""
    CHANNEL_USERNAME: str = ""
    CHANNEL_URL: str = ""

    API_BOT_SECRET: str = _DEFAULT_API_BOT_SECRET

    OWNER_LOGIN: str = "owner"
    OWNER_PASSWORD: str = "change-me"
    OWNER_FULL_NAME: str = "Owner"

    # NoDecode disables pydantic-settings' default JSON parsing for
    # list-typed env vars so plain comma-separated strings work.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # IPs of reverse proxies/load balancers allowed to set X-Forwarded-For.
    # Empty by default — X-Forwarded-For is ignored unless the direct
    # connection comes from one of these (otherwise it's spoofable).
    TRUSTED_PROXIES: Annotated[list[str], NoDecode] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def _parse_trusted_proxies(cls, value):
        if isinstance(value, str):
            return [ip.strip() for ip in value.split(",") if ip.strip()]
        return value

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong random value, not the default"
            )
        if len(self.JWT_SECRET_KEY) < _MIN_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {_MIN_SECRET_LENGTH} characters long"
            )
        if self.API_BOT_SECRET == _DEFAULT_API_BOT_SECRET:
            raise ValueError(
                "API_BOT_SECRET must be set to a strong random value, not the default"
            )
        if len(self.API_BOT_SECRET) < _MIN_SECRET_LENGTH:
            raise ValueError(
                f"API_BOT_SECRET must be at least {_MIN_SECRET_LENGTH} characters long"
            )
        return self

    @property
    def database_url_resolved(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite+aiosqlite:///./data/cargo_tps.db"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
