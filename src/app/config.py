from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    storage_backend: Literal["local", "s3"] = "local"
    storage_local_root: str = "./storage"
    export_local_root: str = "./exports"

    s3_bucket: str = ""
    s3_prefix: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_presign_expires_sec: int = 3600

    @model_validator(mode="after")
    def _validate_s3(self) -> "Settings":
        if self.storage_backend == "s3" and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
