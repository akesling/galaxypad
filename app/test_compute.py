#!/usr/bin/env python

import unittest
from compute import tokens_to_tree, Tree, LAMBDAS, Variable


class TestOps(unittest.TestCase):
    def test_div(self):
        div = LAMBDAS['div']
        self.assertEqual(div(4)(2), 2)
        self.assertEqual(div(4)(3), 1)
        self.assertEqual(div(4)(4), 1)
        self.assertEqual(div(4)(5), 0)
        self.assertEqual(div(5)(2), 2)
        self.assertEqual(div(6)(-2), -3)
        self.assertEqual(div(5)(-3), -1)
        self.assertEqual(div(-5)(3), -1)
        self.assertEqual(div(-5)(-3), 1)
        self.assertEqual(div(Variable(0))(1), Variable(0))


class TestTree(unittest.TestCase):
    def test_numbers(self):
        tree, tokens = tokens_to_tree('1 ap'.split())
        self.assertEqual(tree, 1)
        self.assertEqual(tokens, ['ap'])  # leftover

    def test_basic(self):
        ts = 'ap ap add 1 2'.split()
        tree, tokens = tokens_to_tree(ts)
        add = LAMBDAS['add']
        test_tree = Tree(Tree(add, 1), 2)
        self.assertEqual(tree, test_tree)
        self.assertEqual(tokens, [])

    def test_add(self):
        add = LAMBDAS['add']
        tree, tokens = tokens_to_tree('ap ap add 0 x0'.split())
        test_tree = Tree(Tree(add, 0), Variable(0))
        self.assertEqual(tree, test_tree)
        self.assertEqual(tokens, [])

    def test_variable(self):
        ts = 'ap ap add 0 x0'.split()
        tree, tokens = tokens_to_tree(ts)
        add = LAMBDAS['add']
        test_tree = Tree(Tree(add, 0), Variable(0))
        self.assertEqual(tree, test_tree)
        self.assertEqual(tokens, [])
 


class TestCompute(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()