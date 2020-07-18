#!/usr/bin/env python

import unittest
from tree import parse_tree, compute_fully


class TestImages(unittest.TestCase):
    def check_tree(self, string):
        """ Process a string into a tree and return it """
        tokens = string.strip().split()
        tree, leftover = parse_tree(tokens)
        self.assertEqual(leftover, [])  # Should be empty
        return tree

    def check_line(self, line):
        """ Check that a single equality line is correct """
        assert line.count("=") == 1, f"Bad test line {line}"
        left_s, right_s = line.split("=")
        left = self.check_tree(left_s)
        right = self.check_tree(right_s)
        self.assertEqual(compute_fully(left), right)

    def check_lines(self, lines):
        """ Check a bunch of lines are correct """
        for line in lines.strip().split("\n"):
            line = line.strip()
            if line == "...":
                continue
            self.check_line(line)

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


if __name__ == "__main__":
    unittest.main()
