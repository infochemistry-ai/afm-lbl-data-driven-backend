import numpy as np
from uuid import uuid4

from app.features.minmax_patches import MinMaxPatchesExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx():
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=6, pixels_y=6, width_um=1.0, height_um=1.0, units="m"),
    )


def test_minmax_counts_min_at_known_position():
    z = np.ones((6, 6))
    for r0 in (0, 3):
        for c0 in (0, 3):
            z[r0, c0] = -10.0
            z[r0 + 2, c0 + 2] = 10.0
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = MinMaxPatchesExtractor().extract(s, _ctx(), {})
    assert out["n_patches"] == 4
    assert out["min_pos_0_0_frac"] == 1.0
    assert out["max_pos_2_2_frac"] == 1.0
    assert out["min_pos_1_1_frac"] == 0.0
    assert out["max_pos_0_0_frac"] == 0.0


def test_minmax_handles_non_divisible_shape():
    z = np.zeros((7, 7))
    z[0, 0] = -1
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = MinMaxPatchesExtractor().extract(s, _ctx(), {})
    assert out["n_patches"] == 4
