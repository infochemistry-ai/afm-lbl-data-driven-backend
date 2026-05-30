import numpy as np
from uuid import uuid4

from app.features.distribution import DistributionExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx():
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=10, pixels_y=10, width_um=1.0, height_um=1.0, units="m"),
    )


def test_distribution_percentiles():
    z = np.arange(100).reshape(10, 10).astype(np.float64)
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = DistributionExtractor().extract(s, _ctx(), {})
    assert out["min"] == 0.0
    assert out["max"] == 99.0
    assert out["median"] == 49.5
    assert out["P95"] == np.percentile(z, 95)
    assert out["IQR"] == np.percentile(z, 75) - np.percentile(z, 25)
    assert out["entropy_bits"] > 0
