
from game import GameManager, Action


class Adapter:

    @staticmethod
    def game_to_state(game: GameManager) -> list[float]:
        chkpt_idx = game.pod.nextCheckPointId
        curr_target, next_target = game.checkpoints[chkpt_idx], game.checkpoints[chkpt_idx+1]
        angle1 = game.pod.diffAngle(curr_target)
        angle2 = game.pod.diffAngle(next_target)
        dist1 = game.pod.distance(curr_target)
        dist2 = game.pod.distance(next_target)
        return [
            game.pod.speed / 1133,
            angle1 / 180,
            dist1 / 10000,
            angle2 / 180,
            dist2 / 10000,
        ]

    @staticmethod
    def prediction_to_action(output: list[float]) -> Action:
        thrust, angle = output
        return Action(
            thrust=round(200 * thrust),
            angle=36 * (angle - 0.5)
        )
