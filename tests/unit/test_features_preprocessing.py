import numpy as np

from app.features.preprocessing import preprocess
from app.parsers.base import Surface


def test_preprocess_removes_tilt():
    ny, nx = 64, 64
    y, x = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    tilted = 1e-9 * (0.1 * x + 0.2 * y)              # pure plane
    s = Surface(heights=tilted.astype(np.float64), width_um=5.0, height_um=5.0, channel="Height", units="m")
    cleaned, steps = preprocess(s)
    assert "level" in steps
    assert np.abs(cleaned.heights.mean()) < 1e-15
    assert np.abs(cleaned.heights.std()) < 1e-15      # plane fully removed


def test_preprocess_preserves_shape():
    rng = np.random.default_rng(0)
    s = Surface(heights=rng.normal(0, 1e-9, (32, 48)), width_um=5.0, height_um=5.0, channel="Height", units="m")
    cleaned, _ = preprocess(s)
    assert cleaned.heights.shape == (32, 48)
