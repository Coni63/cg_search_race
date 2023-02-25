from dataclasses import dataclass


@dataclass
class Action:
    thrust: int
    angle: float  # will be converted to X, Y after
