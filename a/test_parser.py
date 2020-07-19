#!/usr/bin/env python

import unittest
from parser import Ap, Atom, Expr, parse


class TestClasses(unittest.TestCase):
    def test_repr(self):
        for e in [
            Expr(),
            Atom("0"),
            Atom("nil"),
            Expr(Expr()),
            Expr(Expr(Atom("1"))),
            Ap(Expr(), Atom("2")),
            Expr(Ap(Atom("3"), Expr())),
            Ap(Ap(Atom("4"), Atom("5")), Expr()),
        ]:
            self.assertEqual(eval(repr(e)), e)


class TestParser(unittest.TestCase):
    def test_parse(self):
        for s, e in [
            ("1", Atom("1")),
            ("nil", Atom("nil")),
            ("ap inc 1", Ap(Atom("inc"), Atom("1"))),
            ("ap ap add 1 2", Ap(Ap(Atom("add"), Atom("1")), Atom("2"))),
        ]:
            self.assertEqual(parse(s), e)


if __name__ == "__main__":
    unittest.main()
