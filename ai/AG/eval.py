from game import Action, GameManager


class Eval:
    moves: list[Action]
    fitness: float = 0

    def __init__(self, moves: list[Action]):
        self.moves = moves
        self.fitness = 0

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
        chkptPos = game.checkpoints[game.pod.nextCheckPointId]
        return game.pod.nextCheckPointId * 1000000 + (50000 - game.pod.distance(chkptPos))
