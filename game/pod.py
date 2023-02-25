from __future__ import annotations
from dataclasses import dataclass

import sys
import math

from .point import Point
from .checkpoint import CheckPoint
from .action import Action


@dataclass
class Pod(Point):
    r: float
    vx: float
    vy: float
    angle: float
    nextCheckPointId: int
    checkPointPassed: int

    def clone(self) -> 'Pod':
        return Pod(self.x, self.y, self.vx, self.vy, self.angle, self.nextCheckPointId)

    def rotate(self, angle: float) -> None:
        # rotate the pod by angle degrees (positive = clockwise)

        # when the pod is stopped, can rotate as much as it requires
        if self.vx == 0 and self.vy == 0:
            self.angle = angle
            return

        # We can't turn more than 18 degrees in one turn
        self.angle += max(min(angle, 18.0), -18.0)

        # The % operator is slow. If we can avoid it, it's better.
        if self.angle >= 360.0:
            self.angle -= 360.0
        elif self.angle < 0.0:
            self.angle += 360.0

    def boost(self, thrust: float) -> None:
        # Conversion of the angle to radians
        ra = math.radians(self.angle)

        # Trigonometry
        self.vx += math.cos(ra) * thrust
        self.vy += math.sin(ra) * thrust

    def check_cross_checkpoint(self, checkPoints: list[CheckPoint], verbose: bool) -> None:
        chkpt_pos = checkPoints[self.nextCheckPointId]

        if self.has_collision(chkpt_pos, verbose):
            self.checkPointPassed += 1
            self.nextCheckPointId += 1

    def has_collision(self, chkptPos: CheckPoint, verbose: bool = False):
        # si on est a l'arret, pas besoin de verifier
        v2 = self.vx**2 + self.vy**2
        if v2 == 0:
            return False

        # Distance carré entre mon pt de départ et le centre du checkpoint
        dist = self.distance_sq(chkptPos)

        # Somme des rayons au carré
        # On prend tout au carré pour éviter d'avoir à appeler un sqrt inutilement. C'est mieux pour les performances
        # si on commence a l'interieur du checkpoint
        if dist < chkptPos.r2:
            return True

        nextPos = Point(x=self.x + self.vx, y=self.y + self.vy)

        # On cherche le point le plus proche de u (qui est donc en (0,0)) sur la droite décrite par notre vecteur de vitesse
        p = chkptPos.closest(self, nextPos)

        # Distance au carré entre u et le point le plus proche sur la droite décrite par notre vecteur de vitesse
        pdist = chkptPos.distance_sq(p)

        # Si la distance entre u et cette droite est inférieur à la somme des rayons, alors il y a possibilité de collision
        if pdist < chkptPos.r2:
            # on verifie que le point est en amont de la trajectore
            # P1 -> p et P1 -> p2 on un produit scalaire > 0
            # if (p.x - P1.x) * (P2.x - P1.x) + (p.y - P1.y) * (P2.y - P1.y) < 0: return False
            if (p.x - self.x) * self.vx + (p.y - self.y) * self.vy < 0:
                return False

            # Le point d'impact est plus loin que ce qu'on peut parcourir en un seul tour
            pdist = p.distance_sq(self)
            if pdist > v2:
                return False

            # Temps nécessaire pour atteindre le point d'impact
            '''
            if verbose:
                t = pdist / v
                print(f"Simulated Collision Time: {t}", file=sys.stderr)
            '''

            return True

        return False

    def getCollision(self, chkptPos: CheckPoint):
        # Check instant collision
        if self.distance_sq(chkptPos) <= chkptPos.r2:
            return True

        # Change referential
        # Unit u is not at point (0, 0) with a speed vector of (0, 0)
        x2 = self.x - chkptPos.x
        y2 = self.y - chkptPos.y
        v = self.vx * self.vx + self.vy * self.vy

        if v <= 0.0:
            return False

        b = 2.0 * (x2 * self.vx + y2 * self.vy)
        c = x2 * x2 + y2 * y2 - chkptPos.r2
        delta = b * b - 4.0 * v * c

        if delta < 0.0:
            return False

        t = (-b - math.sqrt(delta)) / (2.0 * v)

        if t <= 0.0 or t > 1.0:
            return False

        return True

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def end(self):
        self.x = math.trunc(self.x)
        self.y = math.trunc(self.y)
        self.vx = math.trunc(self.vx * 0.85)
        self.vy = math.trunc(self.vy * 0.85)
        self.angle = round(self.angle)

    def applyMoves(self, actions: list[Action], checkpoints: list[CheckPoint], verbose: bool = False):
        if verbose:
            self.describe()

        for action in actions:
            self.applyMove(action, checkpoints, verbose=verbose)

        if verbose:
            self.describe()

    def applyMove(self, action: Action, checkpoints: list[CheckPoint], verbose: bool = False):
        self.rotate(action.angle)
        self.boost(action.thrust)
        self.check_cross_checkpoint(checkpoints, verbose=verbose)
        self.move()
        self.end()

    def output(self, action: Action):
        next_angle: float = self.angle + action.angle

        if next_angle >= 360.0:
            next_angle -= 360.0
        elif next_angle < 0.0:
            next_angle += 360.0

        # On cherche un point pour correspondre à l'angle qu'on veut
        # On multiplie par 10000.0 pour éviter les arrondis
        next_angle = math.radians(next_angle)
        px = self.x + math.cos(next_angle) * 10000
        py = self.y + math.sin(next_angle) * 10000

        return (round(px), round(py), action.thrust)

    def describe(self):
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

        # Simple trigonometry. We multiply by 180.0 / PI to convert to degrees.
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
