"""Configuration centralisee de l'application."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Parametres charges depuis l'environnement ou un fichier .env."""

	database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/stageflow"
	debug: bool = True
	app_name: str = "StageFlow API"
	environment: str = "development"
	access_token_expire_minutes: int = 15
	refresh_token_expire_days: int = 7
	jwt_secret_key: str = Field(default="development-secret-change-me-32-chars", min_length=32)
	jwt_algorithm: str = "HS256"
	access_token_expire_minutes: int = 60

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
	"""Retourne une instance mise en cache de la configuration."""
	return Settings()


settings = get_settings()
