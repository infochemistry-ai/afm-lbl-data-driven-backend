import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


@register_extractor
class DistributionExtractor:
    name = "distribution"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {"bins": 256}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        bins = int(params.get("bins", self.default_params["bins"]))
        z = surface.heights.ravel()
        p = np.percentile(z, [1, 5, 25, 50, 75, 95, 99])
        hist, _ = np.histogram(z, bins=bins)
        probs = hist / hist.sum() if hist.sum() else hist
        nz = probs[probs > 0]
        entropy = float(-np.sum(nz * np.log2(nz))) if nz.size else 0.0
        return {
            "min": float(z.min()),
            "max": float(z.max()),
            "mean": float(z.mean()),
            "median": float(p[3]),
            "std": float(z.std()),
            "P1": float(p[0]),
            "P5": float(p[1]),
            "P25": float(p[2]),
            "P75": float(p[4]),
            "P95": float(p[5]),
            "P99": float(p[6]),
            "IQR": float(p[4] - p[2]),
            "entropy_bits": entropy,
        }
