import numpy as np
from statsmodels.tsa.stattools import acf

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


def _first_zero_crossing(curve_vals: list[float | None]) -> int | None:
    for i in range(1, len(curve_vals)):
        if curve_vals[i] is None or curve_vals[i - 1] is None:
            continue
        if curve_vals[i - 1] >= 0 and curve_vals[i] < 0:
            return i
    return None


def _corr_length(curve_vals: list[float | None]) -> int | None:
    target = 1.0 / np.e
    for i in range(1, len(curve_vals)):
        if curve_vals[i] is None:
            continue
        if curve_vals[i] < target:
            return i
    return None


@register_extractor
class AcfRowColExtractor:
    name = "acf_rowcol"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {"middle_offset": 0}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        offset = int(params.get("middle_offset", self.default_params["middle_offset"]))
        z = np.asarray(surface.heights, dtype=np.float64)
        ny, nx = z.shape
        row_i = max(0, min(ny - 1, ny // 2 + offset))
        col_j = max(0, min(nx - 1, nx // 2 + offset))

        def _compute_acf(series: np.ndarray) -> list[float | None]:
            if series.std() == 0.0:
                return [None] * len(series)
            try:
                values = acf(series, nlags=len(series) - 1, fft=True)
                return [float(v) if np.isfinite(v) else None for v in values]
            except Exception:
                return [None] * len(series)

        acf_x = _compute_acf(z[row_i, :])
        acf_y = _compute_acf(z[:, col_j])

        pixel_size_x_nm = (surface.width_um * 1000.0 / max(nx - 1, 1)) if surface.width_um and nx > 1 else None
        pixel_size_y_nm = (surface.height_um * 1000.0 / max(ny - 1, 1)) if surface.height_um and ny > 1 else None

        x_zero = _first_zero_crossing(acf_x)
        y_zero = _first_zero_crossing(acf_y)
        x_corr = _corr_length(acf_x)
        y_corr = _corr_length(acf_y)

        def _scaled(lag: int | None, px: float | None) -> float | None:
            if lag is None or px is None:
                return None
            return float(lag * px)

        anisotropy = None
        if x_corr is not None and y_corr is not None and y_corr > 0:
            anisotropy = float(x_corr) / float(y_corr)

        return {
            "acf_x_curve": acf_x,
            "acf_y_curve": acf_y,
            "acf_x_first_zero_crossing_nm": _scaled(x_zero, pixel_size_x_nm),
            "acf_y_first_zero_crossing_nm": _scaled(y_zero, pixel_size_y_nm),
            "acf_x_corr_length_nm": _scaled(x_corr, pixel_size_x_nm),
            "acf_y_corr_length_nm": _scaled(y_corr, pixel_size_y_nm),
            "anisotropy_xy_ratio": anisotropy,
        }
