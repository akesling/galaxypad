#!/usr/bin/env python

import re

from vectorize import Vector

MODULATION_REGEX = re.compile(r"[01\s]+")


class Modulation:
    pass


def modulate(vector: Vector) -> Modulation:
    raise NotImplementedError("TODO")


def demodulate(modulation: Modulation) -> Vector:
    raise NotImplementedError("TODO")


if __name__ == '__main__':
    import sys

    from expr import parse, unparse
    from vectorize import VECTOR_REGEX

    if len(sys.argv) == 2:
        string = sys.argv[1]
        if MODULATION_REGEX.fullmatch(string):
            print(demodulate(Modulation(string)))
        elif VECTOR_REGEX.fullmatch(string):
            print(demodulate(Vector(eval(string))))
        else:
            print(modulate(vectorize(parse(string))))
    else:
        print(f"Usage: {sys.argv[0]} '1101000'")
        print(f"       {sys.argv[0]} '(0, ())'")
        print(f"       {sys.argv[0]} 'ap ap cons 0 nil'")