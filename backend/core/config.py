from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    app_name: str = "Snap Class API"

    supabase_url: str
    supabase_key: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cors_origins: list[str] = ["http://localhost:3000"]

    face_match_threshold: float = 0.6
    voice_match_threshold: float = 0.65

    voice_model_dir: str = "pretrained_models/spkrec-ecapa-voxceleb-win"

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()