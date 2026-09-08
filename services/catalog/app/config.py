from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    database_url: str
    migration_database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CATALOG_",
        extra="ignore",
    )

settings = Settings()