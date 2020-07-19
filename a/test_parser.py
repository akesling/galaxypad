#!/usr/bin/env python

import unittest
from parser import Tree, Value, Expr, parse, parse_file, vector, unvector, unparse


# class TestClasses(unittest.TestCase):
#     def test_repr(self):
#         for e in [
#             Expr(),
#             Value("0"),
#             Value("nil"),
#             Tree(Expr(), Value("2")),
#             Tree(Tree(Value("4"), Value("5")), Expr()),
#             Vect(0, 0),
#             Vect(1, 2),
#         ]:
#             self.assertEqual(eval(repr(e)), e)


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
            ("ap ap cons 0 1", [0, 1]),
            ("ap ap cons 0 nil", [0, []]),
            ("ap ap cons 1 ap ap cons 0 nil", [1, [0, []]]),
            ("ap ap cons ap ap cons 0 nil nil", [[0, []], []]),
            ("ap ap cons 1 ap ap cons ap ap cons 0 nil nil", [1, [[0, []], []]]),
        ]:
            self.assertEqual(parse(s), unvector(v))
            self.assertEqual(v, vector(unvector(v)))
            self.assertEqual(s, unparse(parse(s)))


if __name__ == "__main__":
    unittest.main()
