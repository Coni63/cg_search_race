from __future__ import annotations
from dataclasses import dataclass, field

from .point import Point


@dataclass
class CheckPoint(Point):
    r: float = field(repr=False, default=600.0)
    r2: float = field(repr=False, default=360000.0)
