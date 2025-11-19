from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field, PostgresDsn


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file='../.env',
        env_file_encoding='utf-8'
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

    DOCKER_IMAGE_BACKEND: str = ""


settings = Settings()
