import json

from .checkpoint import CheckPoint
from .pod import Pod
from .action import Action


class GameManager:
    def __init__(self):
        self.data = None
        self.checkpoints = []
        self.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)

    def set_testcase(self, testcase: str):
        with open(testcase, "r") as f:
            self.data = json.load(f)
        self.reset()

        return self.pod, self.checkpoints

    def step(self, action: Action) -> tuple[Pod, float, bool]:
        # print(self.checkpoints)
        crossed_chkpt: int = self.pod.applyMove(action=action, checkpoints=self.checkpoints)
        # print(crossed_chkpt)

        # game is done when the target is the last checkpoint which is a fictive one aligned with the 2 last ones
        done = self.pod.nextCheckPointId == len(self.checkpoints) - 1

        if done:
            return self.pod, 1_000_000, done

        current_target = self.checkpoints[self.pod.nextCheckPointId]
        d = self.pod.distance(current_target) - current_target.r
        reward = 10_000 - min(10_000, d) + 100_000 * crossed_chkpt

        return self.pod, reward, done

    def reset(self):
        self.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self._parse_checkpoint()

    def _parse_checkpoint(self):
        self.checkpoints = []
        for _ in range(3):  # we have to do 3 turns
            for s in self.data["testIn"].split(";"):
                x, y = [int(x) for x in s.split(" ")]
                self.checkpoints.append(CheckPoint(x=x, y=y))

        n_minus2 = self.checkpoints[-2]
        n_minus1 = self.checkpoints[-1]
        dist = n_minus2.distance(n_minus1)
        factor = 10_000 / dist
        last_pt = n_minus1 * (factor+1) - n_minus2 * factor
        self.checkpoints.append(CheckPoint(x=round(last_pt.x), y=round(last_pt.y)))
