import math

import gudhi
import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


def _extract_patches(z: np.ndarray, p: int) -> np.ndarray:
    ny, nx = z.shape
    ny_t = (ny // p) * p
    nx_t = (nx // p) * p
    if ny_t == 0 or nx_t == 0:
        return np.empty((0, p * p), dtype=np.float64)
    z = z[:ny_t, :nx_t]
    patches = []
    for r0 in range(0, ny_t, p):
        for c0 in range(0, nx_t, p):
            patches.append(z[r0:r0 + p, c0:c0 + p].ravel())
    return np.asarray(patches, dtype=np.float64)


@register_extractor
class TdaPersistenceExtractor:
    name = "tda_persistence"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {
        "patch_size": 3,
        "max_dim": 2,
        "max_edge_length": None,
        "subsample": 2000,
        "seed": 42,
    }

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        p = int(params.get("patch_size", self.default_params["patch_size"]))
        max_dim = int(params.get("max_dim", self.default_params["max_dim"]))
        edge_param = params.get("max_edge_length", self.default_params["max_edge_length"])
        subsample = int(params.get("subsample", self.default_params["subsample"]))
        seed = int(params.get("seed", self.default_params["seed"]))

        z = np.asarray(surface.heights, dtype=np.float64)
        points = _extract_patches(z, p)
        if points.shape[0] == 0:
            base: dict[str, FeatureValue] = {
                "persistence_diagram": [], "n_points": 0,
            }
            for d in range(max_dim + 1):
                base[f"n_features_h{d}"] = 0
                base[f"mean_lifetime_h{d}"] = None
                base[f"max_lifetime_h{d}"] = None
                base[f"total_persistence_h{d}"] = 0.0
            return base

        if points.shape[0] > subsample:
            rng = np.random.default_rng(seed)
            idx = rng.choice(points.shape[0], size=subsample, replace=False)
            points = points[idx]

        if edge_param is None:
            if points.shape[0] >= 2:
                from scipy.spatial.distance import pdist
                d = pdist(points)
                edge = float(np.median(d)) * 0.5 if d.size else 1.0
            else:
                edge = 1.0
        else:
            edge = float(edge_param)

        rips = gudhi.RipsComplex(points=points, max_edge_length=edge)
        st = rips.create_simplex_tree(max_dimension=max_dim + 1)
        diag = st.persistence(min_persistence=0)

        diagram_records: list[list[float]] = []
        per_dim: dict[int, list[float]] = {d: [] for d in range(max_dim + 1)}
        for dim, (birth, death) in diag:
            if dim > max_dim:
                continue
            if death == math.inf:
                death = edge  # cap infinite features at the filtration ceiling
            life = death - birth
            diagram_records.append([float(birth), float(death), int(dim)])
            per_dim.setdefault(dim, []).append(life)

        out: dict[str, FeatureValue] = {
            "persistence_diagram": diagram_records,
            "n_points": int(points.shape[0]),
            "max_edge_length_used": edge,
        }
        for d in range(max_dim + 1):
            lives = per_dim.get(d, [])
            out[f"n_features_h{d}"] = len(lives)
            out[f"mean_lifetime_h{d}"] = float(np.mean(lives)) if lives else None
            out[f"max_lifetime_h{d}"] = float(np.max(lives)) if lives else None
            out[f"total_persistence_h{d}"] = float(np.sum(lives)) if lives else 0.0
        return out
