import numpy as np
from uuid import uuid4

from app.features.metadata import MetadataExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx():
    return ExtractionContext(
        sample_id=uuid4(),
        scan_id=uuid4(),
        layers=[],
        polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=256, pixels_y=256, width_um=5.0, height_um=5.0, units="m"),
    )


def test_metadata_extracts_pixel_size_and_aspect():
    s = Surface(heights=np.zeros((256, 256)), width_um=5.0, height_um=5.0, channel="Height", units="m")
    out = MetadataExtractor().extract(s, _ctx(), {})
    assert out["pixels_x"] == 256
    assert out["pixels_y"] == 256
    assert out["pixel_size_x_nm"] == 5.0 * 1000 / 255
    assert out["pixel_size_y_nm"] == 5.0 * 1000 / 255
    assert out["aspect_ratio"] == 1.0
