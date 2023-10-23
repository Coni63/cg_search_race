import math
import random

from game import Action, GameManager
from .eval import Eval


class Agent:

    def __init__(self, seed=123, generation=1500, stepsSimulated=18):
        self.population: list[Eval] = []

        self.generation = generation
        self.stepsSimulated: int = stepsSimulated
        self.populationSize: int = 11
        self.selectionSize: int = 1
        self.mutationSize: int = 10
        self.attenuationFactor: float = math.exp(math.log(0.05) / generation)
        self.seed = seed
        random.seed(self.seed)

    def evolve(self, game: GameManager, initial_individual: Eval = None) -> Eval:
        self.initial_game = game

        if initial_individual is None:
            self._init_population()
            gen = self.generation
            amplitude = 1
        else:
            prev_moves = initial_individual.moves
            new_moves = prev_moves[1:] + [self._create_random_step()]
            self.population: list[Eval] = [Eval(new_moves)]
            gen = self.generation // 3
            amplitude = 0.5

        for i in range(gen):
            self._selection()
            # print("generation:", i)
            # print(*self.population, sep="\n")
            self._mutate(amplitude)
            amplitude *= self.attenuationFactor

        return max(self.population, key=lambda x: x.fitness)

    def _selection(self):
        self.population.sort(key=lambda x: -x.fitness)
        self.population = self.population[:self.selectionSize]

    def _mutate(self, amplitude: float):
        def clamp(x: float, lower: float, upper: float):
            return max(min(x, upper), lower)

        # apply the mutation N times from the best element
        list_moves: list[Action] = self.population[0].moves
        for i in range(self.mutationSize):
            new_moves = []
            for action in list_moves:
                if random.random() < 0.3 * (amplitude**0.5):
                    ramin = action.angle - (18 * amplitude)
                    ramax = action.angle + (18 * amplitude)

                    newAngle = random.randint(int(ramin), int(ramax))
                    newAngle = clamp(newAngle, -18, 18)

                    tmin = action.thrust - (100 * amplitude)
                    tmax = action.thrust + (100 * amplitude)

                    newThrust = random.randint(int(tmin), int(tmax))
                    newThrust = clamp(newThrust, 0, 200)

                    new_moves.append(Action(angle=newAngle, thrust=newThrust))
                else:
                    new_moves.append(action)

        self.population.append(self._get_eval_from_moves(new_moves))

    def _init_population(self):
        n = len(self.population)
        for i in range(n, self.populationSize):
            moves: list[Action] = [self._create_random_step() for i in range(self.stepsSimulated)]
            self.population.append(self._get_eval_from_moves(moves))

    def _create_random_step(self) -> Action:
        return Action(thrust=random.randint(0, 200), angle=random.randint(-18, 18))

    def _get_eval_from_moves(self, moves: list[Action]) -> Eval:
        eval: Eval = Eval(moves)
        eval.run(self.initial_game)
        return eval
