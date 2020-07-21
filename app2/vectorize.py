#!/usr/bin/env python

import re


from expr import Expr

VECTOR_REGEX = re.compile(r"[-\(\)\d\s,]+")


class Vector:
    pass


def vectorize(expr: Expr) -> Vector:
    raise NotImplementedError("TODO")


def unvectorize(vector: Vector) -> Expr:
    raise NotImplementedError("TODO")



if __name__ == '__main__':
    import sys

    from expr import parse, unparse

    if len(sys.argv) == 2:
        string = sys.argv[1]
        if VECTOR_REGEX.fullmatch(string):
            print(Vector(eval(string)))
        else:
            print(vectorize(parse(string)))
    else:
        print(f"Usage: {sys.argv[0]} '(0, ())'")
        print(f"       {sys.argv[0]} 'ap ap cons 0 nil'")