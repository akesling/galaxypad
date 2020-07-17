#!/usr/bin/env python

import unittest
from ops import int_to_grid, grid_to_linear


class TestLinear(unittest.TestCase):
    def check_example(self, num, result):
        linear = grid_to_linear(int_to_grid(num))
        self.assertEqual(linear, result)

    def test_examples(self):
        self.check_example(0, '010')
        self.check_example(1, '01100001')
        self.check_example(-1, '10100001')
        self.check_example(2, '01100010')
        self.check_example(-2, '10100010')
        self.check_example(16,  '0111000010000')
        self.check_example(-16, '1011000010000')
        self.check_example(255,  '0111011111111')
        self.check_example(-255, '1011011111111')
        self.check_example(256,  '011110000100000000')
        self.check_example(-256, '101110000100000000')



if __name__ == '__main__':
    unittest.main()