import glob
from functools import reduce
import json
import random
from ai.AG import Agent, Saver
from game import GameManager, Action, CheckPoint


def get_hash(checkpoints: list[CheckPoint]) -> int:
    # remove the last checkpoint as it doesn't exist in real world
    return reduce(lambda a, b: a ^ b, [pt.x*pt.y for pt in checkpoints[:-1]], 0)


def make_simulation(file: str, **kwargs) -> list[Action]:
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
    game = GameManager()
    game.set_testcase(file)

    for i, action in enumerate(actions):
        pod, done, t = game.apply_action(action)
        if done:
            return i + t
    return 1000


def make_simulations(files, sample=100):
    save_manager = Saver("ai/AG/results.db")
    for file in files:
        for i in range(sample):
            random.seed(None)
            generation = 1500
            seed = random.randint(0, 100000)
            stepsSimulated = random.randint(15, 25)
            actions = make_simulation(file, seed=seed, generation=generation, stepsSimulated=stepsSimulated)
            score = get_score(file, actions)
            seq = ";".join(map(str, actions))
            print(file, seed, stepsSimulated, score)
            save_manager.save(file, seed, stepsSimulated, generation, seq, score)


def make_dictionary(files, only_validator=True):
    ans = {}
    s = Saver("ai/AG/results.db")
    game = GameManager()
    for file in files:
        game.set_testcase(file)

        # skip non validator puzzle to recude dict size
        if only_validator and not game.data["isValidator"]:
            continue

        signature = get_hash(game.checkpoints)
        actions, score = s.get_best(file[10:])
        ans[signature] = actions

    with open("output/sols.txt", "w") as f:
        json.dump(ans, f)


def eval(files, only_validator=True):
    s = Saver("ai/AG/results.db")
    total = 0
    for file in files:
        actions, score = s.get_best(file[10:])
        total += score
        print(file, score)

    print("total", total)


if __name__ == "__main__":
    files = glob.glob("testcases/test10.json")
    make_simulations(files, sample=100)

    # make_dictionary(files)

    # eval(files)
