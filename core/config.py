import os

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


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file
