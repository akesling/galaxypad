#!/usr/bin/env python

from expr import Expr, Value, Tree
from typing import Callable, Any

# Python still doesn't have recursive types
Continuation = Callable[[Expr], Callable]


def evaluate(expr: Expr) -> Expr:
    """ Evaluate an expression, returning evaluated tree """
    def done(evaluation):
        if isinstance(evaluation, Expr):
            return evaluation
        raise ValueError(f"bad evalution {evaluation}")
    # Consume continuations until base value
    # https://en.wikipedia.org/wiki/Trampoline_(computing)
    call: Callable = evaluate_c(expr, done)
    while callable(call):
        call = call()
    return call


def evaluate_c(expr: Expr, cont: Continuation) -> Callable:
    """ Evaluate an expression, continuation passing style """
    if isinstance(expr, Value):
        return cont(expr)
    if isinstance(expr, Tree):
        def fv(value):
            expr.value = value
            return cont(value)
        return lambda: evaluate_tree_c(expr, fv)  # mypy bug?
    raise ValueError(f"bad expr {expr}")


def evaluate_int_c(expr: Expr, cont: Continuation) -> Callable:
    """ Evaluate to an integer, continuation passing style """
    def fv(value):
        if isinstance(value, Value):
            return cont(int(value))
        raise ValueError(f"bad value {value}")
    return lambda: evaluate_c(expr, fv)


def evaluate_math_c(expr: Expr, cont: Continu)


def evaluate_tree_c(tree: Tree, cont: Continuation) -> Callable:
    """ Evaluate a tree, continuation passing style """
    if tree.value is not None:
        return cont(tree.value)

    def left(left: Expr):
        x = tree.right
        # Non arithmetic, single argument
        if left == Value('i'):
            return cont(x)
        if left == Value('nil'):
            return cont(Value("t"))
        # Arithmetic, single argument
        def intx(intx: int):
            if left 
        return lambda: evaluate_int_c(x, intx)
        if isinstance(left, Tree):
            left2 = left.left
            y = left.right
            if left2 == Value('t'):
                return cont(y)
            if left2 == Value('f'):
                return cont(x)
        # Arithmetic methods
        def fx(ix):
            if left == Value('inc'):
                return cont(ix + 1)
    return lambda: evaluate_c(tree.left, left)



    def fx(x):
        left = tree.left
        if left == Value("inc"):
            return cont(x + 1)
        elif isinstance(left, Tree):
            def fy(y):
                y = evaluate(left.right)
                left2 = left.left
                if left2 == Value("add"):
                    return cont(y + x)
                raise ValueError(f"bad left2 {left2}")
            return lambda: evaluate_c(left.right, fy)
        raise ValueError(f"bad left {left}")
    return lambda: evaluate_c(tree.right, fx)



if __name__ == '__main__':
    import sys

    from expr import parse, unparse

    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")