import io
import json
from datetime import datetime, timezone
from uuid import UUID

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as papq
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Experiment, Feature, Sample, Scan
from app.storage import get_storage


def _flatten(rows: list[dict]) -> list[dict]:
    keys: set[str] = set()
    for r in rows:
        keys.update(r.keys())
    return [{k: r.get(k) for k in keys} for r in rows]


def build_dataset(session: Session, *, filter_: dict, format_: str, export_id: UUID) -> tuple[str, int]:
    experiment_id = filter_.get("experiment_id")
    sample_ids = filter_.get("sample_ids")
    extractor_filter: set[str] | None = set(filter_["extractors"]) if filter_.get("extractors") else None

    scans_stmt = select(Scan).join(Sample, Sample.id == Scan.sample_id).join(Experiment, Experiment.id == Sample.experiment_id)
    if experiment_id:
        scans_stmt = scans_stmt.where(Sample.experiment_id == experiment_id)
    if sample_ids:
        scans_stmt = scans_stmt.where(Scan.sample_id.in_(sample_ids))
    scans = list(session.scalars(scans_stmt))

    sample_lookup = {s.id: s for s in session.scalars(select(Sample).where(Sample.id.in_({s.sample_id for s in scans})))} if scans else {}
    exp_lookup = {e.id: e for e in session.scalars(select(Experiment).where(Experiment.id.in_({s.experiment_id for s in sample_lookup.values()})))} if sample_lookup else {}

    feature_rows = list(session.scalars(select(Feature).where(
        (Feature.scan_id.in_({s.id for s in scans})) | (Feature.sample_id.in_({s.sample_id for s in scans}))
    ))) if scans else []

    latest: dict[tuple, Feature] = {}
    for f in feature_rows:
        if extractor_filter and f.extractor_name not in extractor_filter:
            continue
        key = (f.scan_id, f.sample_id, f.extractor_name, f.params_hash)
        if key not in latest or f.computed_at > latest[key].computed_at:
            latest[key] = f

    by_scan: dict[UUID, list[Feature]] = {}
    by_sample: dict[UUID, list[Feature]] = {}
    for f in latest.values():
        if f.scan_id:
            by_scan.setdefault(f.scan_id, []).append(f)
        else:
            by_sample.setdefault(f.sample_id, []).append(f)

    rows: list[dict] = []
    extractor_versions: dict[str, str] = {}
    for scan in scans:
        sample = sample_lookup[scan.sample_id]
        exp = exp_lookup[sample.experiment_id]
        row: dict = {
            "experiment_id": str(exp.id),
            "experiment_name": exp.name,
            "sample_id": str(sample.id),
            "sample_name": sample.name,
            "scan_id": str(scan.id),
            "original_filename": scan.original_filename,
        }
        for f in by_scan.get(scan.id, []) + by_sample.get(scan.sample_id, []):
            extractor_versions[f.extractor_name] = f.extractor_version
            for k, v in (f.values or {}).items():
                row[f"{f.extractor_name}__{k}"] = v
        rows.append(row)

    rows = _flatten(rows)
    table = pa.Table.from_pylist(rows) if rows else pa.table({})

    storage = get_storage()
    ext = "parquet" if format_ == "parquet" else "csv"
    key = f"exports/{export_id}.{ext}"
    buf = io.BytesIO()
    if format_ == "parquet":
        papq.write_table(table, buf)
    else:
        pacsv.write_csv(table, buf)
    buf.seek(0)
    storage.put(key, buf)

    manifest = {
        "export_id": str(export_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filter": filter_,
        "format": format_,
        "row_count": len(rows),
        "extractor_versions": extractor_versions,
    }
    storage.put(f"exports/{export_id}.manifest.json", io.BytesIO(json.dumps(manifest, indent=2).encode("utf-8")))
    return key, len(rows)
