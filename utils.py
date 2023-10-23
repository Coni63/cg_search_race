
from functools import reduce
from game import CheckPoint


def get_hash(checkpoints: list[CheckPoint]) -> int:
    """
    Hash the list of checkpoints to have a unique ID for the testcase
    This is used for the final code to map the action to the environement
    The last checkpoint is not usedas it doesn't exist in the game system
    """
    return reduce(lambda a, b: a ^ b, [pt.x*pt.y for pt in checkpoints[:-1]], 0)
