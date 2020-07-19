#!/usr/bin/env python

import unittest
from parser import Ap, Atom, Expr, parse, parse_file, Vect


class TestClasses(unittest.TestCase):
    def test_repr(self):
        for e in [
            Expr(),
            Atom("0"),
            Atom("nil"),
            Ap(Expr(), Atom("2")),
            Expr(Ap(Atom("3"), Expr())),
            Ap(Ap(Atom("4"), Atom("5")), Expr()),
            # With Evalutated
            Expr(Expr()),
            Expr(Expr(Atom("1"))),
            Atom("0", Expr()),
            Atom("nil", Atom('nil')),
            Ap(Expr(), Atom("2"), Atom('2')),
            Expr(Ap(Atom("3"), Expr(), Expr())),
            Ap(Ap(Atom("4"), Atom("5")), Expr(), Expr()),
            # Vect
            Vect(0, 0),
            Vect(1, 2),
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

    def test_parse_galaxy(self):
        parse_file('galaxy.txt')


if __name__ == "__main__":
    unittest.main()
