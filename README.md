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

## Stage 2 extractors

The default pipeline runs 12 extractors (4 MVP + 8 Stage 2):

- **Scan-level:** `metadata`, `iso25178`, `distribution`, `minmax_patches`, `psd_radial`, `acf_2d`, `acf_rowcol`, `tda_persistence`, `lacunarity` (if C++ lib is built)
- **Sample-level:** `polyelectrolyte_meta`, `pe_sequence_kmer`, `rdkit_monomer`

Each extractor stores its results as a `features` row with `extractor_name`,
`extractor_version`, and the value dict. To recompute a single extractor:

```
POST /api/v1/scans/{id}/recompute  {"extractors": ["psd_radial"]}
```

## Vendored components

- **`src/app/features/_lacunarity/`** — C++ lacunarity implementation vendored from
  [github.com/ShockOfWave/Fractal-Analisys](https://github.com/ShockOfWave/Fractal-Analisys)
  (subdir `lib/`). License in `src/app/features/_lacunarity/LICENSE`. Requires GSL
  (`libgsl-dev` in Debian/Ubuntu, `brew install gsl` on macOS).

  Build locally:
  ```
  uv run python -m app.cli build lacunarity
  ```

  The Docker image builds it automatically (`libgsl-dev` is in the apt install
  list). If the library is missing at runtime, the `lacunarity` extractor is
  not registered and the rest of the pipeline runs unaffected.

## Recomputing features on existing scans

After adding new extractors or rebuilding the lacunarity library, recompute
features on existing scans:

```
POST /api/v1/samples/{id}/recompute    # all scans of a sample
POST /api/v1/scans/{id}/recompute      # one scan, all extractors
POST /api/v1/scans/{id}/recompute  {"extractors": ["tda_persistence"]}
```
