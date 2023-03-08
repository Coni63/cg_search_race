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

        pod, done, t = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 1)
        self.assertFalse(done)

        for i in range(598):
            pod, done, t = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 599)
        self.assertFalse(done)

        pod, done, t = game.apply_action(Action(thrust=1, angle=0))
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

        pod, done, t = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 1)
        self.assertFalse(done)

        actions = [Action(thrust=1, angle=0) for i in range(598)]
        pod, done, t = game.apply_actions(actions)
        self.assertEqual(game.turn, 599)
        self.assertFalse(done)

        pod, done, t = game.apply_action(Action(thrust=1, angle=0))
        self.assertEqual(game.turn, 600)
        self.assertTrue(done)

    def test_clone(self):
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        self.assertEqual(game.pod.x, 10353)
        self.assertEqual(game.pod.y, 1986)
        self.assertAlmostEqual(round(game.pod.angle), 161)

        game.apply_action(Action(thrust=200, angle=0))
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

        for i, (action, end_state) in enumerate(zip(actions, target_results)):
            pod, done, t = game.apply_action(action)
            val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
            self.assertTupleEqual(val, end_state)
            if i == 11:
                self.assertAlmostEqual(t, 0.8648988427501346, places=5)
            else:
                self.assertIsNone(t)

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
        Les temps de crosscheckpoints sont aussi controlées
        """
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test1.json")

        outputs = [(-89631, 3731, 175), (-84373, 34545, 148), (-79210, 47438, 105), (-69249, 63694, 200), (-84861, 36529, 195), (-86004, 35118, 191), (-79571, 51304, 200), (-91005, 22222, 198), (-92914, -8736, 130), (-90113, -25541, 0), (-77096, -53452, 53), (-55999, -75812, 68), (-28955, -90431, 0), (1362, -95805, 51), (31925, -91452, 159), (59735, -77890, 200), (82092, -56449, 200), (94980, -34097, 200), (93829, -37698, 200), (102290, -7888, 34), (101948, -13431, 200), (103652, 136, 200), (104144, -3634, 200), (102032, 25540, 200), (90614, 54175, 200), (70943, 77754, 200), (44980, 93993, 0), (23890, 100149, 0), (-1588, 100923, 92), (-29695, 93688, 127)]
        actions = [Action(thrust=175, angle=18), Action(thrust=148, angle=-18), Action(thrust=105, angle=-8), Action(thrust=200, angle=-11), Action(thrust=195, angle=18), Action(thrust=191, angle=1), Action(thrust=200, angle=-10), Action(thrust=198, angle=18), Action(thrust=130, angle=18), Action(thrust=0, angle=10), Action(thrust=53, angle=18), Action(thrust=68, angle=18), Action(thrust=0, angle=18), Action(thrust=51, angle=18), Action(thrust=159, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=15), Action(thrust=200, angle=-2), Action(thrust=34, angle=18), Action(thrust=200, angle=-3), Action(thrust=200, angle=8), Action(thrust=200, angle=-2), Action(thrust=200, angle=17), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=0, angle=18), Action(thrust=0, angle=13), Action(thrust=92, angle=15), Action(thrust=127, angle=17)]
        target_results = [(10178, 1989, -148, 2, 179), (9890, 2039, -244, 42, 161), (9552, 2128, -286, 76, 153), (9108, 2327, -377, 169, 142), (8547, 2562, -476, 200, 160), (7890, 2824, -558, 222, 161), (7157, 3142, -622, 271, 151), (6340, 3450, -693, 262, 169), (5517, 3696, -698, 209, 187), (4819, 3905, -593, 177, 197), (4182, 4051, -540, 124, 215), (3601, 4120, -493, 59, 233), (3108, 4179, -419, 50, 251), (2688, 4178, -356, 0, 269), (2378, 4025, -263, -129, 287), (2229, 3732, -126, -248, 305), (2262, 3363, 28, -313, 323), (2475, 2975, 181, -329, 338), (2838, 2564, 309, -348, 336), (3180, 2212, 291, -298, 354), (3668, 1882, 415, -279, 351), (4282, 1599, 522, -240, 359), (5003, 1348, 613, -212, 357), (5810, 1184, 686, -139, 14), (6665, 1150, 727, -28, 32), (7520, 1275, 727, 106, 50), (8247, 1381, 617, 90, 68), (8864, 1471, 524, 76, 81), (9378, 1638, 437, 142, 96)]

        val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
        self.assertTupleEqual((10353, 1986, 0, 0, 161), val)

        for i, (action, end_state, command_output) in enumerate(zip(actions, target_results, outputs)):
            output_pod = game.pod.output(action=action)
            pod, done, t = game.apply_action(action)
            val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
            self.assertTupleEqual(command_output, output_pod)
            self.assertTupleEqual(val, end_state)
            if i == 12:
                self.assertAlmostEqual(t, 0.9842623982679378, places=5)
            elif i == 18:
                self.assertAlmostEqual(t, 0.9130163339764782, places=5)
            else:
                self.assertIsNone(t)

        self.assertEqual(game.pod.nextCheckPointId, 2)

    def test_simulation_3(self):
        """
        Sur le test Round and Round:
        - run de l'AG sur 30 steps
        - generate output values for CG
        - run this on CG and record pod values
        - simulate the same action on this game
        - compare the pod values after every action

        Ce test est realisé apres un fix sur le cross de chekcpoints resultant a d'autres output et resultats
        Les temps de crosscheckpoints sont aussi controlées
        """
        game = GameManager()
        pod, checkpoints = game.set_testcase("testcases/test701.json")

        outputs = [(31080, 99162, 200), (60518, 88657, 200), (36358, 98565, 190), (26237, 101035, 200), (-4886, 101089, 200), (-34369, 91609, 200), (-59364, 73556, 144), (-77421, 48688, 176), (-86820, 19491, 200), (-86686, -11149, 200), (-77046, -40222, 200), (-58858, -64869, 194), (-33909, -82667, 200), (-4653, -91868, 200), (-5245, -92112, 200), (25505, -91971, 200), (54671, -82325, 200), (57464, -81268, 171), (64686, -77269, 198), (85042, -59033, 144), (99489, -35899, 168), (102793, -28408, 174), (108065, 1861, 109), (103599, 32225, 200), (89949, 59707, 200), (68458, 81612, 200), (42890, 95239, 200), (23141, 100113, 200), (2790, 100821, 137), (-27111, 93679, 200), (-11922, 99205, 187), (-16751, 98452, 62), (-44706, 85345, 200), (-62794, 69715, 182), (-71308, 59270, 159), (-84265, 31366, 115), (-87965, 4344, 200), (-82993, -25956, 200), (-68886, -53214, 200), (-55281, -68312, 169), (-34178, -82687, 200), (-4911, -91985, 200), (13657, -93148, 200), (23583, -92531, 200), (43396, -87724, 200), (70241, -72779, 200), (79155, -65279, 200), (93008, -48092, 180), (104943, -19835, 165), (107467, 10699, 200), (100388, 40501, 193), (84401, 66636, 200), (75190, 76295, 200), (49345, 92851, 200), (19649, 100585, 190), (-10983, 98732, 200), (-7122, 99930, 200), (-36182, 89827, 174), (-40489, 87830, 185), (-64028, 68021, 149), (-70379, 60367, 200), (-83811, 32721, 169), (-88009, 7553, 142), (-84085, -22875, 200), (-73816, -46217, 200), (-53932, -69586, 200), (-31001, -84283, 200), (-15174, -90096, 200), (13647, -93241, 200), (30407, -91280, 200), (59033, -80148, 200), (52709, -84204, 200), (77924, -66563, 200), (96375, -42029, 200), (106273, -13023, 200), (107151, 14137, 200), (102979, 33963, 200), (92935, 55473, 200), (106371, 26662, 200), (107168, 26520, 200), (111385, 4059, 200)]
        actions = [Action(thrust=200, angle=7), Action(thrust=200, angle=-18), Action(thrust=190, angle=15), Action(thrust=200, angle=6), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=144, angle=18), Action(thrust=176, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=194, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=0), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=171, angle=2), Action(thrust=198, angle=5), Action(thrust=144, angle=16), Action(thrust=168, angle=16), Action(thrust=174, angle=5), Action(thrust=109, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=17), Action(thrust=200, angle=12), Action(thrust=137, angle=12), Action(thrust=200, angle=18), Action(thrust=187, angle=-9), Action(thrust=62, angle=3), Action(thrust=200, angle=18), Action(thrust=182, angle=14), Action(thrust=159, angle=8), Action(thrust=115, angle=18), Action(thrust=200, angle=16), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=169, angle=12), Action(thrust=200, angle=15), Action(thrust=200, angle=18), Action(thrust=200, angle=11), Action(thrust=200, angle=6), Action(thrust=200, angle=12), Action(thrust=200, angle=18), Action(thrust=200, angle=7), Action(thrust=180, angle=13), Action(thrust=165, angle=18), Action(thrust=200, angle=18), Action(thrust=193, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=8), Action(thrust=200, angle=18), Action(thrust=190, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=-2), Action(thrust=174, angle=18), Action(thrust=185, angle=3), Action(thrust=149, angle=18), Action(thrust=200, angle=6), Action(thrust=169, angle=18), Action(thrust=142, angle=15), Action(thrust=200, angle=18), Action(thrust=200, angle=15), Action(thrust=200, angle=18), Action(thrust=200, angle=16), Action(thrust=200, angle=10), Action(thrust=200, angle=17), Action(thrust=200, angle=10), Action(thrust=200, angle=18), Action(thrust=200, angle=-4), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=18), Action(thrust=200, angle=16), Action(thrust=200, angle=12), Action(thrust=200, angle=14), Action(thrust=200, angle=-18), Action(thrust=200, angle=0), Action(thrust=200, angle=-13)]
        target_results = [(12038, 1196, 32, 166, 79, 0), (12166, 1536, 109, 289, 61, 0), (12320, 2009, 131, 402, 76, 1), (12478, 2609, 135, 510, 82, 1), (12578, 3315, 85, 600, 100, 1), (12569, 4091, -7, 660, 118, 1), (12458, 4851, -93, 646, 136, 1), (12206, 5574, -213, 614, 154, 2), (11794, 6215, -349, 545, 172, 2), (11248, 6725, -464, 433, 190, 2), (10607, 7064, -544, 288, 208, 2), (9928, 7212, -576, 126, 226, 2), (9264, 7158, -564, -45, 244, 2), (8672, 6914, -503, -206, 262, 2), (8141, 6509, -451, -343, 262, 2), (7724, 5969, -353, -458, 280, 2), (7464, 5334, -220, -539, 298, 2), (7329, 4646, -114, -584, 300, 2), (7328, 3899, 0, -634, 305, 2), (7439, 3174, 95, -615, 321, 2), (7688, 2493, 212, -578, 337, 2), (8065, 1861, 320, -537, 342, 2), (8494, 1324, 364, -456, 0, 2), (9048, 929, 471, -335, 18, 2), (9680, 711, 537, -184, 36, 2), (10334, 688, 556, -18, 54, 2), (10955, 859, 527, 145, 71, 2), (11506, 1202, 468, 291, 83, 2), (11962, 1629, 387, 363, 95, 2), (12270, 2176, 262, 465, 113, 2), (12486, 2822, 184, 549, 104, 2), (12651, 3430, 140, 517, 107, 2), (12676, 4110, 21, 578, 125, 2), (12559, 4807, -98, 592, 139, 2), (12327, 5485, -196, 576, 147, 2), (12019, 6090, -261, 514, 165, 2), (11558, 6600, -391, 433, 181, 3), (10977, 6967, -493, 312, 199, 3), (10324, 7158, -554, 162, 217, 3), (9659, 7192, -565, 29, 229, 3), (9006, 7041, -554, -128, 244, 3), (8424, 6714, -494, -277, 262, 4), (7940, 6237, -411, -405, 273, 4), (7560, 5634, -322, -512, 279, 5), (7309, 4935, -212, -593, 291, 5), (7222, 4186, -73, -636, 309, 5), (7292, 3411, 60, -658, 316, 5), (7506, 2660, 182, -638, 329, 6), (7848, 1984, 291, -573, 347, 6), (8338, 1428, 416, -472, 5, 7), (8931, 1031, 504, -337, 23, 7), (9585, 825, 556, -174, 41, 7), (10272, 801, 584, -19, 49, 7), (10934, 966, 562, 140, 67, 7), (11512, 1295, 491, 279, 85, 8), (11958, 1768, 379, 402, 103, 8), (12298, 2366, 289, 508, 101, 9), (12502, 3026, 173, 561, 119, 9), (12576, 3743, 63, 610, 122, 9), (12524, 4448, -43, 599, 140, 9), (12315, 5158, -177, 604, 146, 10), (11975, 5808, -288, 552, 164, 10), (11545, 6362, -365, 471, 179, 10), (10988, 6774, -472, 350, 197, 10), (10346, 7018, -545, 207, 212, 10), (9672, 7071, -572, 45, 230, 10), (9018, 6933, -555, -117, 246, 10), (8414, 6621, -512, -264, 256, 10), (7912, 6157, -426, -394, 273, 10), (7530, 5568, -323, -500, 283, 10), (7310, 4896, -186, -570, 301, 10), (7214, 4147, -80, -635, 297, 10), (7275, 3370, 52, -659, 315, 10), (7505, 2620, 195, -637, 333, 10), (7897, 1951, 333, -568, 351, 10), (8428, 1407, 451, -462, 7, 10), (9068, 1010, 544, -337, 19, 10), (9779, 781, 604, -193, 33, 10), (10576, 639, 677, -120, 15, 10), (11446, 570, 739, -58, 15, 10)]

        val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle)
        self.assertTupleEqual((12000, 1000, 0, 0, 72), val)

        for i, (action, end_state, command_output) in enumerate(zip(actions, target_results, outputs)):
            output_pod = game.pod.output(action=action)
            self.assertTupleEqual(command_output, output_pod)

            pod, done, t = game.apply_action(action)
            val = (game.pod.x, game.pod.y, game.pod.vx, game.pod.vy, game.pod.angle, game.pod.nextCheckPointId)
            self.assertTupleEqual(val, end_state)

        self.assertEqual(game.pod.nextCheckPointId, 10)
