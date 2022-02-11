import unittest

import os


# class ENVTest(unittest.TestCase):
#     def test_defaults(self):
#         import env

#         self.assertFalse(env.DEBUG)

#         self.assertIsInstance(env.TARGET_TIME, int)
#         self.assertIsInstance(env.MINIMUM_DEPTH, int)

#         self.assertAlmostEqual(env.TARGET_TIME, 1500, delta=1400)
#         self.assertAlmostEqual(env.MINIMUM_DEPTH, 7, delta=2)

#     def test_env_set(self):
#         os.environ['DEBUG'] = '1'
#         os.environ['TARGET_TIME'] = '1000'
#         os.environ['MINIMUM_DEPTH'] = '5'

#         import env

#         self.assertEqual(env.DEBUG, 1)
#         self.assertEqual(env.TARGET_TIME, 1000)
#         self.assertEqual(env.MINIMUM_DEPTH, 5)
