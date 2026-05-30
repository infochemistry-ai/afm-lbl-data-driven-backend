import numpy as np
from uuid import uuid4

from app.features.tda_persistence import TdaPersistenceExtractor
from app.features.base import ExtractionContext, ScanMetaView
from app.parsers.base import Surface


def _ctx(px=32):
    return ExtractionContext(
        sample_id=uuid4(), scan_id=uuid4(), layers=[], polyelectrolytes={},
        scan_meta=ScanMetaView(pixels_x=px, pixels_y=px, width_um=1.0, height_um=1.0, units="m"),
    )


def test_tda_persistence_returns_summary_and_diagram():
    rng = np.random.default_rng(0)
    z = rng.normal(0, 1e-9, (32, 32))
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = TdaPersistenceExtractor().extract(s, _ctx(32), {"max_dim": 1, "subsample": 64})
    for k in ("n_features_h0", "n_features_h1",
              "mean_lifetime_h0", "mean_lifetime_h1",
              "max_lifetime_h0", "max_lifetime_h1",
              "total_persistence_h0", "total_persistence_h1",
              "persistence_diagram"):
        assert k in out
    assert isinstance(out["persistence_diagram"], list)
    if out["persistence_diagram"]:
        first = out["persistence_diagram"][0]
        assert len(first) == 3


def test_tda_persistence_handles_tiny_matrix():
    # 4x4 with patch_size=3 → only 1 patch → 1 point in 9D → no edges.
    z = np.zeros((4, 4))
    s = Surface(heights=z, width_um=1.0, height_um=1.0, channel="Height", units="m")
    out = TdaPersistenceExtractor().extract(s, _ctx(4), {"max_dim": 1})
    assert out["n_features_h0"] >= 0
