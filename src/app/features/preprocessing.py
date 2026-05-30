from dataclasses import replace

import numpy as np

from app.parsers.base import Surface


def _subtract_plane(z: np.ndarray) -> np.ndarray:
    ny, nx = z.shape
    y, x = np.mgrid[0:ny, 0:nx]
    a = np.column_stack([x.ravel(), y.ravel(), np.ones(z.size)])
    coeffs, *_ = np.linalg.lstsq(a, z.ravel(), rcond=None)
    plane = (a @ coeffs).reshape(z.shape)
    return z - plane


def _line_median(z: np.ndarray) -> np.ndarray:
    medians = np.median(z, axis=1, keepdims=True)
    return z - medians


def _clip_outliers(z: np.ndarray, sigma: float = 5.0) -> np.ndarray:
    m = z.mean()
    s = z.std()
    if s == 0:
        return z
    lo, hi = m - sigma * s, m + sigma * s
    return np.clip(z, lo, hi)


def preprocess(surface: Surface) -> tuple[Surface, list[str]]:
    steps: list[str] = []
    z = surface.heights.astype(np.float64, copy=True)

    z = _subtract_plane(z); steps.append("level")
    z = _line_median(z);    steps.append("line_median")
    z = _clip_outliers(z);  steps.append("clip_outliers")

    cleaned = replace(surface, heights=z)
    return cleaned, steps
