# AFM LbL Data-Driven Backend

![GitHub](https://img.shields.io/github/license/infochemistry-ai/afm-lbl-data-driven-backend)
![GitHub last commit](https://img.shields.io/github/last-commit/infochemistry-ai/afm-lbl-data-driven-backend)
![GitHub pull requests](https://img.shields.io/github/issues-pr/infochemistry-ai/afm-lbl-data-driven-backend)
![contributors](https://img.shields.io/github/contributors/infochemistry-ai/afm-lbl-data-driven-backend)
![codesize](https://img.shields.io/github/languages/code-size/infochemistry-ai/afm-lbl-data-driven-backend)
![GitHub repo size](https://img.shields.io/github/repo-size/infochemistry-ai/afm-lbl-data-driven-backend)
![GitHub top language](https://img.shields.io/github/languages/top/infochemistry-ai/afm-lbl-data-driven-backend)
![GitHub language count](https://img.shields.io/github/languages/count/infochemistry-ai/afm-lbl-data-driven-backend)

## Introduction

The backend presented below converts raw atomic force microscopy (AFM) scans and layer-by-layer (LbL) polyelectrolyte deposition recipes into a unified, versioned set of physically interpretable descriptors suitable for downstream machine learning. The pipeline operates on two parallel streams — scan-level descriptors derived from the height map and sample-level descriptors derived from the ordered polyelectrolyte recipe — and joins them per scan into a wide feature matrix exportable as Parquet or CSV.

The system has been developed at the Infochemistry Scientific Center ([ISC](https://infochemistry.ru/)), ITMO University, as the data-side counterpart of a robotised dip-coating platform for high-throughput preparation and characterisation of polyelectrolyte multilayers. It builds on the topological-data-analysis methodology introduced by Aglikov, Aliev, Zhukov, Nikitina, Smirnov, Kozodaev, Nosonovsky and Skorb in *ACS Applied Electronic Materials* (2023), and re-uses the gliding-box lacunarity C++ implementation vendored from the [Fractal-Analisys](https://github.com/ShockOfWave/Fractal-Analisys) repository.

## Feature extractors

Twelve extractors are registered in the default pipeline. Adding a new extractor amounts to dropping a single Python module into `src/app/features/` — no changes to the worker, HTTP API or database schema are required.

**Scan-level (per AFM height map)**

| Extractor | Output |
|---|---|
| `metadata` | Pixel size, aspect ratio, applied preprocessing chain |
| `iso25178` | Sa, Sq, Sz, Ssk, Sku, Sdq, Sdr, Sal, Str, Sk, Spk, Svk, Vmp, Vmc, Vvc, Vvv |
| `distribution` | Min/max/mean/σ, percentiles (P1, P5, P25, P75, P95, P99), IQR, Shannon entropy of the height histogram |
| `psd_radial` | Radial 2D power spectrum, Hurst exponent H, fractal dimension D = 3 − H, dominant wavelength, anisotropy index |
| `acf_2d` | 2D autocorrelation (FFT), correlation length ξ, roughness exponent α |
| `acf_rowcol` | 1D ACF of the central row and central column with first zero crossing and 1/e correlation length |
| `minmax_patches` | 18-bin distribution of local minimum/maximum positions within non-overlapping 3 × 3 pixel patches |
| `tda_persistence` | Vietoris–Rips persistent homology on the 9-dimensional patch cloud (H₀/H₁/H₂ summaries + full diagram) |
| `lacunarity` | Multi-scale gliding-box lacunarity Λ(r) and derived geometric counters (vendored C++ library, optional) |

**Sample-level (per LbL recipe)**

| Extractor | Output |
|---|---|
| `polyelectrolyte_meta` | Number of layers and bilayers, first / terminal layer identity, charge alternation ratio, max same-charge run, log Mw averaged and terminal |
| `pe_sequence_kmer` | Bigrams and trigrams of layer types, charge n-grams (++, +−, −+, −−), most common layer identity |
| `rdkit_monomer` | MolWt, MolLogP, TPSA, H-bond donors/acceptors, BertzCT, Balaban J, Chi and Kappa indices, Morgan fingerprint of the terminal monomer (RDKit) |

A standardised preprocessing chain — least-squares plane subtraction, row-wise median levelling, σ-based outlier clipping — is applied to every scan before feature extraction; the applied steps are stored alongside the features so any subsequent comparison can account for the conditioning regime.

## Functionality tested

- [x] Debian / Ubuntu (apt)
- [x] macOS (Homebrew)
- [ ] Windows

## Installation

### With Docker (recommended)

```bash
git clone git@github.com:infochemistry-ai/afm-lbl-data-driven-backend.git
cd afm-lbl-data-driven-backend
cp .env.example .env

docker compose up -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.cli seed polyelectrolytes
docker compose up api worker
```

The HTTP API is then available on `http://localhost:8000`; interactive OpenAPI docs are at `/docs`. The `lacunarity` extractor is built into the image automatically. Celery monitoring can be enabled with `docker compose --profile dev up flower`.

### Without Docker

```bash
git clone git@github.com:infochemistry-ai/afm-lbl-data-driven-backend.git
cd afm-lbl-data-driven-backend
```

Install the build-time dependency of the lacunarity C++ library:

* For apt:
    ```bash
    sudo apt install libgsl-dev cmake build-essential
    ```
* For brew:
    ```bash
    brew install gsl cmake
    ```

PostgreSQL 16 and Redis 7 must be available on the host. Then:

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.cli seed polyelectrolytes
uv run python -m app.cli build lacunarity          # compiles the vendored C++ library
uv run uvicorn app.main:app --reload               # terminal 1
uv run celery -A app.workers.celery_app worker -l info   # terminal 2
```

If the lacunarity library is not compiled, the corresponding extractor is silently skipped at startup and the rest of the pipeline runs unaffected.

## Usage

### Ingesting a single scan

```bash
# 1. Create an experiment
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d '{"name": "exp-001", "description": "baseline"}'

# 2. Create a sample with an LbL recipe
curl -X POST http://localhost:8000/api/v1/experiments/<exp_id>/samples \
  -H "Content-Type: application/json" \
  -d '{
        "name": "PE12",
        "substrate": "Si",
        "layers": [
          {"position": 1, "polyelectrolyte_id": "PEI", "molecular_weight_kda": 750},
          {"position": 2, "polyelectrolyte_id": "PSS", "molecular_weight_kda": 1000}
        ]
      }'

# 3. Upload an AFM scan; feature extraction is enqueued automatically
curl -X POST http://localhost:8000/api/v1/samples/<sample_id>/scans \
  -F "file=@PE12_1.txt"

# 4. Poll status, then retrieve features
curl http://localhost:8000/api/v1/scans/<scan_id>
curl http://localhost:8000/api/v1/scans/<scan_id>/features
```

### Bulk-ingesting an existing folder of AFM data

The provided CLI command walks a layered folder tree (`no_layers/`, `1_layer/`, …, `4_layers/`) and ingests every `.txt` scan it finds, attaching the appropriate canonical recipe to each sample:

```bash
uv run python -m app.cli ingest raw-data ./raw_data --experiment-name baseline
```

### Recomputing features

Adding or modifying an extractor does not affect previously stored features; the new version is written as a new row, the old version remains queryable:

```bash
# All extractors on one scan
curl -X POST http://localhost:8000/api/v1/scans/<scan_id>/recompute

# A single named extractor
curl -X POST http://localhost:8000/api/v1/scans/<scan_id>/recompute \
  -H "Content-Type: application/json" -d '{"extractors": ["tda_persistence"]}'

# All scans of a sample
curl -X POST http://localhost:8000/api/v1/samples/<sample_id>/recompute
```

### Exporting the joined dataset

```bash
curl -X POST http://localhost:8000/api/v1/exports/dataset \
  -H "Content-Type: application/json" \
  -d '{"format": "parquet", "filter": {"experiment_id": "<exp_id>"}}'
```

The response includes an `export_id`; once status reaches `ready`, the file can be downloaded:

```bash
curl -L http://localhost:8000/api/v1/exports/<export_id>/download -o dataset.parquet
```

Alongside the dataset, a JSON manifest is written that enumerates the originating method versions and parameters used at the time of export, supporting bit-exact reproduction.

## Storage backends

`STORAGE_BACKEND=local` (default) stores raw scans and exports under `./storage` and `./exports`. Setting `STORAGE_BACKEND=s3` and the `S3_*` environment variables switches to any S3-compatible object storage (AWS S3, MinIO, Yandex Object Storage via `S3_ENDPOINT_URL`). Backend selection is per-deployment; per-scan storage backend is recorded so that historical data remains readable after configuration changes.

## Tests

```bash
uv run pytest                       # full suite — requires Docker for testcontainers
uv run pytest tests/unit            # fast subset, no Docker required
```

## Vendored components

The `src/app/features/_lacunarity/` directory contains a C++ gliding-box lacunarity implementation vendored from [Fractal-Analisys](https://github.com/ShockOfWave/Fractal-Analisys) (subdirectory `lib/`). The original license is preserved next to the source.

## Acknowledgements

We thank the [Infochemistry Scientific Center](https://infochemistry.ru/) (ITMO University) for the provided data, AFM measurements and computing resources.

The methodology of the topological-data-analysis branch of this pipeline follows the work:

> Aleksandr S. Aglikov, Timur A. Aliev, Mikhail V. Zhukov, Anna A. Nikitina, Evgeny Smirnov, Dmitry A. Kozodaev, Michael Nosonovsky, Ekaterina V. Skorb, "Topological Data Analysis of Nanoscale Roughness of Layer-by-Layer Polyelectrolyte Samples Using Machine Learning", *ACS Applied Electronic Materials* vol. 5 issue 12 (2023) pp 6955–6963, [https://doi.org/10.1021/acsaelm.3c01358](https://doi.org/10.1021/acsaelm.3c01358).

```tex
@article{Aglikov2023,
  doi = {10.1021/acsaelm.3c01358},
  url = {https://doi.org/10.1021/acsaelm.3c01358},
  year = {2023},
  month = dec,
  publisher = {American Chemical Society ({ACS})},
  volume = {5},
  number = {12},
  pages = {6955--6963},
  author = {Aleksandr S. Aglikov and Timur A. Aliev and Mikhail V. Zhukov and Anna A. Nikitina and Evgeny Smirnov and Dmitry A. Kozodaev and Michael Nosonovsky and Ekaterina V. Skorb},
  title = {Topological Data Analysis of Nanoscale Roughness of Layer-by-Layer Polyelectrolyte Samples Using Machine Learning},
  journal = {{ACS} Applied Electronic Materials}
}
```

## Reference & Citation

A manuscript describing the combined robotic-deposition + automated-feature-extraction platform is in preparation. Citation details will appear here once the paper is published.

## License
## MIT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
