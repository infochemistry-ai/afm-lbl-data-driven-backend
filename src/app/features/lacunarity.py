import ctypes
from pathlib import Path

import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.logging import get_logger
from app.parsers.base import Surface

log = get_logger(__name__)

_LIB_DIR = Path(__file__).parent / "_lacunarity" / "build"
_LIB: ctypes.CDLL | None = None


def _find_lib() -> Path | None:
    for name in ("liblacunarity.so", "liblacunarity.dylib", "lacunarity.dll"):
        cand = _LIB_DIR / name
        if cand.exists():
            return cand
    return None


_lib_path = _find_lib()
if _lib_path is not None:
    try:
        _LIB = ctypes.CDLL(str(_lib_path))
    except OSError as e:
        log.warning("lacunarity_lib_load_failed", path=str(_lib_path), error=repr(e))
        _LIB = None
else:
    log.info(
        "lacunarity_lib_not_built",
        hint="run `python -m app.cli build lacunarity` or rebuild the Docker image",
    )


# Result struct mirrors result.h exactly (field order matters for ctypes).
# Note: z_bgVec / z_bg_len are the last two fields in the C struct.
class _Result(ctypes.Structure):
    _fields_ = [
        ("pressures", ctypes.POINTER(ctypes.c_double)),
        ("pressures_len", ctypes.c_size_t),
        ("derivatives", ctypes.POINTER(ctypes.c_double)),
        ("derivatives_len", ctypes.c_size_t),
        ("holes", ctypes.POINTER(ctypes.c_int)),
        ("holes_len", ctypes.c_size_t),
        ("holes_int", ctypes.POINTER(ctypes.c_int)),
        ("holes_int_len", ctypes.c_size_t),
        ("external_lands", ctypes.POINTER(ctypes.c_int)),
        ("external_lands_len", ctypes.c_size_t),
        ("internal_lands", ctypes.POINTER(ctypes.c_int)),
        ("internal_lands_len", ctypes.c_size_t),
        ("relationship", ctypes.POINTER(ctypes.c_double)),
        ("relationship_len", ctypes.c_size_t),
        ("relationship_derivatives", ctypes.POINTER(ctypes.c_double)),
        ("relationship_derivatives_len", ctypes.c_size_t),
        ("ex_ones_square", ctypes.POINTER(ctypes.c_int)),
        ("ex_ones_square_len", ctypes.c_size_t),
        ("in_ones_square", ctypes.POINTER(ctypes.c_int)),
        ("in_ones_square_len", ctypes.c_size_t),
        ("z_square", ctypes.POINTER(ctypes.c_int)),
        ("z_square_len", ctypes.c_size_t),
        ("half_regressions", ctypes.POINTER(ctypes.c_double)),
        ("half_regressions_len", ctypes.c_size_t),
        ("lambdas", ctypes.POINTER(ctypes.c_double)),
        ("lambdas_len", ctypes.c_size_t),
        # In result.h: int* z_bgVec / size_t z_bg_len  (last two fields)
        ("z_bgVec", ctypes.POINTER(ctypes.c_int)),
        ("z_bg_len", ctypes.c_size_t),
    ]


if _LIB is not None:
    _ND_POINTER_2 = np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags="C_CONTIGUOUS")
    # Actual C signature (7 args):
    # Result lacunarity(double* array, size_t n, size_t p,
    #                   int connectivity, int box, int N, int wait_k)
    _LIB.lacunarity.argtypes = [
        _ND_POINTER_2,
        ctypes.c_size_t,   # n (rows)
        ctypes.c_size_t,   # p (cols)
        ctypes.c_int,      # connectivity
        ctypes.c_int,      # box  (1=box-counting, 2=slide-box)
        ctypes.c_int,      # N   (number_of_slices)
        ctypes.c_int,      # wait_k (visualization delay — pass 0)
    ]
    _LIB.lacunarity.restype = _Result


def _to_list(ptr, n: int) -> list:
    if not ptr or n == 0:
        return []
    arr = np.ctypeslib.as_array(ptr, shape=(n,))
    return arr.copy().tolist()


def _summary_from_curve(curve: list[float]) -> dict[str, float | None]:
    if not curve:
        return {"min": None, "max": None, "mean": None}
    arr = np.asarray(curve, dtype=np.float64)
    return {"min": float(arr.min()), "max": float(arr.max()), "mean": float(arr.mean())}


def _register():
    @register_extractor
    class LacunarityExtractor:
        name = "lacunarity"
        version = "0.1.0"
        scope = "scan"
        default_params: dict = {
            "connectivity": 4,
            "box_counting": 2,
            "number_of_slices": 100,
        }

        def extract(
            self, surface: Surface, ctx: ExtractionContext, params: dict
        ) -> dict[str, FeatureValue]:
            connectivity = int(params.get("connectivity", self.default_params["connectivity"]))
            box_counting = int(params.get("box_counting", self.default_params["box_counting"]))
            n_slices = int(params.get("number_of_slices", self.default_params["number_of_slices"]))

            data = np.ascontiguousarray(surface.heights, dtype=np.float64)
            rows, cols = data.shape
            result = _LIB.lacunarity(
                data,
                rows,
                cols,
                connectivity,
                box_counting,
                n_slices,
                0,  # wait_k — visualization delay; always 0 in headless mode
            )

            lambdas = _to_list(result.lambdas, result.lambdas_len)
            pressures = _to_list(result.pressures, result.pressures_len)
            derivatives = _to_list(result.derivatives, result.derivatives_len)
            holes = _to_list(result.holes, result.holes_len)
            ex_lands = _to_list(result.external_lands, result.external_lands_len)
            in_lands = _to_list(result.internal_lands, result.internal_lands_len)
            relationship = _to_list(result.relationship, result.relationship_len)
            half_reg = _to_list(result.half_regressions, result.half_regressions_len)

            l_summary = _summary_from_curve(lambdas)
            slope = None
            if len(lambdas) >= 3:
                xs = np.arange(1, len(lambdas) + 1, dtype=np.float64)
                ys = np.asarray(lambdas, dtype=np.float64)
                mask = np.isfinite(ys)
                if mask.sum() >= 3:
                    slope = float(np.polyfit(xs[mask], ys[mask], 1)[0])

            return {
                "lambda_at_min_box": float(lambdas[0]) if lambdas else None,
                "lambda_at_max_box": float(lambdas[-1]) if lambdas else None,
                "lambda_mean": l_summary["mean"],
                "lambda_slope_loglog": slope,
                "holes_total": int(sum(holes)) if holes else 0,
                "external_lands_total": int(sum(ex_lands)) if ex_lands else 0,
                "internal_lands_total": int(sum(in_lands)) if in_lands else 0,
                "relationship_mean": float(np.mean(relationship)) if relationship else None,
                "half_regressions_mean": float(np.mean(half_reg)) if half_reg else None,
                "lambda_curve": lambdas,
                "pressures_curve": pressures,
                "derivatives_curve": derivatives,
                "holes_curve": holes,
            }

    return LacunarityExtractor


if _LIB is not None:
    _register()
