import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "Integração Estapar - Data Lake"
    APP_VERSION: str = "0.1.6"

    # Auth
    API_KEY: str

    # Database
    DATABASE_URL: str = 'sqlite:///db.sqlite3'


class DevelopmentSettings(Settings):
    pass


class ProductionSettings(Settings):
    pass


class TestingSettings(Settings):
    pass


@lru_cache
def get_settings() -> Settings:
    config_name = os.environ.get("ENVIRONMENT", "production").capitalize()
    config_dict = {
        "Development": DevelopmentSettings,
        "Production": ProductionSettings,
        "Testing": TestingSettings,
        "Staging": TestingSettings,
    }
    return config_dict[config_name]()


settings = get_settings()