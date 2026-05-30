import numpy as np
from uuid import uuid4

from app.features.psd_radial import PsdRadialExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx(px=128):
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=px, pixels_y=px, width_um=5.0, height_um=5.0, units="m"),
    )


def test_psd_dominant_wavelength_for_sinusoid():
    n = 128
    width_um = 5.0
    period_px = 16
    y, x = np.mgrid[0:n, 0:n]
    z = np.sin(2 * np.pi * x / period_px)
    s = Surface(heights=z.astype(np.float64), width_um=width_um, height_um=width_um,
                channel="Height", units="m")
    out = PsdRadialExtractor().extract(s, _ctx(n), {})
    pixel_size_nm = width_um * 1000.0 / (n - 1)
    expected_nm = period_px * pixel_size_nm
    assert 0.5 * expected_nm < out["dominant_wavelength_nm"] < 2.0 * expected_nm


def test_psd_returns_required_keys_for_random_input():
    rng = np.random.default_rng(0)
    z = rng.normal(0, 1e-9, (64, 64))
    s = Surface(heights=z, width_um=2.0, height_um=2.0, channel="Height", units="m")
    out = PsdRadialExtractor().extract(s, _ctx(64), {})
    for k in ("hurst_H", "fractal_dim_D", "psd_slope_beta",
              "dominant_wavelength_nm", "anisotropy_index", "total_power"):
        assert k in out
