import json
from typing import Optional

from .checkpoint import CheckPoint
from .pod import Pod
from .action import Action
from .renderer import Renderer


class GameManager:
    def __init__(self, renderer: Optional[Renderer] = None):
        self.data = None
        self.checkpoints = []
        self.pod = None
        self.done = False
        self.reward = 0
        self.renderer = renderer

        if self.renderer is not None:
            self.renderer.start()

    def set_testcase(self, testcase: str):
        with open(testcase, "r") as f:
            self.data = json.load(f)
        self.reset()

        if self.renderer is not None:
            self.render()

        return self.pod, self.checkpoints

    def render(self):  # pragma: no cover
        self.renderer.render(self)
        if self.done:
            self.renderer.end()

    def step(self, action: Action) -> tuple[Pod, float, bool]:
        crossed_chkpt: int = self.pod.applyMove(action=action, checkpoints=self.checkpoints)

        # game is done when the target is the last checkpoint which is a fictive one aligned with the 2 last ones
        self.done = self.pod.nextCheckPointId == len(self.checkpoints) - 1

        current_target = self.checkpoints[self.pod.nextCheckPointId]
        d = self.pod.distance(current_target) - current_target.r
        self.reward = 10_000 - min(10_000, d) + 100_000 * crossed_chkpt

        return self.pod, self.reward, self.done

    def reset(self):
        self.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self._parse_checkpoint()
        start = self.checkpoints[-2]
        self.pod = Pod(x=start.x, y=start.y, vx=0, vy=0, angle=0, nextCheckPointId=0)
        angle = self.pod.getAngle(self.checkpoints[0])
        self.pod.angle = angle
        self.done = False
        self.reward = 0

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
