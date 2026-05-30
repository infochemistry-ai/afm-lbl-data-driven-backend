import numpy as np

from app.features import register_extractor, list_extractors, get_extractor
from app.features.base import ExtractionContext, ScanMetaView


@register_extractor
class _Dummy:
    name = "dummy"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {}

    def extract(self, surface, ctx, params):
        return {"value": float(surface.heights.mean())}


def test_dummy_extractor_is_registered():
    assert "dummy" in list_extractors()
    cls = get_extractor("dummy")
    assert cls.version == "0.1.0"


def test_params_hash_is_stable():
    from app.features.base import params_hash
    assert params_hash({"a": 1, "b": 2}) == params_hash({"b": 2, "a": 1})
    assert params_hash({}) == params_hash({})
    assert params_hash({"a": 1}) != params_hash({"a": 2})
