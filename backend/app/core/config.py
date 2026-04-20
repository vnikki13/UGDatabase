from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field, PostgresDsn
from sqlalchemy.engine.url import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use .env file at /app/.env for Docker compatibility
        env_file=".env",
        env_file_encoding="utf-8",
    )

    API_V1_PREFIX: str = '/api/v1'
    DEBUG: bool = False

    ALLOWED_ORIGINS: str = ''

    @field_validator('ALLOWED_ORIGINS')
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(',') if v else []

    POSTGRES_SERVER: str = ''
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ''
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    CLOUD_SQL_CONNECTION_NAME: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field
    @property
    def PROD_SQLALCHEMY_DATABASE_URI(self) -> URL:
        return URL.create(
            drivername="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            database=self.POSTGRES_DB,
            query={"host": f"/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"},
        )

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        # Use Cloud SQL socket only when an instance connection name is configured.
        if self.CLOUD_SQL_CONNECTION_NAME:
            return str(self.PROD_SQLALCHEMY_DATABASE_URI)
        return str(self.SQLALCHEMY_DATABASE_URI)

    DOCKER_IMAGE_BACKEND: str = ""
    GCS_BUCKET_NAME: str = ""
    GCS_PROJECT_ID: str = ""

    GHOST_URL: str = ""
    GHOST_ADMIN_KEY: str = ""


settings = Settings()
