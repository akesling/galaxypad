#!/usr/bin/env python

import unittest
from collections import deque
from expr import Tree, Value


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
        self.assertTrue(Value(1).complete())
        # self.assertFalse(Value(None).complete())  # Gets converted to Value("None")

    def test_tree(self):
        a = Tree(Tree(Value(1), Value(2)), Value(3))
        b = Tree(Value(1), Tree(Value(2), Value(3)))
        self.assertNotEqual(a, b)
        self.assertTrue(Tree(Value(0), Value(1)).complete())
        a.left = None
        b.right = None
        with self.assertRaises(AssertionError, msg=repr(a)):
            deque(a.nlr(), maxlen=0)
        with self.assertRaises(AssertionError, msg=repr(b)):
            deque(b.nlr(), maxlen=0)



if __name__ == "__main__":
    unittest.main()