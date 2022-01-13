import unittest

from checkers import vec2


class VectorTest(unittest.TestCase):
    def test_vector_init(self):
        vec = vec2(1, 2)
        self.assertEqual(vec.x, 1)
        self.assertEqual(vec.y, 2)

    def test_vector_add(self):
        self.assertEqual(vec2(1, 2) + vec2(3, 4), vec2(4, 6))
        self.assertEqual(vec2(2, 1) + vec2(-3, -4), vec2(-1, -3))

    def test_vector_sub(self):
        self.assertEqual(vec2(1, 2) - vec2(3, 4), vec2(-2, -2))
        self.assertEqual(vec2(2, 1) - vec2(-3, -4), vec2(5, 5))

    def test_vector_mul(self):
        self.assertEqual(vec2(1, 2) * 3, vec2(3, 6))
        self.assertEqual(vec2(2, 1) * -3, vec2(-6, -3))

    def test_vector_div(self):
        self.assertEqual(vec2(1, 2) // 2, vec2(0, 1))
        self.assertEqual(vec2(5, 7) // -3, vec2(-2, -3))

    def test_vector_eq(self):
        self.assertTrue(vec2(1, 2) == vec2(1, 2))
        self.assertFalse(vec2(1, 2) == vec2(2, 1))
        self.assertFalse(vec2(1, 2) == vec2(2, 2))

    def test_vector_hash(self):
        self.assertEqual(hash(vec2(1, 2)), hash(vec2(1, 2)))
        self.assertNotEqual(hash(vec2(1, 2)), hash(vec2(2, 1)))
        self.assertNotEqual(hash(vec2(1, 2)), hash(vec2(2, 2)))

    def test_vector_center(self):
        self.assertEqual(vec2(1, 2).center(vec2(0, 1)), None)
        self.assertEqual(vec2(1, 2).center(vec2(-1, 0)), vec2(0, 1))
        self.assertEqual(vec2(3, 4).center(vec2(5, 2)), vec2(4, 3))
        self.assertEqual(vec2(3, 4).center(vec2(5, 1)), None)

    def test_vector_distance(self):
        self.assertEqual(vec2(1, 2).distance(vec2(0, 1)), 1)
        self.assertEqual(vec2(1, 2).distance(vec2(-1, 0)), 2)
        self.assertEqual(vec2(3, 4).distance(vec2(5, 2)), 2)
        self.assertEqual(vec2(3, 4).distance(vec2(5, 1)), 3)