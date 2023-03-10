from __future__ import annotations

import sys
import math
from typing import Tuple

from .point import Point
from .checkpoint import CheckPoint
from .action import Action


class Pod(Point):
    vx: float
    vy: float
    angle: float
    nextCheckPointId: int
    r: float

    def __init__(self, x: int, y: int, vx: float = 0.0, vy: float = 0.0, angle: float = 0.0, nextCheckPointId: int = 0, r: int = 0):
        super(Pod, self).__init__(x, y)
        self.vx = vx
        self.vy = vy
        self.angle = angle
        self.nextCheckPointId = nextCheckPointId
        self.r = 0

    @property
    def speed(self):
        return (self.vx * self.vx + self.vy * self.vy) ** 0.5

    def clone(self) -> Pod:
        return Pod(x=self.x, y=self.y, vx=self.vx, vy=self.vy, angle=self.angle, nextCheckPointId=self.nextCheckPointId)

    def applyMoves(self, actions: list[Action], checkpoints: list[CheckPoint], verbose: bool = False) -> int:
        if verbose:
            self.describe()

        cross = 0
        for action in actions:
            self.applyMove(action, checkpoints, verbose=verbose)

        if verbose:
            self.describe()

        return cross

    def applyMove(self, action: Action, checkpoints: list[CheckPoint], verbose: bool = False) -> int:
        self._rotate(action.angle)
        self._boost(action.thrust)
        cross, data = self._check_cross_checkpoint(checkpoints)
        self._move()
        self._end()
        return data

    def output(self, action: Action):
        next_angle: float = self.angle + action.angle

        if next_angle >= 360.0:
            next_angle -= 360.0
        elif next_angle < 0.0:
            next_angle += 360.0

        # On cherche un point pour correspondre à l'angle qu'on veut
        # On multiplie par 10000.0 pour éviter les arrondis
        next_angle = math.radians(next_angle)
        px = self.x + math.cos(next_angle) * 100000
        py = self.y + math.sin(next_angle) * 100000

        # return (round(px), round(py), action.thrust)
        return (math.trunc(px), math.trunc(py), action.thrust)

    def describe(self):  # pragma: no cover
        print("", file=sys.stderr, flush=True)
        print(f"Pod Position       : ({self.x}, {self.y})", file=sys.stderr, flush=True)
        print(f"Pod Speed          : ({self.vx}, {self.vy})", file=sys.stderr, flush=True)
        print(f"Pod Angle          : {self.angle}", file=sys.stderr, flush=True)
        print(f"Pod NextCheckPoint : {self.nextCheckPointId}", file=sys.stderr, flush=True)

    def getAngle(self, p: Point):
        """
        Returns the angle between the pod and point p relative to the X axis
        """
        d = self.distance(p)
        dx = (p.x - self.x) / d
        dy = (p.y - self.y) / d

        a = math.degrees(math.acos(dx))

        # If the point we want is above us, we need to adjust the angle to make it correct.
        if dy < 0:
            return 360 - a
        else:
            return a

    def diffAngle(self, p: Point):
        a = self.getAngle(p)

        # To determine the closest direction, we simply look in both directions and keep the smaller one.
        # Ternary operators are used here to avoid the use of a modulo operator which would be slower.
        right = a - self.angle if self.angle <= a else 360 - self.angle + a
        left = self.angle - a if self.angle >= a else self.angle + 360 - a

        if right < left:
            return right
        else:
            # We return a negative angle if we need to turn left
            return -left

    def _rotate(self, angle: float) -> None:
        # rotate the pod by angle degrees (positive = clockwise)

        # We can't turn more than 18 degrees in one turn
        self.angle += max(min(angle, 18.0), -18.0)

        # The % operator is slow. If we can avoid it, it's better.
        if self.angle >= 360.0:
            self.angle -= 360.0
        elif self.angle < 0.0:
            self.angle += 360.0

    def _boost(self, thrust: float) -> None:
        # Conversion of the angle to radians
        ra = math.radians(self.angle)

        # Trigonometry
        self.vx += math.cos(ra) * thrust
        self.vy += math.sin(ra) * thrust

    def _check_cross_checkpoint(self, checkPoints: list[CheckPoint]) -> Tuple[int, float]:
        chkpt_pos = checkPoints[self.nextCheckPointId]
        t = self._has_collision(chkpt_pos)
        if t != -1:
            self.nextCheckPointId += 1
            return 1, t

        return 0, None

    def _has_collision(self, chkptPos: CheckPoint) -> float:
        """
        Approach used : https://www.youtube.com/watch?v=23kTf-36Fcw
        """
        curr_pos = Point(x=self.x, y=self.y)
        next_pos = Point(x=self.x + self.vx, y=self.y + self.vy)

        # si on est a l'arret, pas besoin de verifier
        if curr_pos == next_pos:
            return -1

        # On cherche le point le plus proche de u (qui est donc en (0,0)) sur la droite décrite par notre vecteur de vitesse
        p = chkptPos.closest(curr_pos, next_pos)

        # Distance au carré entre u et le point le plus proche sur la droite décrite par notre vecteur de vitesse
        b_sq = chkptPos.distance_sq(p)
        # Si la distance entre u et cette droite est inférieur à la somme des rayons, alors il y a possibilité de collision
        if b_sq > chkptPos.r2:
            return -1
        
        # produit scalaire du centre du checkpoint avec la vitesse
        # s'il est negatif c'est que le pt est en arriere de la trajectoire
        d = p - curr_pos
        s = d.x * self.vx + d.y * self.vy
        if s < 0:
            return -1

        a_sq = curr_pos.distance_sq(p)
        if a_sq < 0:
            return -1
        
        f = math.sqrt(chkptPos.r2 - b_sq)
        t = (math.sqrt(a_sq) - f) / (self.vx * self.vx + self.vy * self.vy)**0.5
        
        if t < 0 or t > 1:
            return -1
        
        return t

    def _move(self):
        self.x += self.vx
        self.y += self.vy

    def _end(self):
        self.x = math.trunc(self.x)
        self.y = math.trunc(self.y)
        self.vx = math.trunc(self.vx * 0.85)
        self.vy = math.trunc(self.vy * 0.85)
        self.angle = round(self.angle)
