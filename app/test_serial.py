#!/usr/bin/env python

import unittest

from tree import Tree, Value
from serial import serialize, deserialize


class TestSerialize(unittest.TestCase):
    def check_serialize(self, serial):
        self.assertEqual(serial, serialize(deserialize(serial)))

    def test_serialize(self):
        for serial in """
            0
            i
            nil
            ap
            ap inc
            ap inc 0
            ap ap add
            ap ap add 1
            ap ap add 1 2
        """.strip().split():
            self.check_serialize(serial)

    def check_deserialize(self, tree, serial):
        self.assertEqual(tree, deserialize(serial))
        self.assertEqual(serialize(tree), serial)

    def test_deserialize(self):
        _0 = Value(0)
        _1 = Value(1)
        _add = Value("add")
        for tree, serial in [
            (_0, "0"),
            (_add, "add"),
            (Tree(), "ap"),
            (Tree(_add), "ap add"),
            (Tree(_add, _0), "ap add 0"),
            (Tree(Tree(_add)), "ap ap add"),
            (Tree(Tree(_add, _0)), "ap ap add 0"),
            (Tree(Tree(_add, _0), _1), "ap ap add 0 1"),
        ]:
            self.check_deserialize(tree, serial.strip())


if __name__ == "__main__":
    unittest.main()
