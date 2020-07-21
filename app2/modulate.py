#!/usr/bin/env python

import re

from expr import Expr

MODULATION_REGEX = re.compile(r"[01\s]+")


class Modulation:
    bits: str

    def __init__(self, bits: str):
        self.bits = bits


def modulate(expr: Expr) -> Modulation:
    raise NotImplementedError("TODO")


def demodulate(modulation: Modulation) -> Expr:
    raise NotImplementedError("TODO")


if __name__ == '__main__':
    import sys

    from expr import parse, unparse

    if len(sys.argv) == 2:
        string = sys.argv[1]
        if MODULATION_REGEX.fullmatch(string):
            print(demodulate(Modulation(string)))
        else:
            print(modulate(parse(string)))
    else:
        print(f"Usage: {sys.argv[0]} '1101000'")
        print(f"       {sys.argv[0]} 'ap ap cons 0 nil'")