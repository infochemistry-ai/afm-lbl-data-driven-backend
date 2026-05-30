# AFM LbL Backend

FastAPI backend for ingesting AFM scans of layer-by-layer polyelectrolyte films, extracting a Stage-1 surface-feature set, and exporting a joined dataset for downstream ML.

## Quickstart (Docker)

```bash
cp .env.example .env
docker compose up -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.cli seed polyelectrolytes
docker compose up api worker
# optional Celery monitoring:
docker compose --profile dev up flower
```

API at http://localhost:8000 ; OpenAPI docs at /docs.

## Local development (no Docker)

```bash
brew services start postgresql@16 redis
createdb afm_lbl
uv sync
uv run alembic upgrade head
uv run python -m app.cli seed polyelectrolytes
uv run uvicorn app.main:app --reload                                       # terminal 1
uv run celery -A app.workers.celery_app worker -l info                     # terminal 2
```

## Bulk-ingest existing raw_data/

```bash
uv run python -m app.cli ingest raw-data ./raw_data --experiment-name baseline
```

## Storage backends

`STORAGE_BACKEND=local` (default) keeps raw scans and exports under `./storage` and `./exports`.
Set `STORAGE_BACKEND=s3` plus the `S3_*` env vars to use S3-compatible object storage (AWS S3, MinIO, Yandex Object Storage via `S3_ENDPOINT_URL`).

## Tests

```bash
uv run pytest                       # full suite (requires Docker for testcontainers)
uv run pytest tests/unit            # fast subset
```
