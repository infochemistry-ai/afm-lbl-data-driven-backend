import pytest

from app.storage import get_storage
from app.storage.local import LocalStorage


def test_factory_returns_local_by_default():
    s = get_storage()
    assert isinstance(s, LocalStorage)


def test_factory_returns_s3(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    get_storage.cache_clear()
    from app.storage.s3 import S3Storage
    s = get_storage()
    assert isinstance(s, S3Storage)


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "ftp")
    get_storage.cache_clear()
    with pytest.raises(ValueError):
        get_storage()
