import glob
from functools import reduce

from ai.AG import Agent
from game import GameManager


def get_hash(checkpoints):
    # remove the last checkpoint as it doesn't exist in real world
    return reduce(lambda a, b: a ^ b, [pt.x*pt.y for pt in checkpoints[:-1]], 0)


def make_simulations(files):
    game = GameManager()
    for file in files:
        game.set_testcase(file)

        agent = Agent()
        output = []
        best_gene = None
        for i in range(600):
            best_gene = agent.evolve(game, initial_individual=best_gene, generation=1000)
            output.append(str(best_gene.moves[0]))
            pod, done = game.apply_action(best_gene.moves[0])
            if done:
                break

        with open(f"output/{file[10:-5]}.txt", "w") as f:
            f.write(";".join(output))


def make_dictionary(files):
    ans = {}
    game = GameManager()
    for file in files:
        game.set_testcase(file)
        signature = get_hash(game.checkpoints)
        with open(f"output/{file[10:-5]}.txt", "r") as f:
            cmd = f.read()
        ans[signature] = cmd
    return ans


if __name__ == "__main__":
    files = glob.glob("testcases/**.json")
    # make_simulations(files)
    d = make_dictionary(files)
    print(d)
