from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int

    def distance(self, other: Point) -> float:
        return self.distance_sq(other) ** 0.5

    def distance_sq(self, other: Point) -> float:
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float | int) -> Point:
        return Point(self.x * scalar, self.y * scalar)

    def __eq__(self, other: Point) -> bool:
        return self.x == other.x and self.y == other.y

    def closest(self, a: Point, b: Point) -> Point:
        """
        http://files.magusgeek.com/csb/csb.html
        Elle permet de trouver le point le plus proche sur une droite
        (décrite ici par 2 points) depuis un point.
               x
               |
        a---------b
               ^
               pt
        """
        da = b.y - a.y
        db = a.x - b.x
        c1 = da*a.x + db*a.y
        c2 = -db * self.x + da * self.y
        det = da*da + db*db

        if det != 0:
            cx = (da*c1 - db*c2) / det
            cy = (da*c2 + db*c1) / det
        else:
            # Le point est déjà sur la droite
            cx = self.x
            cy = self.y

        return Point(cx, cy)

    def norm_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def norm(self) -> float:
        return self.norm_sq() ** 0.5
