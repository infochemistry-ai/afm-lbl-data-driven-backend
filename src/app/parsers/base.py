from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np


@dataclass(slots=True)
class Surface:
    heights: np.ndarray            # 2D array, shape (pixels_y, pixels_x), values in `units`
    width_um: float | None
    height_um: float | None
    channel: str | None
    units: str | None              # e.g. "m"

    @property
    def pixels_y(self) -> int:
        return int(self.heights.shape[0])

    @property
    def pixels_x(self) -> int:
        return int(self.heights.shape[1])


@runtime_checkable
class Parser(Protocol):
    name: str
    extensions: tuple[str, ...]

    def parse(self, path: str) -> Surface: ...
