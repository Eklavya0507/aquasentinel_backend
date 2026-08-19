from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AquaSentinel Backend"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "AquaSentinel-Local-Demo-Secret-Key-Change-Before-Deploy-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./aquasentinel.db"
    CORS_ORIGINS: str = "http://127.0.0.1:5500,http://localhost:5500,https://eklavya0507.github.io"
    MODEL_B1_PATH: str = "app/ml/B1_disease_risk_model.pkl"
    MODEL_B1_ENCODER_PATH: str = "app/ml/B1_label_encoder.pkl"
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
