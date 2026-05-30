from pathlib import Path

import numpy as np

from app.parsers import register_parser
from app.parsers.base import Surface


@register_parser
class NativeAfmParser:
    name = "native"
    extensions = (".spm", ".ibw", ".sxm")

    def parse(self, path: str) -> Surface:
        ext = Path(path).suffix.lower()
        if ext == ".ibw":
            return self._parse_ibw(path)
        if ext == ".sxm":
            return self._parse_sxm(path)
        if ext == ".spm":
            return self._parse_spm(path)
        raise ValueError(f"Unsupported native extension: {ext}")

    def _parse_ibw(self, path: str) -> Surface:
        import afmformats
        groups = afmformats.load_data(path)
        if not groups:
            raise ValueError(f"No data groups in {path}")
        g = groups[0]
        heights = np.asarray(g["height (measured)"]) if "height (measured)" in g.columns else np.asarray(g.appr["height (measured)"])
        meta = g.metadata
        return Surface(
            heights=heights,
            width_um=float(meta.get("scan range x", 0)) * 1e6 or None,
            height_um=float(meta.get("scan range y", 0)) * 1e6 or None,
            channel="Height",
            units="m",
        )

    def _parse_sxm(self, path: str) -> Surface:
        import pySPM
        scan = pySPM.SXM(path)
        ch = scan.get_channel("Z")
        heights = np.asarray(ch.pixels, dtype=np.float64)
        return Surface(
            heights=heights,
            width_um=float(scan.size["real"]["x"]) * 1e6 if "real" in scan.size else None,
            height_um=float(scan.size["real"]["y"]) * 1e6 if "real" in scan.size else None,
            channel="Z",
            units="m",
        )

    def _parse_spm(self, path: str) -> Surface:
        import pySPM
        scan = pySPM.Bruker(path)
        ch = scan.get_channel("Height Sensor")
        heights = np.asarray(ch.pixels, dtype=np.float64)
        return Surface(
            heights=heights,
            width_um=float(ch.size["real"]["x"]) * 1e6 if hasattr(ch, "size") else None,
            height_um=float(ch.size["real"]["y"]) * 1e6 if hasattr(ch, "size") else None,
            channel="Height Sensor",
            units="m",
        )
