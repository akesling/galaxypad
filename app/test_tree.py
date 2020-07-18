#!/usr/bin/env python

import unittest

from tree import Tree, Value, deserialize, pair, serialize, unvector, vector


class TestVector(unittest.TestCase):
    def check_example(self, vec):
        self.assertEqual(vector(unvector(vec)), vec)

    def test_examples(self):
        for vec in [
            [],
            [[]],
            [0],
            [[], 0],
            [0, 1],
            [1, 2, 3],
            [[1, 2], 3],
            [1, 2, 3, 4],
            [1, [2, 3], 4],
        ]:
            self.check_example(vec)

    def check_vector(self, vec, tree):
        self.assertEqual(unvector(vec), tree)
        self.assertEqual(vec, vector(tree))

    def test_vector(self):
        nil = Value('nil')
        _0 = Value(0)
        _1 = Value(1)
        _2 = Value(2)
        for vec, tree in [
            ([], nil),
            ([0], pair(_0, nil)),
            ([0, 1], pair(_0, pair(_1, nil))),
            ([0, 1, 2], pair(_0, pair(_1, pair(_2, nil)))),
            ([[0, 1], 2], pair(pair(_0, pair(_1, nil)), pair(_2, nil))),
            ([2, [0, 1]], pair(_2, pair(pair(_0, pair(_1, nil)), nil))),
        ]:
            self.check_vector(vec, tree)


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
        _add = Value('add')
        for tree, serial in [
            (_0, '0'),
            (_add, 'add'),
            (Tree(), 'ap'),
            (Tree(_add), 'ap add'),
            (Tree(_add, _0), 'ap add 0'),
            (Tree(Tree(_add)), 'ap ap add'),
            (Tree(Tree(_add, _0)), 'ap ap add 0'),
            (Tree(Tree(_add, _0), _1), 'ap ap add 0 1'),
        ]:
            self.check_deserialize(tree, serial.strip())



if __name__ == "__main__":
    unittest.main()
