from dataclasses import dataclass


@dataclass
class Action:
    thrust: int
    angle: int

    def __str__(self):
        return f"{self.thrust},{self.angle}"
