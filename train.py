import glob
import random
from ai.AG import Agent, Saver
from game import GameManager, Action


def make_simulation(file: str, **kwargs) -> list[Action]:
    """
    Run a single iteration of the simulation for a given Agent and testcase.
    """
    game = GameManager()
    game.set_testcase(file)

    agent = Agent(**kwargs)
    output = []
    best_gene = None
    for i in range(600):
        best_gene = agent.evolve(game, initial_individual=best_gene)
        output.append(best_gene.moves[0])  # list of Actions
        pod, done, t = game.apply_action(best_gene.moves[0])
        if done:
            return output


def get_score(file: str, actions: list[Action]) -> float:
    """
    For a given testcase and list of actions, returns the score
    """
    game = GameManager()
    game.set_testcase(file)

    for i, action in enumerate(actions):
        pod, done, t = game.apply_action(action)
        if done:
            return i + t
    return 1000


def make_simulations(files, sample=20, generation=1500, seed=None):
    """
    Run 'sample' simulations for each testcase in 'files'
    The AG run 'generation' generations with a starting seed
    """
    save_manager = Saver("ai/AG/results.db")
    for file in files:
        for i in range(sample):
            random.seed(seed)
            seed = random.randint(0, 100000)
            stepsSimulated = random.randint(15, 25)
            actions = make_simulation(file, seed=seed, generation=generation, stepsSimulated=stepsSimulated)
            score = get_score(file, actions)
            seq = ";".join(map(str, actions))
            print(file, seed, stepsSimulated, score)
            save_manager.save(file, seed, stepsSimulated, generation, seq, score)


if __name__ == "__main__":
    files = glob.glob("testcases/test*.json")
    make_simulations(files)
