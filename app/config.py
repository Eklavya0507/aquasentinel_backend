from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AquaSentinel Backend"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./aquasentinel.db"

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10
    CORS_ORIGINS: str = "http://127.0.0.1:5500,http://localhost:5500"

    MODEL_A_PATH: str = ""
    MODEL_A_LABEL_ENCODER_PATH: str = ""
    MODEL_A_FEATURES_PATH: str = ""

    MODEL_B_PATH: str = ""
    MODEL_B_FEATURES_PATH: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
