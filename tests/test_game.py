import unittest

from game import GameManager, CheckPoint, Pod, Action


class TestGame(unittest.TestCase):

    def test_read_tests(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")
        self.assertEqual(len(game.checkpoints), 10)

        pt_final = CheckPoint(6492, -6658)  # checked with geogebra
        self.assertEqual(game.checkpoints[-1], pt_final)
        self.assertEqual(pod.nextCheckPointId, 0)

    def test_step(self):
        game = GameManager()

        # override test_case
        game.checkpoints = [
            CheckPoint(x=800, y=0),
            CheckPoint(x=2200, y=0),
            CheckPoint(x=3600, y=0),  # this checkpoint will not be reach to end the game
        ]
        game.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)

        pod, reward, done = game.step(Action(thrust=150, angle=0))
        self.assertEqual(pod.nextCheckPointId, 0)
        self.assertEqual(reward, 9950)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 1)
        self.assertEqual(reward, 108877)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 1)
        self.assertEqual(reward, 9354)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 1)
        self.assertEqual(reward, 9959)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 2)
        self.assertEqual(reward, 109273)
        self.assertTrue(done)
