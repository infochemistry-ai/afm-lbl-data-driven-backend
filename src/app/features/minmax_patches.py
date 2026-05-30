import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


@register_extractor
class MinMaxPatchesExtractor:
    name = "minmax_patches"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {"patch_size": 3}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        p = int(params.get("patch_size", self.default_params["patch_size"]))
        z = np.asarray(surface.heights, dtype=np.float64)
        ny, nx = z.shape
        ny_trim = (ny // p) * p
        nx_trim = (nx // p) * p
        if ny_trim == 0 or nx_trim == 0:
            return {"n_patches": 0, "patch_size": p}
        z = z[:ny_trim, :nx_trim]
        n_patches = (ny_trim // p) * (nx_trim // p)

        min_counts = np.zeros((p, p), dtype=np.int64)
        max_counts = np.zeros((p, p), dtype=np.int64)
        for r0 in range(0, ny_trim, p):
            for c0 in range(0, nx_trim, p):
                patch = z[r0:r0 + p, c0:c0 + p]
                mi = np.unravel_index(np.argmin(patch), patch.shape)
                ma = np.unravel_index(np.argmax(patch), patch.shape)
                min_counts[mi] += 1
                max_counts[ma] += 1

        out: dict[str, FeatureValue] = {"n_patches": int(n_patches), "patch_size": p}
        for i in range(p):
            for j in range(p):
                out[f"min_pos_{i}_{j}_frac"] = float(min_counts[i, j]) / n_patches
                out[f"max_pos_{i}_{j}_frac"] = float(max_counts[i, j]) / n_patches
        return out
