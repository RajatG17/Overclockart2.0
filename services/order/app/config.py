from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    database_url: str
    migration_database_url: str
    rabbitmq_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_prefix="ORDER_",
        extra="ignore", 
    )

settings = Settings() 