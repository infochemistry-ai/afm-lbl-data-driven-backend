import numpy as np

from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface

_HEIGHT_PARAMS = ("Sa", "Sq", "Sz", "Sp", "Sv", "Ssk", "Sku")
_HYBRID_PARAMS = ("Sdq", "Sdr")
_SPATIAL_PARAMS = ("Sal", "Str")
_FUNCTIONAL_PARAMS = ("Sk", "Spk", "Svk", "Smr1", "Smr2")
_VOLUME_PARAMS = ("Vmp", "Vmc", "Vvc", "Vvv")


def _try(fn, default=None):
    try:
        return float(fn())
    except Exception:
        return default


@register_extractor
class Iso25178Extractor:
    name = "iso25178"
    version = "0.1.0"
    scope = "scan"
    default_params: dict = {}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        out: dict[str, FeatureValue] = {}
        z = np.asarray(surface.heights, dtype=np.float64)

        mean = z.mean()
        dz = z - mean
        sq = float(np.sqrt((dz ** 2).mean()))
        sa = float(np.mean(np.abs(dz)))
        sp = float(dz.max())
        sv = float(-dz.min())
        sz = sp + sv
        ssk = float(((dz ** 3).mean()) / sq ** 3) if sq > 0 else 0.0
        sku = float(((dz ** 4).mean()) / sq ** 4) if sq > 0 else 0.0
        out.update(Sa=sa, Sq=sq, Sz=sz, Sp=sp, Sv=sv, Ssk=ssk, Sku=sku)

        if surface.width_um and surface.height_um:
            try:
                import surfalize
                step_x = (surface.width_um * 1e-6) / surface.pixels_x
                step_y = (surface.height_um * 1e-6) / surface.pixels_y
                surf = surfalize.Surface(z, step_x=step_x, step_y=step_y)
                for name in (*_HYBRID_PARAMS, *_SPATIAL_PARAMS, *_FUNCTIONAL_PARAMS, *_VOLUME_PARAMS):
                    out[name] = _try(lambda n=name: getattr(surf, n)())
            except Exception:
                for name in (*_HYBRID_PARAMS, *_SPATIAL_PARAMS, *_FUNCTIONAL_PARAMS, *_VOLUME_PARAMS):
                    out.setdefault(name, None)

        return out
