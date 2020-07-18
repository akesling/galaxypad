#!/usr/bin/env python

import unittest
from tree import Value, vector, pair
from mod_parser import parse_partial, unparse


class TestParser(unittest.TestCase):
    def test_int_reverse(self):
        for i in range(-10000, 10000):
            modulation = unparse(i)
            value, remainder = parse_partial(modulation)
            self.assertEqual(value, Value(i))
            self.assertEqual(remainder, '')

    def check_int_example(self, i, modulation):
        value, remainder = parse_partial(modulation)
        self.assertEqual(Value(i), value)
        self.assertEqual(remainder, '')
        self.assertEqual(unparse(i), modulation)

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

    def check_list_example(self, l, modulation):
        value, remainder = parse_partial(modulation)
        self.assertEqual(l, value)
        self.assertEqual(remainder, '')
        self.assertEqual(unparse(l), modulation)

    def test_linear_list_examples(self):
        nil = Value('nil')
        self.check_list_example(nil, "00")
        self.check_list_example(pair(nil, nil), "110000")
        self.check_list_example(pair(0, nil), "1101000")
        self.check_list_example(pair(1, 2), "110110000101100010")
        self.check_list_example(pair(1, pair(2, nil)), "1101100001110110001000")
        self.check_list_example(vector([1, 2]), "1101100001110110001000")
        v = vector([1, [2, 3], 4])
        self.check_list_example(v, "1101100001111101100010110110001100110110010000")


if __name__ == '__main__':
    unittest.main()
