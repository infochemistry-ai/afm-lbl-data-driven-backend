from app.features import register_extractor
from app.features.base import ExtractionContext, FeatureValue
from app.parsers.base import Surface


@register_extractor
class MetadataExtractor:
    name = "metadata"
    version = "0.2.0"
    scope = "scan"
    default_params: dict = {}

    def extract(self, surface: Surface, ctx: ExtractionContext, params: dict) -> dict[str, FeatureValue]:
        out: dict[str, FeatureValue] = {
            "pixels_x": surface.pixels_x,
            "pixels_y": surface.pixels_y,
            "width_um": surface.width_um,
            "height_um": surface.height_um,
            "units": surface.units,
            "channel": surface.channel,
        }
        if surface.width_um and surface.pixels_x and surface.pixels_x > 1:
            out["pixel_size_x_nm"] = surface.width_um * 1000.0 / (surface.pixels_x - 1)
        if surface.height_um and surface.pixels_y and surface.pixels_y > 1:
            out["pixel_size_y_nm"] = surface.height_um * 1000.0 / (surface.pixels_y - 1)
        if surface.width_um and surface.height_um:
            out["aspect_ratio"] = surface.width_um / surface.height_um
        return out
