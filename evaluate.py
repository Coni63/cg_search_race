import glob
import json
from ai.AG import Saver
from game import GameManager
from utils import get_hash


def make_dictionary(files, only_validator=True) -> dict:
    """
    From all the simulations done, return the best for each validators tests
    Returns a dictionary with the signature of the testcase as key and the encoded actions as value
    """
    ans = {}
    total = 0
    s = Saver("ai/AG/results.db")
    game = GameManager()
    for file in files:
        game.set_testcase(file)

        # skip non validator puzzle to recude dict size
        if only_validator and not game.data["isValidator"]:
            continue

        signature = get_hash(game.checkpoints)
        actions, score = s.get_best(file[10:])
        total += score
        ans[signature] = actions

    print("total", total)


if __name__ == "__main__":
    files = glob.glob("testcases/test*.json")
    data = make_dictionary(files)

    with open("output/sols.txt", "w") as f:
        json.dump(data, f)
