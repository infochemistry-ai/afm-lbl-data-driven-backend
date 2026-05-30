import re

import numpy as np

from app.parsers import register_parser
from app.parsers.base import Surface

_FLOAT_RE = r"([\d.]+(?:[eE][+-]?\d+)?)"


@register_parser
class TxtParser:
    name = "txt"
    extensions = (".txt",)

    def parse(self, path: str) -> Surface:
        channel: str | None = None
        width_um: float | None = None
        height_um: float | None = None
        units: str | None = None
        data_rows: list[list[float]] = []

        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    body = line.lstrip("#").strip()
                    lower = body.lower()
                    if "channel" in lower or "канал" in lower:
                        channel = body.split(":", 1)[-1].strip()
                    elif "width" in lower or "ширина" in lower:
                        m = re.search(_FLOAT_RE, body)
                        if m:
                            width_um = float(m.group(1))
                    elif "height" in lower or "высота" in lower:
                        m = re.search(_FLOAT_RE, body)
                        if m:
                            height_um = float(m.group(1))
                    elif "unit" in lower or "единиц" in lower:
                        units = body.split(":", 1)[-1].strip()
                    continue
                row = [float(x) for x in line.split()]
                if row:
                    data_rows.append(row)

        if not data_rows:
            raise ValueError(f"No numeric rows found in {path}")
        heights = np.asarray(data_rows, dtype=np.float64)
        return Surface(
            heights=heights,
            width_um=width_um,
            height_um=height_um,
            channel=channel,
            units=units,
        )
