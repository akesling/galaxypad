#!/usr/bin/env python

import unittest
from collections import deque
from expr import Tree, Value, nlr, parse, unparse


class TestClasses(unittest.TestCase):
    def test_value(self):
        self.assertEqual(Value('nil'), Value('nil'))
        self.assertEqual(Value('i'), Value('i'))
        self.assertEqual(Value(':123'), Value(':123'))
        self.assertEqual(Value('galaxy'), Value('galaxy'))
        self.assertEqual(Value(0), Value(0))
        self.assertEqual(Value(1), Value(1))
        self.assertEqual(Value(-1), Value(-1))
        self.assertNotEqual(Value(0), Value(1))
        self.assertEqual(Value(0), Value("0"))
        self.assertEqual(Value(1), Value("1"))
        self.assertEqual(Value(-1), Value("-1"))
        self.assertNotEqual(Value(0), Value("1"))
        self.assertEqual(int(Value(0)), 0)
        self.assertEqual(int(Value(1)), 1)
        self.assertEqual(int(Value(-1)), -1)
        with self.assertRaises(ValueError):
            int(Value('nil'))

    def test_tree(self):
        a = Tree(Tree(Value(1), Value(2)), Value(3))
        b = Tree(Value(1), Tree(Value(2), Value(3)))
        self.assertNotEqual(a, b)
        a.left = None
        b.right = None
        with self.assertRaises(ValueError, msg=repr(a)):
            deque(nlr(a), maxlen=0)
        with self.assertRaises(ValueError, msg=repr(b)):
            deque(nlr(b), maxlen=0)


TEST_EXPRESSIONS = [line.strip() for line in '''
    0
    1
    -1
    98712983479182374987
    nil
    ap inc 1
    ap ap add 1 2
    ap ap cons 0 nil
    ap ap cons 0 ap ap cons 1 nil
    ap ap cons ap ap cons 0 nil nil
    ap ap ap ap inc dec inc dec 0
    ap ap mul 2 ap ap ap ap eq 0 ap ap add -1 1 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
'''.strip().split('\n')]


class TestParser(unittest.TestCase):
    def test_parser(self):
        for s in TEST_EXPRESSIONS:
            self.assertEqual(s, unparse(parse(s)))
        


if __name__ == "__main__":
    unittest.main()