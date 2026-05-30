from collections import Counter

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue


def _sign_token(sign: int) -> str:
    if sign > 0:
        return "p"
    if sign < 0:
        return "m"
    return "n"


@register_extractor
class PeSequenceKmerExtractor:
    name = "pe_sequence_kmer"
    version = "0.1.0"
    scope = "sample"
    default_params: dict = {"max_k": 3}

    def extract(self, surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        max_k = int(params.get("max_k", self.default_params["max_k"]))
        layers = sorted(ctx.layers, key=lambda layer: layer.position)
        ids = [layer.polyelectrolyte_id for layer in layers]
        n = len(ids)

        out: dict[str, FeatureValue] = {
            "unique_layer_types": len(set(ids)),
        }

        if n == 0:
            out["most_common_layer_id"] = None
            out["most_common_layer_fraction"] = None
            return out

        id_counts = Counter(ids)
        most_common_id, most_common_count = id_counts.most_common(1)[0]
        out["most_common_layer_id"] = most_common_id
        out["most_common_layer_fraction"] = most_common_count / n

        # Layer-id k-grams (only emit nonzero counts).
        for k in range(2, max_k + 1):
            if n < k:
                continue
            grams = Counter(tuple(ids[i:i + k]) for i in range(n - k + 1))
            prefix = "bigram" if k == 2 else ("trigram" if k == 3 else f"{k}gram")
            for gram, c in grams.items():
                key = f"{prefix}_" + "_".join(gram) + "_count"
                out[key] = int(c)

        # Charge n-grams. Layers not in catalog → 'n' (neutral).
        signs = [_sign_token(ctx.polyelectrolytes[i].charge_sign)
                 if i in ctx.polyelectrolytes else "n" for i in ids]
        if n >= 2:
            charge_bigrams = Counter("".join(p) for p in zip(signs, signs[1:]))
            for combo in ("pp", "pm", "mp", "mm"):
                out[f"charge_bigram_{combo}_count"] = int(charge_bigrams.get(combo, 0))
        if n >= 3 and max_k >= 3:
            charge_trigrams = Counter("".join(p) for p in zip(signs, signs[1:], signs[2:]))
            for combo, c in charge_trigrams.items():
                out[f"charge_trigram_{combo}_count"] = int(c)

        return out
