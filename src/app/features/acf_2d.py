import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


@register_extractor
class Acf2dExtractor:
    name = "acf_2d"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {"threshold": 0.367879441}  # 1/e

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        thr = float(params.get("threshold", self.default_params["threshold"]))
        z = np.asarray(surface.heights, dtype=np.float64)
        z = z - z.mean()
        ny, nx = z.shape

        f = np.fft.fft2(z)
        acf = np.real(np.fft.ifft2(np.abs(f) ** 2))
        acf = np.fft.fftshift(acf) / acf.flat[0]

        cy, cx = ny // 2, nx // 2
        y, x = np.indices(acf.shape)
        r = np.sqrt((y - cy) ** 2 + (x - cx) ** 2).astype(int)
        rmax = min(cy, cx)
        sums = np.bincount(r.ravel(), weights=acf.ravel())[:rmax + 1]
        counts = np.maximum(np.bincount(r.ravel())[:rmax + 1], 1)
        radial = sums / counts

        below = np.where(radial < thr)[0]
        corr_px = float(below[0]) if below.size > 0 else float(rmax)

        pixel_size_x_nm = (surface.width_um * 1000.0 / max(surface.pixels_x - 1, 1)) \
            if (surface.width_um and surface.pixels_x and surface.pixels_x > 1) else None

        out: dict[str, FeatureValue] = {
            "correlation_length_px": corr_px,
            "correlation_length_nm": corr_px * pixel_size_x_nm if pixel_size_x_nm else None,
        }

        small = radial[1:min(8, len(radial))]
        if (small > 0).all() and (small < 1).all() and len(small) >= 3:
            lags = np.arange(1, 1 + len(small))
            try:
                slope, _ = np.polyfit(np.log(lags), np.log(1.0 - small), 1)
                out["roughness_exponent_alpha"] = float(slope / 2.0)
            except (ValueError, FloatingPointError):
                out["roughness_exponent_alpha"] = None
        else:
            out["roughness_exponent_alpha"] = None

        return out
