import unittest

from game import Point


class TestPod(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_distance(self):
        a = Point(x=0, y=0)
        b = Point(x=3, y=4)
        c = Point(x=-3, y=-4)

        self.assertEqual(a.distance(b), 5)

        # cehck both directions
        self.assertEqual(c.distance(b), 10)
        self.assertEqual(b.distance(c), 10)

    def test_distance_sq(self):
        a = Point(x=0, y=0)
        b = Point(x=-3, y=-4)

        self.assertEqual(a.distance_sq(b), 25)

    def test_closest_distance(self):
        a = Point(x=0, y=0)
        b = Point(x=10, y=0)

        # normal case
        c = Point(x=3, y=1)
        p1 = Point(x=3, y=0)
        self.assertEqual(c.closest(a, b), p1)

        # before of after points
        c = Point(x=-3, y=1)
        p1 = Point(x=-3, y=0)
        self.assertEqual(c.closest(a, b), p1)

        c = Point(x=30, y=1)
        p1 = Point(x=30, y=0)
        self.assertEqual(c.closest(a, b), p1)

        # already on segment
        c = Point(x=3, y=0)
        p1 = Point(x=3, y=0)
        self.assertEqual(c.closest(a, b), p1)

        # diagonal segment on line
        a = Point(x=0, y=0)
        b = Point(x=5, y=5)
        c = Point(x=3, y=3)
        p1 = Point(x=3, y=3)
        self.assertEqual(c.closest(a, b), p1)

        # diagonal segment close to line
        a = Point(x=0, y=0)
        b = Point(x=5, y=5)
        c = Point(x=3.1, y=2.9)
        p1 = Point(x=3, y=3)
        self.assertEqual(c.closest(a, b), p1)

        # all same place
        a = Point(x=0, y=0)
        b = Point(x=0, y=0)
        c = Point(x=0, y=0)
        p1 = Point(x=0, y=0)
        self.assertEqual(c.closest(a, b), p1)
