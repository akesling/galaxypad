#!/usr/bin/env python

import unittest

from tree import vector, unvector, Tree, Value, pair


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


if __name__ == "__main__":
    unittest.main()
