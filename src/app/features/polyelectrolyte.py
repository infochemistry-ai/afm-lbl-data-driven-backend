import math

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue


@register_extractor
class PolyelectrolyteMetaExtractor:
    name = "polyelectrolyte_meta"
    version = "0.1.0"
    scope = "sample"
    default_params: dict = {}

    def extract(self, surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        layers = sorted(ctx.layers, key=lambda l: l.position)
        n = len(layers)
        out: dict[str, FeatureValue] = {
            "n_layers": n,
            "n_bilayers": n // 2,
            "terminal_layer_id": layers[-1].polyelectrolyte_id if layers else None,
            "first_layer_id": layers[0].polyelectrolyte_id if layers else None,
        }
        if n == 0:
            for k in ("cation_fraction", "anion_fraction", "neutral_fraction",
                     "charge_alternation_ratio", "max_same_charge_run",
                     "log_mw_avg", "log_mw_terminal", "n_strong", "n_weak"):
                out[k] = None
            return out

        signs = [ctx.polyelectrolytes[l.polyelectrolyte_id].charge_sign for l in layers]
        is_strong = [ctx.polyelectrolytes[l.polyelectrolyte_id].is_strong for l in layers]
        out["cation_fraction"] = sum(1 for s in signs if s > 0) / n
        out["anion_fraction"] = sum(1 for s in signs if s < 0) / n
        out["neutral_fraction"] = sum(1 for s in signs if s == 0) / n
        out["n_strong"] = sum(1 for x in is_strong if x)
        out["n_weak"] = sum(1 for x in is_strong if not x)

        if n >= 2:
            alternations = sum(1 for a, b in zip(signs, signs[1:]) if a * b < 0)
            out["charge_alternation_ratio"] = alternations / (n - 1)
            run = best = 1
            for a, b in zip(signs, signs[1:]):
                if a == b:
                    run += 1; best = max(best, run)
                else:
                    run = 1
            out["max_same_charge_run"] = best
        else:
            out["charge_alternation_ratio"] = None
            out["max_same_charge_run"] = 1

        mws = [l.molecular_weight_kda for l in layers if l.molecular_weight_kda]
        out["log_mw_avg"] = float(math.log10(sum(mws) / len(mws))) if mws else None
        mw_term = layers[-1].molecular_weight_kda
        out["log_mw_terminal"] = float(math.log10(mw_term)) if mw_term else None
        return out
