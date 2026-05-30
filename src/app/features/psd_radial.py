import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


@register_extractor
class PsdRadialExtractor:
    name = "psd_radial"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {"bin_count": 64, "fit_range": [0.1, 0.5]}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        bin_count = int(params.get("bin_count", self.default_params["bin_count"]))
        fit_range = params.get("fit_range", self.default_params["fit_range"])
        z = np.asarray(surface.heights, dtype=np.float64)
        z = z - z.mean()
        ny, nx = z.shape

        f = np.fft.fftshift(np.fft.fft2(z))
        psd2 = np.abs(f) ** 2

        cy, cx = ny // 2, nx // 2
        y, x = np.indices(psd2.shape)
        kx = (x - cx) / nx
        ky = (y - cy) / ny
        kr = np.sqrt(kx ** 2 + ky ** 2)
        kr_max = 0.5
        bins = np.linspace(0, kr_max, bin_count + 1)
        idx = np.digitize(kr.ravel(), bins) - 1
        valid = (idx >= 0) & (idx < bin_count)

        psd_radial = np.zeros(bin_count)
        counts = np.zeros(bin_count)
        np.add.at(psd_radial, idx[valid], psd2.ravel()[valid])
        np.add.at(counts, idx[valid], 1)
        psd_radial = psd_radial / np.maximum(counts, 1)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])

        pixel_size_nm = (surface.width_um * 1000.0 / max(nx - 1, 1)) if surface.width_um else None
        q_nm_inv = (bin_centers / pixel_size_nm) if pixel_size_nm else bin_centers

        lo, hi = float(fit_range[0]), float(fit_range[1])
        mask = (bin_centers >= lo * kr_max) & (bin_centers <= hi * kr_max) & (psd_radial > 0)
        if mask.sum() >= 3:
            slope, _ = np.polyfit(np.log(bin_centers[mask]), np.log(psd_radial[mask]), 1)
        else:
            slope = float("nan")

        hurst_H = (-slope - 2.0) / 2.0 if np.isfinite(slope) else None
        fractal_dim_D = (3.0 - hurst_H) if hurst_H is not None else None

        if psd_radial[1:].size and pixel_size_nm:
            i = 1 + int(np.argmax(psd_radial[1:]))
            dominant_q = bin_centers[i] / pixel_size_nm
            dominant_wavelength_nm = 1.0 / dominant_q if dominant_q > 0 else None
        else:
            dominant_wavelength_nm = None

        angles = np.arctan2(ky, kx)
        sector_count = 12
        sectors = np.digitize(angles.ravel(), np.linspace(-np.pi, np.pi, sector_count + 1)) - 1
        sectors = np.clip(sectors, 0, sector_count - 1)
        mid_mask = (kr.ravel() > kr_max * 0.2) & (kr.ravel() < kr_max * 0.6)
        sector_power = np.zeros(sector_count)
        sector_n = np.zeros(sector_count)
        np.add.at(sector_power, sectors[mid_mask], psd2.ravel()[mid_mask])
        np.add.at(sector_n, sectors[mid_mask], 1)
        sector_mean = sector_power / np.maximum(sector_n, 1)
        if sector_mean.mean() > 0:
            anisotropy_index = float(sector_mean.std() / sector_mean.mean())
        else:
            anisotropy_index = None

        return {
            "hurst_H": float(hurst_H) if hurst_H is not None and np.isfinite(hurst_H) else None,
            "fractal_dim_D": float(fractal_dim_D) if fractal_dim_D is not None and np.isfinite(fractal_dim_D) else None,
            "psd_slope_beta": float(slope) if np.isfinite(slope) else None,
            "dominant_wavelength_nm": float(dominant_wavelength_nm) if dominant_wavelength_nm is not None else None,
            "anisotropy_index": anisotropy_index,
            "total_power": float(psd2.sum()),
            "radial_psd_curve": psd_radial.tolist(),
            "radial_psd_q_nm_inv": q_nm_inv.tolist() if pixel_size_nm else None,
        }
