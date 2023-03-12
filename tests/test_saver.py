import unittest

from ai.AG import Saver


class TestSaver(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self) -> None:
        pass

    def test_saver_create(self):
        s = Saver(":memory:")

        data = ("testfile", 42, 1500, 22, "abcdef", 123.45)
        s.save(*data)

        target_data = ("abcdef", 123.45)
        ans = s.get_best("testfile")
        self.assertTupleEqual(ans, target_data)
