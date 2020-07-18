#!/usr/bin/env python

import unittest
from tree import parse_tree
from compute import compute_fully


class TestImages(unittest.TestCase):
    def check_tree(self, string):
        """ Process a string into a tree and return it """
        tokens = string.strip().split()
        tree, leftover = parse_tree(tokens)
        self.assertEqual(leftover, [])  # Should be empty
        return tree

    def check_line(self, line, line_number):
        """ Check that a single equality line is correct """
        assert line.count("=") == 1, f"Bad test line #{line_number} {line}"
        left_s, right_s = line.split("=")
        left = self.check_tree(left_s)
        right = self.check_tree(right_s)
        self.assertEqual(
            compute_fully(left), compute_fully(right),
            f'line number {line_number}')

    def check_lines(self, lines):
        """ Check a bunch of lines are correct """
        for i, line in enumerate(lines.strip().split("\n")):
            line = line.strip()
            if line == "...":
                continue
            self.check_line(line, i)

    def test_equality(self):
        """ Basically that numbers equal themselves """
        self.check_lines(
            """
            0   =   0
            1   =   1
            2   =   2
            3   =   3
            ...
            10   =   10
            11   =   11
            ...
            -1   =   -1
            -2   =   -2
        """
        )

    def test_increment(self):
        self.check_lines(
            """
            ap inc 0   =   1
            ap inc 1   =   2
            ap inc 2   =   3
            ap inc 3   =   4
            ...
            ap inc 300   =   301
            ap inc 301   =   302
            ...
            ap inc -1   =   0
            ap inc -2   =   -1
            ap inc -3   =   -2
        """
        )

    def test_decrement(self):
        self.check_lines(
            """
            ap dec 1   =   0
            ap dec 2   =   1
            ap dec 3   =   2
            ap dec 4   =   3
            ...
            ap dec 1024   =   1023
            ...
            ap dec 0   =   -1
            ap dec -1   =   -2
            ap dec -2   =   -3
        """
        )

    def test_addition(self):
        self.check_lines(
            """
            ap ap add 1 2   =   3
            ap ap add 2 1   =   3
            ap ap add 0 1   =   1
            ap ap add 2 3   =   5
            ap ap add 3 5   =   8
        """
        )

    def test_placeholder(self):
        self.check_lines(
            """
            ap ap add 0 x0   =   x0
            ap ap add 0 x1   =   x1
            ap ap add 0 x2   =   x2
            ...
            ap ap add x0 0   =   x0
            ap ap add x1 0   =   x1
            ap ap add x2 0   =   x2
            """
            # We currently don't do this commutative check
            # ap ap add x0 x1   =   ap ap add x1 x0
        )

    def test_multiplication(self):
        self.check_lines(
            """
            ap ap mul 4 2   =   8
            ap ap mul 3 4   =   12
            ap ap mul 3 -2   =   -6
            ap ap mul x0 0   =   0
            ap ap mul x0 1   =   x0
        """
            # We currently don't do this commutative check
            # ap ap mul x0 x1   =   ap ap mul x1 x0
        )

    def test_division(self):
        self.check_lines(
            """
            ap ap div 4 2   =   2
            ap ap div 4 3   =   1
            ap ap div 4 4   =   1
            ap ap div 4 5   =   0
            ap ap div 5 2   =   2
            ap ap div 6 -2   =   -3
            ap ap div 5 -3   =   -1
            ap ap div -5 3   =   -1
            ap ap div -5 -3   =   1
            ap ap div x0 1   =   x0
        """
        )

    def test_compare_equals(self):
        self.check_lines(
            """
            ap ap eq x0 x0   =   t
            ap ap eq 0 -2   =   f
            ap ap eq 0 -1   =   f
            ap ap eq 0 0   =   t
            ap ap eq 0 1   =   f
            ap ap eq 0 2   =   f
            ...
            ap ap eq 1 -1   =   f
            ap ap eq 1 0   =   f
            ap ap eq 1 1   =   t
            ap ap eq 1 2   =   f
            ap ap eq 1 3   =   f
            ...
            ap ap eq 2 0   =   f
            ap ap eq 2 1   =   f
            ap ap eq 2 2   =   t
            ap ap eq 2 3   =   f
            ap ap eq 2 4   =   f
            ...
            ap ap eq 19 20   =   f
            ap ap eq 20 20   =   t
            ap ap eq 21 20   =   f
            ...
            ap ap eq -19 -20   =   f
            ap ap eq -20 -20   =   t
            ap ap eq -21 -20   =   f
        """
        )

    def test_less_than(self):
        self.check_lines(
            """
            ap ap lt 0 -1   =   f
            ap ap lt 0 0   =   f
            ap ap lt 0 1   =   t
            ap ap lt 0 2   =   t
            ...
            ap ap lt 1 0   =   f
            ap ap lt 1 1   =   f
            ap ap lt 1 2   =   t
            ap ap lt 1 3   =   t
            ...
            ap ap lt 2 1   =   f
            ap ap lt 2 2   =   f
            ap ap lt 2 3   =   t
            ap ap lt 2 4   =   t
            ...
            ap ap lt 19 20   =   t
            ap ap lt 20 20   =   f
            ap ap lt 21 20   =   f
            ...
            ap ap lt -19 -20   =   f
            ap ap lt -20 -20   =   f
            ap ap lt -21 -20   =   t
        """
        )

    def test_negate(self):
        self.check_lines(
            """
            ap neg 0   =   0
            ap neg 1   =   -1
            ap neg -1   =   1
            ap neg 2   =   -2
            ap neg -2   =   2
        """
        )

    def test_application(self):
        self.check_lines(
            """
            ap inc ap inc 0   =   2
            ap inc ap inc ap inc 0   =   3
            ap inc ap dec x0   =   x0
            ap dec ap inc x0   =   x0
            ap ap add ap ap add 2 3 4   =   9
            ap ap add 2 ap ap add 3 4   =   9
            ap ap add ap ap mul 2 3 4   =   10
            ap ap mul 2 ap ap add 3 4   =   14
        """
            # This is outside of our rewriting rules for now
            # Requires a commutative transform
            # ap dec ap ap add x0 1   =   x0
        )

    def test_s_combinator(self):
        self.check_lines(
            """
            ap ap ap s x0 x1 x2   =   ap ap x0 x2 ap x1 x2
            ap ap ap s add inc 1   =   3
            ap ap ap s mul ap add 1 6   =   42
        """
        )

    def test_c_combinator(self):
        self.check_lines(
            """
            ap ap ap c x0 x1 x2   =   ap ap x0 x2 x1
            ap ap ap c add 1 2   =   3
        """
        )

    def test_b_combinator(self):
        self.check_lines(
            """
            ap ap ap b x0 x1 x2   =   ap x0 ap x1 x2
            ap ap ap b inc dec x0   =   x0
        """
        )

    def test_t_combinator(self):
        self.check_lines(
            """
            ap ap t x0 x1   =   x0
            ap ap t 1 5   =   1
            ap ap t t i   =   t
            ap ap t t ap inc 5   =   t
            ap ap t ap inc 5 t   =   6
        """
        )

    def test_f_combinator(self):
        self.check_lines(
            """
            ap ap f x0 x1   =   x1
            """
            # This is a much more fancy transformation
            # Unfortunately it grows the tree by a ton
            # I think we should figure out whether or not to add this
            # f   =   ap s t
        )

    def test_pwr2(self):
        self.check_lines(
            """
            ap pwr2 0   =   ap ap ap s ap ap c ap eq 0 1 ap ap b ap mul 2 ap ap b pwr2 ap add -1 0
            ap pwr2 0   =   ap ap ap ap c ap eq 0 1 0 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 0
            ap pwr2 0   =   ap ap ap ap eq 0 0 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 0
            ap pwr2 0   =   ap ap t 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 0
            ap pwr2 0   =   1
            ap pwr2 1   =   ap ap ap s ap ap c ap eq 0 1 ap ap b ap mul 2 ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap ap ap c ap eq 0 1 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap ap ap eq 0 1 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap f 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap ap b pwr2 ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap pwr2 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap ap s ap ap c ap eq 0 1 ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap ap ap c ap eq 0 1 ap ap add -1 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap ap ap eq 0 ap ap add -1 1 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap ap ap eq 0 0 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 ap ap t 1 ap ap ap b ap mul 2 ap ap b pwr2 ap add -1 ap ap add -1 1
            ap pwr2 1   =   ap ap mul 2 1
            ap pwr2 1   =   2
            ap pwr2 2   =   ap ap ap s ap ap c ap eq 0 1 ap ap b ap mul 2 ap ap b pwr2 ap add -1 2
            ...
            ap pwr2 2   =   4
            ap pwr2 3   =   8
            ap pwr2 4   =   16
            ap pwr2 5   =   32
            ap pwr2 6   =   64
            ap pwr2 7   =   128
            ap pwr2 8   =   256
            """
        )

    def test_identity(self):
        self.check_lines(
            """
            ap i x0   =   x0
            ap i 1   =   1
            ap i i   =   i
            ap i add   =   add
            ap i ap add 1   =   ap add 1
        """
        )

    def test_pair(self):
        self.check_lines(
            """
            ap ap ap cons x0 x1 x2   =   ap ap x2 x0 x1
        """
        )

    def test_head(self):
        self.check_lines(
            """
            ap car ap ap cons x0 x1   =   x0
        """
            # More advanced than we can do presently
            # I dont quite understand exactly what's going on here
            # ap car x2   =   ap x2 t
        )

    def test_tail(self):
        self.check_lines(
            """
            ap cdr ap ap cons x0 x1   =   x1
        """
            # More advanced substitution than we can do presently
            # TODO is figure out how to do something like this
            # I think this rewrite is a simplification
            # ap cdr x2   =   ap x2 f
        )

    def test_nil(self):
        self.check_lines(
            """
            ap nil x0   =   t
        """
        )

    def test_isnil(self):
        self.check_lines(
            """
            ap isnil nil   =   t
            ap isnil ap ap cons x0 x1   =   f
        """
        )

    def test_vector(self):
        self.check_lines(
            """
            vec   =   cons
        """
            # Normally this would be dangerous
            # Because we could oscillate between these symbols
            # For now we only include one-way rewrite rules
            # So this should be safe for the moment
        )

    def test_if0(self):
        self.check_lines("""
            ap ap ap if0 0 x0 x1   =   x0
            ap ap ap if0 1 x0 x1   =   x1
        """
        )

    def test_send(self):
        self.check_lines("""
            ap send nil = ap ap cons 0 nil
        """)


if __name__ == "__main__":
    unittest.main()
