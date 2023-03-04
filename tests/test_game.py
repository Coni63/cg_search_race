import unittest

from game import GameManager, CheckPoint, Pod, Action


class TestGame(unittest.TestCase):

    def test_start_position(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        self.assertEqual(pod.x, 10353)
        self.assertEqual(pod.y, 1986)
        self.assertAlmostEqual(pod.angle, 160.6, places=1)
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

    def test_step(self):
        game = GameManager()

        # override test_case
        game.checkpoints = [
            CheckPoint(x=800, y=0),
            CheckPoint(x=2200, y=0),
            CheckPoint(x=3600, y=0),  # this checkpoint will not be reach to end the game
        ]
        game.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self.assertEqual(game.pod.speed, 0)

        pod, reward, done = game.step(Action(thrust=150, angle=0))
        self.assertEqual(pod.nextCheckPointId, 0)
        self.assertEqual(pod.speed, 127)
        self.assertEqual(reward, 9950)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 1)
        self.assertEqual(pod.speed, 277)
        self.assertEqual(reward, 108877)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=200, angle=0))
        self.assertEqual(pod.nextCheckPointId, 1)
        self.assertEqual(pod.speed, 405)
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

    def test_turn(self):
        game = GameManager()

        # override test_case
        game.checkpoints = [
            CheckPoint(x=800, y=0),
            CheckPoint(x=2200, y=0),
            CheckPoint(x=3600, y=0),  # this checkpoint will not be reach to end the game
        ]
        game.pod = Pod(x=0, y=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        self.assertEqual(game.turn, 0)

        pod, reward, done = game.step(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 1)
        self.assertFalse(done)

        for i in range(598):
            pod, reward, done = game.step(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 599)
        self.assertFalse(done)

        pod, reward, done = game.step(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 600)
        self.assertTrue(done)
