from dataclasses import dataclass


@dataclass
class Action:
    thrust: int
    angle: float  # will be converted to X, Y after

    def __str__(self):
        return f"{self.thrust},{self.angle}"