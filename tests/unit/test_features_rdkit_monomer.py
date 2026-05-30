from uuid import uuid4

from app.features.rdkit_monomer import RdkitMonomerExtractor
from app.features.base import ExtractionContext, LayerView, PolyelectrolyteView


def test_rdkit_returns_descriptors_for_pei_pss():
    catalog = {
        "PEI": PolyelectrolyteView(id="PEI", charge_sign=1, charge_group="primary_amine",
                                    is_strong=False, pka=7.0, monomer_mw_g_mol=43.07,
                                    backbone_type="vinyl"),
        "PSS": PolyelectrolyteView(id="PSS", charge_sign=-1, charge_group="sulfonate",
                                    is_strong=True, pka=None, monomer_mw_g_mol=206.19,
                                    backbone_type="vinyl"),
    }
    layers = [
        LayerView(position=1, polyelectrolyte_id="PEI"),
        LayerView(position=2, polyelectrolyte_id="PSS"),
    ]
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=layers,
                            polyelectrolytes=catalog, scan_meta=None)
    out = RdkitMonomerExtractor().extract(
        None, ctx, {"smiles_overrides": {"PEI": "NCC", "PSS": "CC(c1ccc(cc1)S(=O)(=O)[O-])"}}
    )
    assert "MolWt_mean" in out
    assert "MolWt_terminal" in out
    assert out["valid_layers"] == 2
    assert out["MolWt_terminal"] > out["MolWt_first"]


def test_rdkit_skips_missing_smiles_with_warning():
    catalog = {
        "MXene": PolyelectrolyteView(id="MXene", charge_sign=-1, charge_group="oxide",
                                      is_strong=False, pka=None, monomer_mw_g_mol=0.0,
                                      backbone_type="inorganic_flake"),
    }
    layers = [LayerView(position=1, polyelectrolyte_id="MXene")]
    ctx = ExtractionContext(sample_id=uuid4(), scan_id=None, layers=layers,
                            polyelectrolytes=catalog, scan_meta=None)
    out = RdkitMonomerExtractor().extract(None, ctx, {"smiles_overrides": {"MXene": ""}})
    assert out["valid_layers"] == 0
    assert not any(k.endswith("_mean") for k in out)
