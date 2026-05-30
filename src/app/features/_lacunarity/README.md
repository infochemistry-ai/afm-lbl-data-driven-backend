# Vendored: lacunarity (C++)

Source: https://github.com/ShockOfWave/Fractal-Analisys (subdir `lib/`).
License: see `LICENSE` next to this file.

## Build

From the project root:

    uv run python -m app.cli build lacunarity

This runs `cmake -S src/app/features/_lacunarity -B src/app/features/_lacunarity/build`
and `cmake --build src/app/features/_lacunarity/build`, producing
`liblacunarity.{so|dylib}` under `build/`.

The Python extractor (`src/app/features/lacunarity.py`) loads this library
at import time. If the library is missing, the extractor is not registered
and the rest of the pipeline runs without it.
