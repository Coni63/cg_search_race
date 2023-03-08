from __future__ import annotations

import json

from .checkpoint import CheckPoint
from .pod import Pod
from .action import Action


class GameManager:
    def __init__(self):
        self.data = None
        self.checkpoints = []
        self.pod = None
        self.done = False
        self.turn = 0

    def clone(self) -> GameManager:
        copy = GameManager()
        copy.data = self.data
        copy.checkpoints = self.checkpoints
        copy.pod = self.pod.clone()
        copy.done = self.done
        copy.turn = self.turn
        return copy

    def set_testcase(self, testcase: str):
        with open(testcase, "r") as f:
            self.data = json.load(f)
        self.reset()

        return self.pod, self.checkpoints

    def apply_action(self, action: Action) -> tuple[Pod, bool]:
        t = self.pod.applyMove(action=action, checkpoints=self.checkpoints)
        self.turn += 1

        # game is done when the target is the last checkpoint which is a fictive one aligned with the 2 last ones
        self.done = (self.pod.nextCheckPointId == len(self.checkpoints) - 1) or (self.turn == 600)

        return self.pod, self.done, t

    def apply_actions(self, actions: list[Action]) -> tuple[Pod, bool]:
        for action in actions:
            self.apply_action(action)
            if self.done:
                break

        return self.pod, self.done, None

    def reset(self):
        self.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self._parse_checkpoint()
        start = self.checkpoints[-2]
        self.pod = Pod(x=start.x, y=start.y, vx=0, vy=0, angle=0, nextCheckPointId=0)
        angle = self.pod.getAngle(self.checkpoints[0])
        self.pod.angle = round(angle)
        self.done = False
        self.reward = 0
        self.turn = 0

    def _parse_checkpoint(self):
        all_pts = []
        for s in self.data["testIn"].split(";"):
            x, y = [int(x) for x in s.split(" ")]
            all_pts.append(CheckPoint(x=x, y=y))

        rotated_chkpt = all_pts[1:] + all_pts[:1]

        self.checkpoints = rotated_chkpt * 3

        n_minus2 = self.checkpoints[-2]
        n_minus1 = self.checkpoints[-1]
        dist = n_minus2.distance(n_minus1)
        factor = 30_000 / dist
        last_pt = n_minus1 * (factor+1) - n_minus2 * factor
        self.checkpoints.append(CheckPoint(x=round(last_pt.x), y=round(last_pt.y)))
