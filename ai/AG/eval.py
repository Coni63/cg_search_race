from __future__ import annotations
from game import Action, GameManager


class Eval:
    moves: list[Action]
    fitness: float = 0

    def __init__(self, moves: list[Action]):
        self.moves = moves
        self.fitness = 0

    @staticmethod
    def from_str(s) -> Eval:
        moves = []
        for sub in s.split(";"):
            thrust, alpha = [int(j) for j in sub.split(",")]
            moves.append(Action(thrust, alpha))
        return Eval(moves)

    def run(self, game: GameManager):
        test_game = game.clone()
        for move in self.moves:
            test_game.apply_action(move)
            self.fitness += self._score(test_game)

    def __repr__(self) -> str:
        s = f"Score: {self.fitness}\n"
        s += ", ". join(f"({action.angle}, {action.thrust})" for action in self.moves)
        return s + "\n\n"

    def _score(self, game: GameManager):
        """
        Score:

        1M de pts par checkpoints
        + un score basé sur la distance au prochain checkpoints (100k points si a 0 de distance)
        + une penalité lorsque le bot n'accelere pas à fond
        """
        chkptPos = game.checkpoints[game.pod.nextCheckPointId]

        history_size = 10
        # entre 0 et 200 but close to 0
        pena_thrust = sum(200-move.thrust for move in self.moves[-history_size:]) / history_size   # entre 0 et 200 but close to 0
        # pena_angle is between 0 and 36
        pena_angle = sum(abs(b.angle-a.angle) for a, b in zip(self.moves[-history_size-1:-1], self.moves[-history_size:])) / history_size

        return (
            game.pod.nextCheckPointId * 100_000
            + max(0, 100_000 - game.pod.distance(chkptPos))
            - pena_thrust * 5
            - pena_angle * 25
        )
