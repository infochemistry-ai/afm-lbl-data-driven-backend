import numpy as np
from uuid import uuid4

from app.features.iso25178 import Iso25178Extractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx():
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=64, pixels_y=64, width_um=5.0, height_um=5.0, units="m"),
    )


def test_iso_returns_basic_height_params():
    rng = np.random.default_rng(42)
    z = rng.normal(0, 1e-9, (64, 64))
    s = Surface(heights=z, width_um=5.0, height_um=5.0, channel="Height", units="m")
    out = Iso25178Extractor().extract(s, _ctx(), {})
    # Sa and Sq must exist and be positive for noisy input.
    assert out["Sa"] > 0
    assert out["Sq"] > 0
    # Sq should approximately equal std of zero-mean noise.
    assert abs(out["Sq"] - z.std()) < 1e-12


def test_iso_handles_missing_dimensions():
    # If dimensions are missing, hybrid/areal params may be NaN but height params still work.
    z = np.zeros((32, 32))
    s = Surface(heights=z, width_um=None, height_um=None, channel="Height", units="m")
    out = Iso25178Extractor().extract(s, _ctx(), {})
    assert out["Sa"] == 0.0
    assert out["Sq"] == 0.0
