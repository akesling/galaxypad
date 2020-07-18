#!/usr/bin/env python

import unittest
from parser import parse_partial, unparse


class TestParser(unittest.TestCase):
    def test_int_reverse(self):
        for i in range(-10000, 10000):
            modulation = unparse(i)
            value, remainder = parse_partial(modulation)
            self.assertEqual(value, i)
            self.assertEqual(remainder, '')


if __name__ == '__main__':
    unittest.main()