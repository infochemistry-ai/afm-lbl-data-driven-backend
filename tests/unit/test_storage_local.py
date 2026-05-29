import io

from app.storage.local import LocalStorage


def test_local_put_get_delete(tmp_path):
    s = LocalStorage(root=str(tmp_path))
    s.put("scans/abc.txt", io.BytesIO(b"hello world"))
    assert s.exists("scans/abc.txt")
    with s.open("scans/abc.txt") as f:
        assert f.read() == b"hello world"
    s.delete("scans/abc.txt")
    assert not s.exists("scans/abc.txt")


def test_local_url_returns_api_path(tmp_path):
    s = LocalStorage(root=str(tmp_path))
    assert s.url("scans/abc.txt") == "/api/v1/files/scans/abc.txt"


def test_local_rejects_path_traversal(tmp_path):
    import pytest
    s = LocalStorage(root=str(tmp_path))
    with pytest.raises(ValueError):
        s.put("../etc/passwd", io.BytesIO(b"nope"))
