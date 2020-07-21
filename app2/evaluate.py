#!/usr/bin/env python

from expr import Expr

def evaluate(expr: Expr) -> Expr:
    raise NotImplementedError("TODO")


if __name__ == '__main__':
    import sys

    from expr import parse, unparse

    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")