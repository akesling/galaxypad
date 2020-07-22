#!/usr/bin/env python

import logging

from expr import Expr, Value, Tree, parse_tokens, unparse
from typing import Callable, Dict

logging.basicConfig(level=logging.DEBUG)
logging.debug("Debug logging enabled.")

inc = Value("inc")
dec = Value("dec")
neg = Value("neg")
i = Value("i")
nil = Value("nil")
isnil = Value("isnil")
car = Value("car")
cdr = Value("cdr")
t = Value("t")
f = Value("f")
add = Value("add")
mul = Value("mul")
div = Value("div")
lt = Value("lt")
eq = Value("eq")
cons = Value("cons")
s = Value("s")
c = Value("c")
b = Value("b")
UNARY_MATH = (neg, inc, dec)
BINARY_MATH = (add, mul, div, lt, eq)


functions: Dict[str, Expr] = {}
for line in open("galaxy.txt").readlines():
    name, _, *tokens = line.strip().split()
    functions[name] = parse_tokens(tokens)


def trampoline(call: Callable):
    """ Consume continuations until a base value """
    # https://en.wikipedia.org/wiki/Trampoline_(computing)
    # https://eli.thegreenplace.net/2017/on-recursion-continuations-and-trampolines/
    # http://blog.moertel.com/posts/2013-06-12-recursion-to-iteration-4-trampolines.html
    while callable(call):
        call = call()
    return call

# def evaluate(orig: Expr) -> Expr:
#     """ Fully evaluate an expression, returning resulting expression """
#     expr = orig
#     while True:
#         res = try_evaluate(expr)
#         if res == expr:
#             orig.value = res
#             return res
#         expr = res
            

def evaluate(expr: Expr) -> Expr:
    """ Evaluate an expression, returning evaluated expression """
    logging.debug(f"try_evaluate {unparse(expr)}")
    evaluation = trampoline(evaluate_c(expr, lambda x: x))
    if isinstance(evaluation, Expr):
        return evaluation
    raise ValueError(f"bad evalution {evaluation}")


def evaluate_c(orig: Expr, call: Callable) -> Callable:
    """ Evaluate an expression, continuation passing style """
    logging.debug(f"evaluate_c {unparse(orig)}")
    if isinstance(orig, Expr):
        if orig.value is not None:
            return call(orig.value)
        def expr(expr):
            def res(res):
                if expr == res:
                    orig.value = res
                    return cal(orig)
                return lambda: evaluate_c(expr, res)
            return lambda: evaluate_c(expr, res)
        return lambda: evaluate_c(orig, expr)
    raise ValueError(f"bad expr {expr}")


def evaluate_integer_c(expr: Expr, call: Callable) -> Callable:
    """ Evaluate to an integer, continuation passing style """
    logging.debug(f"evaluate_integer_c {unparse(expr)}")

    def integer(integer):
        if isinstance(integer, Value):
            return call(int(integer))
        raise ValueError(f"bad integer {integer}")

    return evaluate_c(expr, integer)


def evaluate_math_c(tree: Tree, call: Callable) -> Callable:
    """ Evaluate arithmetic, continuation passing style """
    logging.debug(f"evaluate_math_c {unparse(tree)}")
    if isinstance(tree, Tree):
        left = tree.left

        def x(x):
            if left == neg:
                return call(Value(-x))
            if left == inc:
                return call(Value(x + 1))
            if left == dec:
                return call(Value(x - 1))
            if isinstance(left, Tree):
                left2 = left.left

                def y(y):
                    if left2 == add:
                        return call(Value(y + x))
                    if left2 == mul:
                        return call(Value(y * x))
                    if left2 == div:
                        return call(Value(y // x if y * x > 0 else (y + (-y % x)) // x))
                    if left2 == lt:
                        return call(t if y < x else f)
                    if left2 == eq:
                        return call(t if y == x else f)
                    raise ValueError(f"bad binary math {tree}")

                return evaluate_integer_c(left.right, y)
            raise ValueError(f"bad unary math {tree}")

        return evaluate_integer_c(tree.right, x)
    raise ValueError(f"bad math {tree}")


def evaluate_try_c(expr: Tree, call: Callable) -> Callable:
    """ Try to evaluate an expression, continuation passing style """
    logging.debug(f"evaluate_try_c {unparse(expr)}")
    if isinstance(expr, Expr) and expr.value is not None:
        return call(expr.value)
    if isinstance(expr, Value) and expr.name in functions:
        return call(functions[expr.name])
    if isinstance(expr, Tree):

        def left(left):
            x = expr.right
            if left == i:
                return call(x)
            if left == nil:
                return call(t)
            if left == isnil:
                return call(Tree(x, Tree(t, Tree(t, f))))
            if left == car:
                return call(Tree(x, t))
            if left == cdr:
                return call(Tree(x, f))
            if left in UNARY_MATH:
                return evaluate_math_c(expr, call)
            if isinstance(left, Tree):

                def left2(left2):
                    y = left.right
                    if left2 == t:
                        return call(y)
                    if left2 == f:
                        return call(x)
                    if left2 == cons:
                        return evaluate_cons_c(y, x, call)
                    if left2 in BINARY_MATH:
                        return evaluate_math_c(expr, call)
                    if isinstance(left2, Tree):

                        def left3(left3):
                            z = left2.right
                            if left3 == s:
                                return call(Tree(Tree(z, x), Tree(y, x)))
                            if left3 == c:
                                return call(Tree(Tree(x, x), y))
                            if left3 == b:
                                return call(Tree(z, Tree(y, x)))
                            if left3 == cons:
                                return call(Tree(Tree(x, z), y))
                            return call(expr)

                        return evaluate_c(left2.left, left3)
                    return call(expr)

                return evaluate_c(left.left, left2)
            return call(expr)

        return evaluate_c(expr.left, left)
    if isinstance(expr, Expr):
        return call(expr)
    raise ValueError(f"bad try expr {expr}")


def evaluate_cons_c(a: Expr, b: Expr, call: Callable) -> Callable:
    """ Evaluate a cons, continuation passing style """
    logging.debug(f"evaluate_cons_c {unparse(a)} {unparse(b)}")

    def eval_a(eval_a):
        def eval_b(eval_b):
            def pair(pair):
                # Manually set value to prevent infinite loop
                res = Tree(pair, eval_b)
                res.value = res
                logging.debug(f'evaluated pair {unparse(a)},{unparse(b)} -> {unparse(res)}')
                return call(res)

            return evaluate_c(Tree(cons, eval_a), pair)

        return evaluate_c(b, eval_b)

    return evaluate_c(a, eval_a)


if __name__ == "__main__":
    import sys

    from expr import parse, unparse

    # TODO: remove
    state = nil
    event = Tree(Tree(cons, Value(0)), Value(0))
    # res = evaluate(Tree(Tree(Value(":1338"), state), event))
    # print(unparse(res))

    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")
