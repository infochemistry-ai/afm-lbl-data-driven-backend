import numpy as np
import pytest
from uuid import uuid4

import app.features.lacunarity as lac_mod
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


pytestmark = pytest.mark.skipif(
    lac_mod._LIB is None,
    reason="lacunarity native library not built (run `python -m app.cli build lacunarity`)",
)


def _ctx():
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=16, pixels_y=16, width_um=1.0, height_um=1.0, units="m"),
    )


def test_lacunarity_runs_on_random_matrix():
    from app.features import get_extractor
    cls = get_extractor("lacunarity")
    rng = np.random.default_rng(0)
    z = rng.normal(0, 1.0, (16, 16))
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = cls().extract(s, _ctx(), {"number_of_slices": 10})
    assert "lambda_curve" in out
    assert isinstance(out["lambda_curve"], list)
    if out["lambda_curve"]:
        assert all(isinstance(v, (int, float)) for v in out["lambda_curve"])
