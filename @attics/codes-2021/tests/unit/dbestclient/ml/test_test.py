

import unittest


class TestSum(unittest.TestCase):
    def test_sum(self):
        data = [1, 2, 3]
        result = sum(data)
        # print("in test 0....")
        self.assertEqual(result, 6)


if __name__ == "__main__":
    unittest.main()
