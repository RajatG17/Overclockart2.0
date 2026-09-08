from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    database_url: str
    migration_database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_prefix="AUTH_",
        extra="ignore",
    )

settings = Settings()