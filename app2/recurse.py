#!/usr/bin/env python


#!/usr/bin/env python

from expr import Expr, Value, Tree
from typing import Callable, Any

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


def evaluate(expr: Expr) -> Expr:
    """ Evaluate an expression, returning evaluated tree """
    evaluation = evaluate_r(expr)
    if isinstance(evaluation, Expr):
        return evaluation
    raise ValueError(f"bad evalution {evaluation}")


def evaluate_r(expr: Expr) -> Expr:
    """ Evaluate an expression, recursive style """
    if isinstance(expr, Value):
        return expr
    if isinstance(expr, Tree):
        value = evaluate_tree_r(expr)
        expr.value = value
        return value
    raise ValueError(f"bad expr {expr}")


def evaluate_int_r(expr: Expr) -> int:
    """ Evaluate to an integer, recursive style """
    value = evaluate_r(expr)
    if isinstance(value, Value):
        return int(value)
    raise ValueError(f"bad value {value}")


def is_math_expr(expr: Expr) -> bool:
    """ Return if this tree can be evaluated as arithmetic """
    return isinstance(expr, Tree) and (
        expr.left == neg
        or (isinstance(expr.left, Tree) and expr.left.left in BINARY_MATH)
    )


def evaluate_math_r(tree: Tree) -> Value:
    """ Evaluate """
    if isinstance(tree, Tree):
        left = tree.left
        x = evaluate_int_r(tree.right)
        if left == neg:
            return Value(-x)
        if left == inc:
            return Value(x + 1)
        if left == dec:
            return Value(x - 1)
        if isinstance(left, Tree):
            left2 = left.left
            y = evaluate_int_r(left.right)
            if left2 == add:
                return Value(y + x)
            if left2 == mul:
                return Value(y * x)
            if left2 == div:
                return Value(y // x if y * x > 0 else (y + (-y % x)) // x)
            if left2 == lt:
                return t if y < x else f
            if left2 == eq:
                return t if y == x else f
    raise ValueError(f"bad math {tree}")


def evaluate_tree_r(tree: Tree) -> Expr:
    """ Evaluate a tree, recursive style """
    if isinstance(tree, Tree):
        if tree.value is not None:
            return tree.value

        left = evaluate_r(tree.left)
        x = tree.right
        if left == i:
            return x
        if left == nil:
            return t
        if left == isnil:
            return Tree(x, Tree(t, Tree(t, f)))
        if left == car:
            return Tree(x, t)
        if left == cdr:
            return Tree(x, f)
        if left in UNARY_MATH:
            return evaluate_math_r(tree)
        if isinstance(left, Tree):
            left2 = evaluate_r(left.left)
            y = left.right
            if left2 == t:
                return y
            if left2 == f:
                return x
            if left2 == cons:
                return evaluate_cons_r(y, x)
            if left2 in BINARY_MATH:
                return evaluate_math_r(tree)
            if isinstance(left2, Tree):
                left3 = evaluate_r(left2.left)
                z = left2.right
                if left3 == s:
                    return Tree(Tree(z, x), Tree(y, x))
                if left3 == c:
                    return Tree(Tree(x, x), y)
                if left3 == b:
                    return Tree(z, Tree(y, x))
                if left3 == cons:
                    return Tree(Tree(x, z), y)
        return tree
    raise ValueError(f"bad tree {tree}")


def evaluate_cons_r(a: Expr, b: Expr) -> Expr:
    """ Evaluate a cons, recursive style """
    eval_a = evaluate_r(a)
    eval_b = evaluate_r(b)
    pair = evaluate_r(Tree(cons, eval_a))
    # Manually set value to prevent infinite loop
    res = Tree(pair, eval_b)
    res.value = res
    return res


if __name__ == "__main__":
    import sys

    from expr import parse, unparse
    evaluate(parse('ap ap cons 0 nil'))

    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")
