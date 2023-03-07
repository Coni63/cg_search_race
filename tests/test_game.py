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

    def test_simulation_1(self):
        """
        Sur le test 1:
        - run de l'AG sur 30 steps
        - generate output values for CG
        - run this on CG and record pod values
        - simulate the same action on this game
        - compare the pod values after every action

        Ce test est realisé avant un fix sur le cross de chekcpoints resultant a d'autres output et resultats
        Le pod passe a coté du 2eme checkpoint en pensant l'avoir
        """
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
        self.assertTupleEqual((10353, 1986, 0, 0, 161), val)

        # outputs = [(-89586, 5475, 192), (-89823, 246, 200), (-89958, 8968, 179), (-86319, 31243, 200), (-90746, 12527, 200), (-88132, 29717, 200), (-80265, 50756, 175), (-61834, 75598, 200), (-36738, 93398, 200), (-7463, 102462, 0), (23124, 101744, 0), (51947, 91360, 0), (76112, 72367, 51), (93228, 46691, 0), (101531, 16839, 16), (100182, -14237, 31), (89294, -43481, 200), (71314, -66899, 200), (64933, -72795, 120), (77675, -60877, 200), (62709, -75428, 169), (84819, -53305, 200), (99017, -25625, 178), (100560, -22695, 200), (102092, -19722, 199), (105051, 11093, 200), (98342, 41133, 200), (82677, 67474, 167), (59613, 87532, 97), (31421, 99292, 104)]
        actions = [Action(thrust=192, angle=17), Action(thrust=200, angle=3), Action(thrust=179, angle=-5), Action(thrust=200, angle=-13), Action(thrust=200, angle=11), Action(thrust=200, angle=-10), Action(thrust=175, angle=-13), Action(thrust=200, angle=-18), Action(thrust=200, angle=-18), Action(thrust=0, angle=-18), Action(thrust=0, angle=-18), Action(thrust=0, angle=-18), Action(thrust=51, angle=-18), Action(thrust=0, angle=-18), Action(thrust=16, angle=-18), Action(thrust=31, angle=-18), Action(thrust=200, angle=-18), Action(thrust=200, angle=-17), Action(thrust=120, angle=-5), Action(thrust=200, angle=10), Action(thrust=169, angle=-12), Action(thrust=200, angle=18), Action(thrust=178, angle=18), Action(thrust=200, angle=2), Action(thrust=199, angle=2), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=167, angle=18), Action(thrust=97, angle=18), Action(thrust=104, angle=18)]
        target_results = [(10161, 1992, -163, 5, 178), (9798, 1993, -308, 1, 181), (9311, 2006, -413, 11, 176), (8706, 2075, -513, 59, 163), (7994, 2154, -605, 67, 174), (7196, 2276, -677, 103, 164), (6365, 2463, -705, 159, 151), (5523, 2768, -715, 259, 133), (4723, 3208, -679, 374, 115), (4044, 3582, -577, 317, 97), (3467, 3899, -490, 269, 79), (2977, 4168, -416, 228, 61), (2598, 4430, -321, 223, 43), (2277, 4653, -272, 189, 25), (2020, 4843, -217, 162, 7), (1833, 4999, -158, 132, 349), (1849, 5034, 14, 29, 331), (2001, 4919, 129, -97, 314), (2205, 4728, 173, -161, 309), (2528, 4435, 275, -248, 319), (2904, 4052, 320, -325, 307), (3387, 3612, 411, -373, 325), (3968, 3186, 494, -361, 343), (4655, 2773, 584, -350, 345), (5432, 2378, 661, -335, 347), (6292, 2060, 731, -269, 5), (7207, 1869, 777, -162, 23), (8110, 1816, 767, -44, 41), (8926, 1855, 694, 33, 59)]

        for action, end_state in zip(actions, target_results):
            game.apply_action(action)
            val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
            self.assertTupleEqual(val, end_state)

        self.assertEqual(game.pod.nextCheckPointId, 1)

    def test_simulation_2(self):
        """
        Sur le test 1:
        - run de l'AG sur 30 steps
        - generate output values for CG
        - run this on CG and record pod values
        - simulate the same action on this game
        - compare the pod values after every action

        Ce test est realisé apres un fix sur le cross de chekcpoints resultant a d'autres output et resultats
        """
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        outputs = [(-89631, 3731, 175), (-84373, 34545, 148), (-79210, 47438, 105), (-69249, 63694, 200), (-84861, 36529, 195), (-86004, 35118, 191), (-79571, 51304, 200), (-91005, 22222, 198), (-92914, -8736, 130), (-90113, -25541, 0), (-77096, -53452, 53), (-55999, -75812, 68), (-28955, -90431, 0), (1362, -95805, 51), (31925, -91452, 159), (59735, -77890, 200), (82092, -56449, 200), (94980, -34097, 200), (93829, -37698, 200), (102290, -7888, 34), (101948, -13431, 200), (103652, 136, 200), (104144, -3634, 200), (102032, 25540, 200), (90614, 54175, 200), (70943, 77754, 200), (44980, 93993, 0), (23890, 100149, 0), (-1588, 100923, 92), (-29695, 93688, 127)]
        actions = [Action(thrust=175, angle=18), Action(thrust=148, angle=-18), Action(thrust=105, angle=-8), Action(thrust=200, angle=-11), Action(thrust=195, angle=18), Action(thrust=191, angle=1), Action(thrust=200, angle=-10), Action(thrust=198, angle=18), Action(thrust=130, angle=18), Action(thrust=0, angle=10), Action(thrust=53, angle=18), Action(thrust=68, angle=18), Action(thrust=0, angle=18), Action(thrust=51, angle=18), Action(thrust=159, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=15), Action(thrust=200, angle=-2), Action(thrust=34, angle=18), Action(thrust=200, angle=-3), Action(thrust=200, angle=8), Action(thrust=200, angle=-2), Action(thrust=200, angle=17), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=0, angle=18), Action(thrust=0, angle=13), Action(thrust=92, angle=15), Action(thrust=127, angle=17)]
        target_results = [(10178, 1989, -148, 2, 179), (9890, 2039, -244, 42, 161), (9552, 2128, -286, 76, 153), (9108, 2327, -377, 169, 142), (8547, 2562, -476, 200, 160), (7890, 2824, -558, 222, 161), (7157, 3142, -622, 271, 151), (6340, 3450, -693, 262, 169), (5517, 3696, -698, 209, 187), (4819, 3905, -593, 177, 197), (4182, 4051, -540, 124, 215), (3601, 4120, -493, 59, 233), (3108, 4179, -419, 50, 251), (2688, 4178, -356, 0, 269), (2378, 4025, -263, -129, 287), (2229, 3732, -126, -248, 305), (2262, 3363, 28, -313, 323), (2475, 2975, 181, -329, 338), (2838, 2564, 309, -348, 336), (3180, 2212, 291, -298, 354), (3668, 1882, 415, -279, 351), (4282, 1599, 522, -240, 359), (5003, 1348, 613, -212, 357), (5810, 1184, 686, -139, 14), (6665, 1150, 727, -28, 32), (7520, 1275, 727, 106, 50), (8247, 1381, 617, 90, 68), (8864, 1471, 524, 76, 81), (9378, 1638, 437, 142, 96)]

        val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
        self.assertTupleEqual((10353, 1986, 0, 0, 161), val)

        for action, end_state, command_output in zip(actions, target_results, outputs):
            output_pod = game.pod.output(action=action)
            game.apply_action(action)
            val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
            self.assertTupleEqual(command_output, output_pod)
            self.assertTupleEqual(val, end_state)

        self.assertEqual(game.pod.nextCheckPointId, 2)
