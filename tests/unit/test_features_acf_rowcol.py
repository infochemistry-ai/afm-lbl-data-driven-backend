import numpy as np
from uuid import uuid4

from app.features.acf_rowcol import AcfRowColExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx(px=64):
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=px, pixels_y=px, width_um=5.0, height_um=5.0, units="m"),
    )


def test_acf_rowcol_returns_curves_and_summary():
    rng = np.random.default_rng(1)
    z = rng.normal(0, 1e-9, (64, 64))
    s = Surface(heights=z, width_um=5.0, height_um=5.0, channel="Height", units="m")
    out = AcfRowColExtractor().extract(s, _ctx(64), {})
    assert "acf_x_curve" in out and len(out["acf_x_curve"]) == 64
    assert "acf_y_curve" in out and len(out["acf_y_curve"]) == 64
    assert out["acf_x_curve"][0] == 1.0
    for k in ("acf_x_first_zero_crossing_nm",
              "acf_y_first_zero_crossing_nm",
              "acf_x_corr_length_nm",
              "acf_y_corr_length_nm",
              "anisotropy_xy_ratio"):
        assert k in out


def test_acf_rowcol_constant_signal():
    z = np.ones((32, 32))
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = AcfRowColExtractor().extract(s, _ctx(32), {})
    assert "acf_x_curve" in out
    assert "acf_y_curve" in out
