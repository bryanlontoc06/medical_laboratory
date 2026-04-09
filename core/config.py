import os
from urllib.parse import quote_plus

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine the path to the .env.local file relative to this config.py file
current_dir = os.path.dirname(os.path.abspath(__file__))
app_env = os.getenv("APP_ENV", "local")
env_filename = f".env.{app_env}"
# Construct the full path to the .env file
env_path = os.path.join(current_dir, env_filename)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        extra="ignore",
        env_file_encoding="utf-8",
    )
    PORT: int
    APP_ENV: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_TTL: int = 2592000  # in seconds (30 days)
    ACCESS_TOKEN_TTL: int = 86400  # in seconds (1 day)
    secret_key: SecretStr
    GUEST_UID: str

    @property
    def DATABASE_URL(self) -> str:
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"mysql+aiomysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file
