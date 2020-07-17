#!/usr/bin/env python

import unittest
from ops import (  # noqa
    grid_to_int,
    grid_to_linear,
    int_to_grid,
    linear_to_grid,
    linear_to_int,
    list_to_linear,
    list_to_cons_form,
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

    def check_list_example(self, data, result):
        linear = list_to_linear(data)
        self.assertEqual(linear, result)

    def test_linear_list_examples(self):
        self.check_list_example([None], '00')
        self.check_list_example([None, None], '110000')
        self.check_list_example([0, None], '1101000')
        self.check_list_example([1, 2], '110110000101100010')
        self.check_list_example([1, [2, None]], '1101100001110110001000')
        t1 = list_to_cons_form([1, 2])
        self.check_list_example(t1, '1101100001110110001000')
        t2 = list_to_cons_form([1, [2, 3], 4])
        self.check_list_example(t2, '1101100001111101100010110110001100110110010000')

    def test_list_to_cons_form(self):
        self.assertEqual(list_to_cons_form([1, 2, None]), [1, [2, None]])
        self.assertEqual(list_to_cons_form([1, [2, None]]), [1, [2, None]])

if __name__ == "__main__":
    unittest.main()
