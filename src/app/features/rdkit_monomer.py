import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, GraphDescriptors, Lipinski, rdMolDescriptors

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.logging import get_logger

RDLogger.DisableLog("rdApp.warning")

log = get_logger(__name__)

_DESCRIPTOR_FUNCS = {
    "MolWt": Descriptors.MolWt,
    "MolLogP": Descriptors.MolLogP,
    "TPSA": Descriptors.TPSA,
    "NumHDonors": Lipinski.NumHDonors,
    "NumHAcceptors": Lipinski.NumHAcceptors,
    "NumRotatableBonds": Lipinski.NumRotatableBonds,
    "FractionCSP3": Lipinski.FractionCSP3,
    "NumAromaticRings": Lipinski.NumAromaticRings,
    "BalabanJ": GraphDescriptors.BalabanJ,
    "BertzCT": GraphDescriptors.BertzCT,
    "Chi0": GraphDescriptors.Chi0,
    "Chi1": GraphDescriptors.Chi1,
    "Chi2n": GraphDescriptors.Chi2n,
    "Chi3n": GraphDescriptors.Chi3n,
    "Chi4n": GraphDescriptors.Chi4n,
    "Kappa1": GraphDescriptors.Kappa1,
    "Kappa2": GraphDescriptors.Kappa2,
    "Kappa3": GraphDescriptors.Kappa3,
}


def _safe(fn, mol):
    try:
        v = fn(mol)
        return float(v) if v is not None else None
    except Exception:
        return None


@register_extractor
class RdkitMonomerExtractor:
    name = "rdkit_monomer"
    version = "0.1.0"
    scope = "sample"
    default_params: dict = {"morgan_radius": 2, "morgan_bits": 64}

    def extract(self, surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        morgan_radius = int(params.get("morgan_radius", self.default_params["morgan_radius"]))
        morgan_bits = int(params.get("morgan_bits", self.default_params["morgan_bits"]))
        smiles_overrides: dict[str, str] = params.get("smiles_overrides", {})

        layers = sorted(ctx.layers, key=lambda layer: layer.position)
        valid: list[tuple[int, Chem.Mol]] = []
        for i, layer in enumerate(layers):
            pe = ctx.polyelectrolytes.get(layer.polyelectrolyte_id)
            smi = smiles_overrides.get(layer.polyelectrolyte_id)
            if smi is None and pe is not None:
                smi = pe.monomer_smiles
            if not smi:
                log.info("rdkit_monomer_skip_no_smiles", layer_id=layer.polyelectrolyte_id)
                continue
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                log.warning("rdkit_monomer_bad_smiles", layer_id=layer.polyelectrolyte_id, smiles=smi)
                continue
            valid.append((i, mol))

        out: dict[str, FeatureValue] = {"valid_layers": len(valid)}
        if not valid:
            return out

        per_layer: dict[str, list[float]] = {name: [] for name in _DESCRIPTOR_FUNCS}
        for _, mol in valid:
            for name, fn in _DESCRIPTOR_FUNCS.items():
                v = _safe(fn, mol)
                if v is not None and np.isfinite(v):
                    per_layer[name].append(v)

        for name, values in per_layer.items():
            if not values:
                continue
            arr = np.asarray(values, dtype=np.float64)
            out[f"{name}_mean"] = float(arr.mean())
            out[f"{name}_std"] = float(arr.std()) if len(arr) > 1 else 0.0

        first_mol = valid[0][1]
        last_mol = valid[-1][1]
        for name, fn in _DESCRIPTOR_FUNCS.items():
            fv = _safe(fn, first_mol)
            lv = _safe(fn, last_mol)
            if fv is not None and np.isfinite(fv):
                out[f"{name}_first"] = float(fv)
            if lv is not None and np.isfinite(lv):
                out[f"{name}_terminal"] = float(lv)

        try:
            fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(last_mol, morgan_radius, nBits=morgan_bits)
            for bit_idx in range(morgan_bits):
                out[f"morgan_bit_{bit_idx}_terminal"] = int(fp.GetBit(bit_idx))
        except Exception as e:
            log.warning("rdkit_monomer_morgan_failed", error=repr(e))

        return out
