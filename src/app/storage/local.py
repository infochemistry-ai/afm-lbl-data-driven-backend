import shutil
from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    backend_name = "local"

    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        target = (self.root / key).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as e:
            raise ValueError(f"Key escapes storage root: {key}") from e
        return target

    def put(self, key: str, data: BinaryIO) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            shutil.copyfileobj(data, out)

    def open(self, key: str) -> BinaryIO:
        return self._resolve(key).open("rb")

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)

    def url(self, key: str, expires_sec: int | None = None) -> str:
        return f"/api/v1/files/{key}"
