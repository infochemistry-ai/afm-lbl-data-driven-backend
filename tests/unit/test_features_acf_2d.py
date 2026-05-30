import numpy as np
from uuid import uuid4

from app.features.acf_2d import Acf2dExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx(px=256):
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=px, pixels_y=px, width_um=5.0, height_um=5.0, units="m"),
    )


def test_acf_2d_known_correlation_length():
    # Synthesise a Gaussian-correlated surface by convolving white noise with a Gaussian
    # kernel of 1/e radius sigma_px. The resulting 2D ACF (= autocorrelation of the kernel
    # since noise is delta-correlated) has 1/e radius ~ sigma_px * sqrt(2).
    rng = np.random.default_rng(42)
    n = 256
    sigma_px = 8.0
    noise = rng.normal(0, 1, (n, n))
    y, x = np.mgrid[-n // 2:n // 2, -n // 2:n // 2]
    kernel = np.exp(-(x ** 2 + y ** 2) / (2 * sigma_px ** 2))
    kernel /= kernel.sum()
    Z = np.real(np.fft.ifft2(np.fft.fft2(noise) * np.fft.fft2(np.fft.ifftshift(kernel))))

    s = Surface(heights=Z, width_um=5.0, height_um=5.0, channel="Height", units="m")
    out = Acf2dExtractor().extract(s, _ctx(n), {})
    pixel_size_nm = 5000.0 / (n - 1)
    expected_nm = sigma_px * np.sqrt(2) * pixel_size_nm
    assert 0.5 * expected_nm < out["correlation_length_nm"] < 2.0 * expected_nm


def test_acf_2d_flat_surface_returns_full_corr_length():
    z = np.ones((64, 64)) * 1e-9
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = Acf2dExtractor().extract(s, _ctx(64), {})
    assert out["correlation_length_nm"] is not None
    assert out["correlation_length_nm"] > 0
