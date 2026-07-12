from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    database_url: str # required - no default, must come from .env or real env vars
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    
settings = Settings()