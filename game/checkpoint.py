from __future__ import annotations
from dataclasses import dataclass

from .point import Point


@dataclass
class CheckPoint(Point):
    r: float = 600.0
    r2: float = 360000.0
