from uuid import uuid4

from app.features.polyelectrolyte import PolyelectrolyteMetaExtractor
from app.features.base import ExtractionContext, LayerView, PolyelectrolyteView


def _pe(id_, sign, is_strong=True):
    return PolyelectrolyteView(
        id=id_, charge_sign=sign, charge_group="x", is_strong=is_strong,
        pka=None, monomer_mw_g_mol=100.0, backbone_type="vinyl",
    )


def test_pei_pss_pei_pss():
    layers = [
        LayerView(position=1, polyelectrolyte_id="PEI", molecular_weight_kda=750),
        LayerView(position=2, polyelectrolyte_id="PSS", molecular_weight_kda=1000),
        LayerView(position=3, polyelectrolyte_id="PEI", molecular_weight_kda=750),
        LayerView(position=4, polyelectrolyte_id="PSS", molecular_weight_kda=1000),
    ]
    catalog = {"PEI": _pe("PEI", +1, is_strong=False), "PSS": _pe("PSS", -1, is_strong=True)}
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=layers, polyelectrolytes=catalog, scan_meta=None)
    out = PolyelectrolyteMetaExtractor().extract(None, ctx, {})
    assert out["n_layers"] == 4
    assert out["n_bilayers"] == 2
    assert out["terminal_layer_id"] == "PSS"
    assert out["first_layer_id"] == "PEI"
    assert out["cation_fraction"] == 0.5
    assert out["charge_alternation_ratio"] == 1.0
    assert out["max_same_charge_run"] == 1
    assert out["n_strong"] == 2
    assert out["n_weak"] == 2


def test_empty_layers():
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=[], polyelectrolytes={}, scan_meta=None)
    out = PolyelectrolyteMetaExtractor().extract(None, ctx, {})
    assert out["n_layers"] == 0
    assert out["terminal_layer_id"] is None
