import unittest

from game import Pod, CheckPoint, Action


class TestPod(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_apply_moves(self):
        """
        Only check acceleration and friction
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=0, y=1000, r=600)]
        moves = [Action(thrust=200, angle=0) for _ in range(10)]

        self.assertEqual(pod.vx, 0)
        self.assertEqual(pod.vy, 0)
        pod.applyMoves(moves, checkpoints)
        self.assertEqual(pod.vx, 907)
        self.assertEqual(pod.vy, 0)

    def test_vmax_right(self):
        """
        Only check acceleration and friction
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
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
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=0, y=1000, r=600)]

        self.assertEqual(pod.vx, 0)
        self.assertEqual(pod.vy, 0)
        move = Action(thrust=200, angle=180)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.angle, 180)
        self.assertEqual(pod.vx, -170)
        self.assertEqual(pod.vy, 0)

    def test_friction(self):
        pod = Pod(x=0, y=0, r=0, vx=150, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=0, y=1000, r=600)]

        self.assertEqual(pod.vx, 150)
        move = Action(thrust=0, angle=180)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.vx, 127)

    def test_rotation(self):
        """
        Check rotation limits
        """
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
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
        pod = Pod(x=0, y=0, r=0, vx=5, vy=5, angle=45, nextCheckPointId=0)
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

    def test_cross_checkpoint_1(self):
        """
        Case when you are tangent to the circle. 
        In that case, the checkpoint does not count
        """
        pod = Pod(x=0, y=0, r=0, vx=500, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=350, y=600, r=600), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 700)
        self.assertEqual(pod.nextCheckPointId, 0)

    def test_cross_checkpoint_2(self):
        """
        Case when you are inside the circle in the middle of the trajectory
        """
        pod = Pod(x=0, y=0, r=0, vx=500, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=350, y=599, r=600), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 700)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_cross_checkpoint_3(self):
        """
        Case when you are inside the circle at the start of the trajectory
        The id is already incremented to next checkpoint as it will never happen in first frame
        """
        pod = Pod(x=0, y=0, r=0, vx=500, vy=0, angle=0, nextCheckPointId=1)
        checkpoints = [CheckPoint(x=0, y=599, r=600), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 1)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 700)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_cross_checkpoint_4(self):
        """
        Case when you are inside the circle at the start of the trajectory
        """
        pod = Pod(x=0, y=0, r=0, vx=500, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=700, y=599, r=600), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 700)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_cross_checkpoint_5(self):
        """
        Case when you enter exactly aligned with the center of the checkpoint
        """
        pod = Pod(x=150, y=0, r=0, vx=127, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=800, y=0), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 477)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_cross_checkpoint_6(self):
        """
        Case when you cross the checkpoint by the middle point
        """
        pod = Pod(x=150, y=0, r=0, vx=1100, vy=0, angle=0, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=800, y=50), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 1450)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_cross_checkpoint_7(self):
        """
        Case when you cross the checkpoint by the middle point reversed
        """
        pod = Pod(x=1450, y=0, r=0, vx=-1100, vy=0, angle=180, nextCheckPointId=0)
        checkpoints = [CheckPoint(x=800, y=50), CheckPoint(x=0, y=100000, r=600)]

        move = Action(thrust=200, angle=0)
        self.assertEqual(pod.nextCheckPointId, 0)
        pod.applyMove(move, checkpoints)
        self.assertEqual(pod.x, 150)
        self.assertEqual(pod.nextCheckPointId, 1)

    def test_output(self):
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=36, nextCheckPointId=0)
        move = Action(thrust=123, angle=9)

        x, y, thrust = pod.output(move)

        self.assertEqual(x, 7071)
        self.assertEqual(y, 7071)
        self.assertEqual(thrust, 123)

    def test_output_2(self):
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=5, nextCheckPointId=0)
        move = Action(thrust=11, angle=-10)

        x, y, thrust = pod.output(move)

        self.assertEqual(x, 9962)
        self.assertEqual(y, -872)
        self.assertEqual(thrust, 11)

    def test_output_3(self):
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=355, nextCheckPointId=0)
        move = Action(thrust=11, angle=10)

        x, y, thrust = pod.output(move)

        self.assertEqual(x, 9962)
        self.assertEqual(y, 872)
        self.assertEqual(thrust, 11)

    def test_get_angle(self):
        # angle is not considered as it is only the absolute angle from the pod to checkpoint
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0) 

        checkpoint = CheckPoint(x=1000, y=1000, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 45)

        checkpoint = CheckPoint(x=-1000, y=1000, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 135)

        checkpoint = CheckPoint(x=-1000, y=-1000, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 225)

        checkpoint = CheckPoint(x=1000, y=-1000, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 315)

        checkpoint = CheckPoint(x=1000, y=0, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 0)

        pod = Pod(x=500, y=500, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        checkpoint = CheckPoint(x=-1000, y=500, r=600)
        angle = pod.getAngle(checkpoint)
        self.assertAlmostEqual(angle, 180)

    def test_diff_angle(self):
        # angle is not considered as it is only the absolute angle from the pod to checkpoint
        pod = Pod(x=0, y=0, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)

        checkpoint = CheckPoint(x=1000, y=1000, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, 45)

        checkpoint = CheckPoint(x=-1000, y=1000, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, 135)

        checkpoint = CheckPoint(x=-1000, y=-1000, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, -135)

        checkpoint = CheckPoint(x=1000, y=-1000, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, -45)

        checkpoint = CheckPoint(x=1000, y=0, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, 0)

        pod = Pod(x=500, y=500, r=0, vx=0, vy=0, angle=0, nextCheckPointId=0)
        checkpoint = CheckPoint(x=-1000, y=500, r=600)
        angle = pod.diffAngle(checkpoint)
        self.assertAlmostEqual(angle, -180)  # -180 or 180 but -180 is smaller so this is the answer here
