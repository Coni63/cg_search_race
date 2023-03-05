import unittest

from game import GameManager, CheckPoint, Pod, Action


class TestGame(unittest.TestCase):

    def test_start_position(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        self.assertEqual(pod.x, 10353)
        self.assertEqual(pod.y, 1986)
        self.assertEqual(pod.angle, 161)  # round at loading
        self.assertEqual(pod.vx, 0)
        self.assertEqual(pod.vy, 0)
        self.assertEqual(pod.nextCheckPointId, 0)

    def test_checkpoint_list(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")
        target = [
            CheckPoint(2757, 4659),
            CheckPoint(3358, 2838),
            CheckPoint(10353, 1986),
            CheckPoint(2757, 4659),
            CheckPoint(3358, 2838),
            CheckPoint(10353, 1986),
            CheckPoint(2757, 4659),
            CheckPoint(3358, 2838),
            CheckPoint(10353, 1986),
            CheckPoint(40133, -1641)
        ]

        self.assertListEqual(target, checkpoints)

    def test_apply_move(self):
        game = GameManager()

        # override test_case
        game.checkpoints = [
            CheckPoint(x=800, y=0),
            CheckPoint(x=2200, y=0),
            CheckPoint(x=3600, y=0),  # this checkpoint will not be reach to end the game
        ]
        game.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self.assertEqual(game.turn, 0)

        pod, done = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 1)
        self.assertFalse(done)

        for i in range(598):
            pod, done = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 599)
        self.assertFalse(done)

        pod, done = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 600)
        self.assertTrue(done)

    def test_apply_moves(self):
        game = GameManager()

        # override test_case
        game.checkpoints = [
            CheckPoint(x=800, y=0),
            CheckPoint(x=2200, y=0),
            CheckPoint(x=3600, y=0),  # this checkpoint will not be reach to end the game
        ]
        game.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self.assertEqual(game.turn, 0)

        pod, done = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 1)
        self.assertFalse(done)

        actions = [Action(thrust=1, angle=0) for i in range(598)]
        pod, done = game.apply_actions(actions)
        self.assertEqual(game.turn, 599)
        self.assertFalse(done)

        pod, done = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 600)
        self.assertTrue(done)

    def test_clone(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        self.assertEqual(game.pod.x, 10353)
        self.assertEqual(game.pod.y, 1986)
        self.assertAlmostEqual(round(game.pod.angle), 161)

        game.apply_action(Action(thrust=200, angle=0))
        game.pod.describe()
        self.assertEqual(game.pod.x, 10163)
        self.assertEqual(game.pod.y, 2051)

        game2 = game.clone()
        self.assertEqual(game.pod.x, game2.pod.x)
        self.assertEqual(game.pod.y, game2.pod.y)
        self.assertNotEqual(game, game2)

    def test_output(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        