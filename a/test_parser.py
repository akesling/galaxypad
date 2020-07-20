#!/usr/bin/env python

import unittest
from galaxy import (
    Tree,
    Value,
    Expr,
    parse,
    parse_file,
    vector,
    unvector,
    unparse,
    modulate,
    demodulate,
)


class TestClasses(unittest.TestCase):
    def test_repr(self):
        for e in [
            Value("0"),
            Value("nil"),
            Tree(Value("0"), Value("2")),
            Tree(Tree(Value("cons"), Value("5")), Value("nil")),
        ]:
            self.assertEqual(eval(repr(e)), e)


def pair(h, t):
    return Tree(Tree(Value("cons"), h), t)


class TestParser(unittest.TestCase):
    def test_parse(self):
        for s, e in [
            ("1", Value("1")),
            ("nil", Value("nil")),
            ("ap inc 1", Tree(Value("inc"), Value("1"))),
            ("ap ap add 1 2", Tree(Tree(Value("add"), Value("1")), Value("2"))),
            # ("ap ap cons 0 nil", Vector([0])),
            # ("ap ap cons 1 ap ap cons 2 nil", Vector([1, 2])),
        ]:
            self.assertEqual(parse(s), e)

    def test_parse_galaxy(self):
        parse_file("galaxy.txt")


class TestVector(unittest.TestCase):
    def test_parse(self):
        for s, v in [
            ("0", 0),
            ("1", 1),
            ("nil", None),
            ("ap ap cons 0 nil", [0]),
            ("ap ap cons 0 1", (0, 1)),
            ("ap ap cons 0 ap ap cons 1 nil", [0, 1]),
            ("ap ap cons 0 ap ap cons 1 ap ap cons 2 nil", [0, 1, 2]),
            ("ap ap cons ap ap cons 0 nil nil", [[0]]),
            ("ap ap cons nil nil", (None, None)),
            (
                "ap ap cons ap ap cons 0 1 ap ap cons ap ap cons 2 3 nil",
                [(0, 1), (2, 3)],
            ),
            ("ap ap cons 1 ap ap cons ap ap cons 0 nil nil", (1, [[0]])),
        ]: 
            self.assertEqual(s, unparse(parse(s)), s)  # String parses
            self.assertEqual(v, vector(unvector(v)), s)  # Vector parses
            self.assertEqual(s, unparse(unvector(v)), s)
            self.assertEqual(v, vector(parse(s)), s)
            self.assertEqual(parse(s), unvector(v), s)


class TestModulate(unittest.TestCase):
    def test_ints(self):
        for i in range(-10000, 10000):
            value = Value(str(i))
            self.assertEqual(demodulate(modulate(value)), value)

    def check_int_example(self, i, modulation):
        value = Value(str(i))
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

    def check_tree_example(self, tree, modulation):
        self.assertEqual(modulate(tree), modulation)
        self.assertEqual(demodulate(modulation), tree)

    def test_tree_examples(self):
        self.check_tree_example(Value("nil"), "00")
        self.check_tree_example(unvector((None, None)), "110000")
        self.check_tree_example(unvector([0]), "1101000")
        self.check_tree_example(unvector((1, 2)), "110110000101100010")
        self.check_tree_example(unvector((1, (2, None))), "1101100001110110001000")

    def test_vec_examples(self):
        self.check_tree_example(unvector([1, 2]), "1101100001110110001000")
        self.check_tree_example(
            unvector([1, [2, 3], 4]), "1101100001111101100010110110001100110110010000"
        )


if __name__ == "__main__":
    unittest.main()
