from functools import lru_cache

from app.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage


@lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "local":
        return LocalStorage(root=s.storage_local_root)
    if s.storage_backend == "s3":
        from app.storage.s3 import S3Storage
        return S3Storage(
            bucket=s.s3_bucket,
            prefix=s.s3_prefix,
            region=s.s3_region,
            endpoint_url=s.s3_endpoint_url or None,
            access_key_id=s.s3_access_key_id or None,
            secret_access_key=s.s3_secret_access_key or None,
            presign_expires_sec=s.s3_presign_expires_sec,
        )
    raise ValueError(f"Unsupported STORAGE_BACKEND: {s.storage_backend}")


__all__ = ["get_storage", "StorageBackend"]
