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
    return lambda: call


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
            logging.debug(f"DONE evaluated {unparse(orig)} -> {unparse(orig.value)}")
            return lambda: call(orig.value)

        def expr_fn(expr):
            return lambda: evaluate_compare_c(orig, expr, call)

        return lambda: evaluate_try_c(orig, expr_fn)
    raise ValueError(f"bad orig {orig}")


def evaluate_compare_c(orig: Expr, expr: Expr, call: Callable) -> Callable:
    """ Evaluate an expression until convergence, continuation passing style """
    logging.debug(f"evaluate_compare_c {unparse(orig)},{unparse(expr)}")
    if isinstance(orig, Expr) and isinstance(expr, Expr):

        def evaluation_fn(evaluation):
            if expr == evaluation:
                logging.debug(f"COMPARE success {unparse(expr)}")
                expr.value = evaluation
                return lambda: call(evaluation)
            return lambda: evaluate_compare_c(expr, evaluation, call)

        return lambda: evaluate_try_c(expr, evaluation_fn)
    raise ValueError(f"bad compare {orig},{expr}")


def evaluate_integer_c(expr: Expr, call: Callable) -> Callable:
    """ Evaluate to an integer, continuation passing style """
    logging.debug(f"evaluate_integer_c {unparse(expr)}")

    def integer(integer):
        if isinstance(integer, Value):
            return lambda: call(int(integer))
        raise ValueError(f"bad integer {integer}")

    return lambda: evaluate_c(expr, integer)


def evaluate_math_c(tree: Tree, call: Callable) -> Callable:
    """ Evaluate arithmetic, continuation passing style """
    logging.debug(f"evaluate_math_c {unparse(tree)}")
    if isinstance(tree, Tree):
        left = tree.left

        def x(x):
            if left == neg:
                return lambda: call(Value(-x))
            if left == inc:
                return lambda: call(Value(x + 1))
            if left == dec:
                return lambda: call(Value(x - 1))
            if isinstance(left, Tree):
                left2 = left.left

                def y(y):
                    if left2 == add:
                        return lambda: call(Value(y + x))
                    if left2 == mul:
                        return lambda: call(Value(y * x))
                    if left2 == div:
                        return lambda: call(Value(y // x if y * x > 0 else (y + (-y % x)) // x))
                    if left2 == lt:
                        return lambda: call(t if y < x else f)
                    if left2 == eq:
                        return lambda: call(t if y == x else f)
                    raise ValueError(f"bad binary math {tree}")

                return lambda: evaluate_integer_c(left.right, y)
            raise ValueError(f"bad unary math {tree}")

        return lambda: evaluate_integer_c(tree.right, x)
    raise ValueError(f"bad math {tree}")


def evaluate_try_c(expr: Expr, call: Callable) -> Callable:
    """ Try to evaluate an expression, continuation passing style """
    logging.debug(f"evaluate_try_c {unparse(expr)}")
    if isinstance(expr, Expr) and expr.value is not None:
        logging.debug(f"Evaluated already {unparse(expr)} -> {unparse(expr.value)}")
        return lambda: call(expr.value)
    if isinstance(expr, Value):
        if expr.name in functions:
            logging.debug(f"REPLACE {expr.name},{unparse(functions[expr.name])}")
            return lambda: call(functions[expr.name])  # type: ignore
        logging.debug(f"BARE VALUE {unparse(expr)}")
        return lambda: call(expr)
    if isinstance(expr, Tree):

        def left(left):
            logging.debug(f" eval try left {unparse(left)}")
            x = expr.right
            if left == i:
                return lambda: call(x)
            if left == nil:
                return lambda: call(t)
            if left == isnil:
                return lambda: call(Tree(x, Tree(t, Tree(t, f))))
            if left == car:
                return lambda: call(Tree(x, t))
            if left == cdr:
                return lambda: call(Tree(x, f))
            if left in UNARY_MATH:
                return lambda: evaluate_math_c(expr, call)
            if isinstance(left, Tree):
                logging.debug("left is instance of tree")

                def left2(left2):
                    y = left.right
                    if left2 == t:
                        return lambda: call(y)
                    if left2 == f:
                        return lambda: call(x)
                    if left2 == cons:
                        return lambda: evaluate_cons_c(y, x, call)
                    if left2 in BINARY_MATH:
                        return lambda: evaluate_math_c(expr, call)
                    if isinstance(left2, Tree):

                        def left3(left3):
                            z = left2.right
                            if left3 == s:
                                return lambda: call(Tree(Tree(z, x), Tree(y, x)))
                            if left3 == c:
                                logging.debug(f"C COMBINATOR (removed) z-> {unparse(z)}")
                                logging.debug(f"C COMBINATOR y-> {unparse(y)}")
                                logging.debug(f"C COMBINATOR x-> {unparse(x)}")
                                logging.debug(f"C COMBINATOR -> {unparse(Tree(Tree(x, x), y))}")
                                return lambda: call(Tree(Tree(x, x), y))
                            if left3 == b:
                                logging.debug(f"B COMBINATOR z-> {unparse(z)}")
                                logging.debug(f"B COMBINATOR y-> {unparse(y)}")
                                logging.debug(f"B COMBINATOR x-> {unparse(x)}")
                                logging.debug(f"B COMBINATOR -> {unparse(Tree(z, Tree(y, x)))}")
                                return lambda: call(Tree(z, Tree(y, x)))
                            if left3 == cons:
                                return lambda: call(Tree(Tree(x, z), y))
                            return lambda: call(expr)

                        return lambda: evaluate_c(left2.left, left3)
                    return lambda: call(expr)

                return lambda: evaluate_c(left.left, left2)
            logging.debug(f" left try found no match {unparse(expr)}")
            return lambda: call(expr)

        return lambda: evaluate_c(expr.left, left)  # type: ignore
    if isinstance(expr, Expr):
        return lambda: call(expr)
    raise ValueError(f"bad try expr {expr}")


def evaluate_cons_c(y: Expr, x: Expr, call: Callable) -> Callable:
    """ Evaluate a cons, continuation passing style """
    logging.debug(f"evaluate_cons_c {unparse(y)} {unparse(x)}")

    def eval_y(eval_y):
        def eval_x(eval_x):
            def pair(pair):
                # Manually set value to prevent infinite loop
                res = Tree(pair, eval_x)
                res.value = res
                logging.debug(
                    f"evaluated pair {unparse(y)},{unparse(x)} -> {unparse(res)}"
                )
                return lambda: call(res)

            return lambda: evaluate_c(Tree(cons, eval_y), pair)

        return lambda: evaluate_c(x, eval_x)

    return lambda: evaluate_c(y, eval_y)


if __name__ == "__main__":
    import sys

    from expr import parse, unparse

    # TODO: remove
    # state = nil
    # event = Tree(Tree(cons, Value(0)), Value(0))
    # res = evaluate(Tree(Tree(Value(":1338"), state), event))
    # print(unparse(res))
    # evaluate(parse("ap inc 0"))
    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")
