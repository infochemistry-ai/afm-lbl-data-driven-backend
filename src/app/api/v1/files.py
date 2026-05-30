from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.storage import get_storage
from app.storage.local import LocalStorage

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{key:path}")
def serve(key: str) -> StreamingResponse:
    s = get_storage()
    if not isinstance(s, LocalStorage):
        raise HTTPException(404, "local file streaming disabled when storage backend is not local")
    if not s.exists(key):
        raise HTTPException(404, "not found")
    return StreamingResponse(s.open(key), media_type="application/octet-stream")
