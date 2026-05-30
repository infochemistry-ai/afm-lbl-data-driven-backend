import os
import shutil
import tempfile
from datetime import datetime, timezone
from typing import BinaryIO
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Scan
from app.parsers import get_parser_by_name, get_parser_for_extension
from app.parsers.base import Surface
from app.storage import get_storage


def _detect_parser_name(filename: str, parser_hint: str | None) -> str:
    if parser_hint:
        return parser_hint
    ext = os.path.splitext(filename)[1].lower()
    return get_parser_for_extension(ext).name


def ingest_scan(
    session: Session,
    *,
    sample_id,
    filename: str,
    file: BinaryIO,
    parser_hint: str | None = None,
    channel_hint: str | None = None,
) -> Scan:
    parser_name = _detect_parser_name(filename, parser_hint)
    parser_cls = get_parser_by_name(parser_name)
    parser = parser_cls()
    storage = get_storage()
    scan_id = uuid4()
    ext = os.path.splitext(filename)[1].lower() or ".bin"
    storage_key = f"scans/{scan_id}{ext}"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file, tmp)
        tmp_path = tmp.name

    try:
        surface: Surface = parser.parse(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        raise ValueError(f"Parser '{parser_name}' failed: {e}") from e

    with open(tmp_path, "rb") as up:
        storage.put(storage_key, up)
    os.unlink(tmp_path)

    scan = Scan(
        id=scan_id,
        sample_id=sample_id,
        original_filename=filename,
        storage_backend=storage.backend_name,
        storage_key=storage_key,
        parser_name=parser_name,
        channel=channel_hint or surface.channel,
        width_um=surface.width_um,
        height_um=surface.height_um,
        pixels_x=surface.pixels_x,
        pixels_y=surface.pixels_y,
        units=surface.units,
        status="pending",
        uploaded_at=datetime.now(timezone.utc),
    )
    session.add(scan)
    session.flush()
    return scan
