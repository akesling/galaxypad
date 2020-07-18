#!/usr/bin/env python

import unittest

from tree import Value, pair
from vector import unvector
from modulate import Modulation, demodulate, modulate, modulate_vector


class TestModulate(unittest.TestCase):
    def test_ints(self):
        for i in range(-10000, 10000):
            value = Value(i)
            self.assertEqual(demodulate(modulate(value)), value)

    def check_int_example(self, i, bits):
        value = Value(i)
        modulation = Modulation(bits)
        self.assertEqual(value, demodulate(modulation))
        self.assertEqual(modulate(value), modulation)

    def test_int_examples(self):
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

    def check_tree_example(self, tree, bits):
        modulation = Modulation(bits)
        self.assertEqual(modulate(tree), modulation)
        self.assertEqual(demodulate(modulation), tree)

    def test_tree_examples(self):
        nil = Value("nil")
        _0 = Value(0)
        _1 = Value(1)
        _2 = Value(2)
        self.check_tree_example(nil, "00")
        self.check_tree_example(pair(nil, nil), "110000")
        self.check_tree_example(pair(_0, nil), "1101000")
        self.check_tree_example(pair(_1, _2), "110110000101100010")
        self.check_tree_example(pair(_1, pair(_2, nil)), "1101100001110110001000")

    def test_vec_examples(self):
        self.check_tree_example(unvector([1, 2]), "1101100001110110001000")
        self.check_tree_example(
            unvector([1, [2, 3], 4]), "1101100001111101100010110110001100110110010000"
        )


if __name__ == "__main__":
    unittest.main()
