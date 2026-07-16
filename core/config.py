from functools import lru_cache
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Attendy")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    app_name: str = "Attendy Class API"

    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str | None = None

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://attendy-frontend-three.vercel.app"
    ]

    face_match_threshold: float = 0.6
    voice_match_threshold: float = 0.65

    voice_model_dir: str = "pretrained_models/spkrec-ecapa-voxceleb-win"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

logger.info("SUPABASE_URL = %r", settings.supabase_url)
logger.info("SUPABASE_KEY exists = %s", bool(settings.supabase_key))