from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket_name: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()