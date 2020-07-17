#!/usr/bin/env python

import unittest
from ops import (  # noqa
    grid_to_int,
    grid_to_linear,
    int_to_grid,
    linear_to_grid,
    linear_to_int,
)


class TestLinear(unittest.TestCase):
    def check_int_example(self, num, result):
        linear = grid_to_linear(int_to_grid(num))
        self.assertEqual(linear, result)

    def test_linear_int_examples(self):
        self.check_int_example(0, "010")
        self.check_int_example(1, "01100001")
        self.check_int_example(-1, "10100001")
        self.check_int_example(2, "01100010")
        self.check_int_example(-2, "10100010")
        self.check_int_example(16, "0111000010000")
        self.check_int_example(-16, "1011000010000")
        self.check_int_example(255, "0111011111111")
        self.check_int_example(-255, "1011011111111")
        self.check_int_example(256, "011110000100000000")
        self.check_int_example(-256, "101110000100000000")

    def test_reverse_int_grid(self):
        for i in range(-10000, 10000):
            self.assertEqual(grid_to_int(int_to_grid(i)), i)

    def test_reverse_int_linear(self):
        for i in range(-10000, 10000):
            self.assertEqual(linear_to_int(grid_to_linear(int_to_grid(i))), i)

    # def check_list_example(self, data, result):
    #     linear=


if __name__ == "__main__":
    unittest.main()
