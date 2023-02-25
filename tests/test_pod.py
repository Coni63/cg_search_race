import unittest

from game import Pod, CheckPoint, Action


class TestPod(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_vmax_right(self):
        """
        Only check acceleration and friction
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0, checkPointPassed=0)
        checkpoints = [CheckPoint(x=0, y=1000, r=600)]
        speeds = [170, 314, 436, 540, 629, 704, 768, 822, 868, 907, 940, 969, 993, 1014, 1031, 1046, 1059]

        self.assertEqual(pod.vx, 0)
        self.assertEqual(pod.vy, 0)
        for speed in speeds:
            move = Action(thrust=200, angle=0)
            pod.applyMove(move, checkpoints)
            self.assertEqual(pod.vx, speed)
            self.assertEqual(pod.vy, 0)

    def test_vmax_left(self):
        """
        Pod do a half turn if it's the first turn only.
        After it's 18 deg change max
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0, checkPointPassed=0)
        checkpoints = [CheckPoint(x=0, y=1000, r=600)]

        self.assertEqual(pod.vx, 0)
        self.assertEqual(pod.vy, 0)
        move = Action(thrust=200, angle=180)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 180)
        self.assertEqual(pod.vx, -170)
        self.assertEqual(pod.vy, 0)

    def test_rotation(self):
        """
        Check rotation limits
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0, checkPointPassed=0)
        checkpoints = [CheckPoint(x=0, y=100000, r=600)]

        self.assertEqual(pod.angle, 0)

        move = Action(thrust=200, angle=90)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 90)

        move = Action(thrust=200, angle=30)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 108)

        move = Action(thrust=200, angle=-30)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 90)

        move = Action(thrust=200, angle=-18)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 72)

        move = Action(thrust=200, angle=15)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 87)

    def test_rotation_2(self):
        """
        Check rotation limits
        """
        pod = Pod(x=0, y=0, r=0, vx=5, vy=5, angle=45, nextCheckPointId=0, checkPointPassed=0)
        checkpoints = [CheckPoint(x=0, y=100000, r=600)]

        self.assertEqual(pod.angle, 45)

        move = Action(thrust=200, angle=-30)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 27)

        move = Action(thrust=200, angle=-30)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 9)

        move = Action(thrust=200, angle=-30)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 351)

        move = Action(thrust=200, angle=10)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 1)

        move = Action(thrust=200, angle=-1)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 0)
