from uuid import uuid4

from app.features.pe_sequence_kmer import PeSequenceKmerExtractor
from app.features.base import ExtractionContext, LayerView, PolyelectrolyteView


def _pe(id_, sign, is_strong=True):
    return PolyelectrolyteView(
        id=id_, charge_sign=sign, charge_group="x", is_strong=is_strong,
        pka=None, monomer_mw_g_mol=100.0, backbone_type="vinyl",
    )


def test_kmer_pei_pss_pei_pss():
    layers = [
        LayerView(position=1, polyelectrolyte_id="PEI"),
        LayerView(position=2, polyelectrolyte_id="PSS"),
        LayerView(position=3, polyelectrolyte_id="PEI"),
        LayerView(position=4, polyelectrolyte_id="PSS"),
    ]
    catalog = {"PEI": _pe("PEI", +1), "PSS": _pe("PSS", -1)}
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=layers,
                            polyelectrolytes=catalog, scan_meta=None)
    out = PeSequenceKmerExtractor().extract(None, ctx, {})
    assert out["bigram_PEI_PSS_count"] == 2
    assert out["bigram_PSS_PEI_count"] == 1
    assert out["trigram_PEI_PSS_PEI_count"] == 1
    assert out["trigram_PSS_PEI_PSS_count"] == 1
    assert out["charge_bigram_pm_count"] == 2
    assert out["charge_bigram_mp_count"] == 1
    assert out["charge_bigram_pp_count"] == 0
    assert out["charge_bigram_mm_count"] == 0
    assert out["unique_layer_types"] == 2
    assert out["most_common_layer_id"] in ("PEI", "PSS")
    assert out["most_common_layer_fraction"] == 0.5


def test_kmer_empty_layers():
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=[],
                            polyelectrolytes={}, scan_meta=None)
    out = PeSequenceKmerExtractor().extract(None, ctx, {})
    assert out["unique_layer_types"] == 0
    assert out["most_common_layer_id"] is None


def test_kmer_only_stores_nonzero_counts():
    layers = [LayerView(position=1, polyelectrolyte_id="PEI")]
    catalog = {"PEI": _pe("PEI", +1)}
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=layers,
                            polyelectrolytes=catalog, scan_meta=None)
    out = PeSequenceKmerExtractor().extract(None, ctx, {})
    bigram_keys = [k for k in out if k.startswith("bigram_")]
    assert bigram_keys == []
