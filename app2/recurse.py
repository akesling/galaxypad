#!/usr/bin/env python

from expr import Expr, Value, Tree, parse_tokens, nlr
from typing import Callable, Any, Dict

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


functions: Dict[str, Expr] = {}
for line in open("galaxy.txt").readlines():
    name, _, *tokens = line.strip().split()
    functions[name] = parse_tokens(tokens)


def insert(old: Expr, new: Expr) -> Expr:
    if old is new or old == new:
        return new
    for parent in old.parents:
        if isinstance(parent, Tree):
            if parent.left is old:
                parent.left = new
            if parent.right is old:
                parent.right = new
            new.parents.append(parent)
        else:
            raise ValueError(f"Non tree parent {parent}->{old}:{new}")
    return new


def evaluate(orig: Expr) -> Expr:
    """ Evaluate an expression, returning evaluated tree """
    again = True
    while again:
        print("evaluate", unparse(orig))
        again = False
        for expr in nlr(orig):
            result = try_eval(expr)
            if expr is orig:
                orig = result
            if result is not expr:
                insert(expr, result)
                again = True
                break
    return orig


def try_eval(expr: Expr) -> Expr:
    """ Evaluate a expr, recursive style """
    if isinstance(expr, Value) and expr.name in functions:
        return functions[expr.name]
    if isinstance(expr, Tree):
        left = expr.left
        x = expr.right
        if left == neg:
            return Value(-eval_int(x))
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

        if isinstance(left, Tree):
            left2 = left.left
            y = left.right
            if left2 == t:
                return y
            if left2 == f:
                return x
            if left2 == cons:
                return Tree(Tree(cons, evaluate(y)), evaluate(x))
            if left2 == add:
                return Value(eval_int(y) + eval_int(x))
            if left2 == mul:
                return Value(eval_int(y) * eval_int(x))
            if left2 == div:
                y, x = eval_int(y), eval_int(x)  # type: ignore
                return Value(y // x if y * x > 0 else (y + (-y % x)) // x)  # type: ignore
            if left2 == lt:
                return t if eval_int(y) < eval_int(x)else f
            if left2 == eq:
                return t if eval_int(y) == eval_int(x) else f
            if isinstance(left2, Tree):
                left3 = left2.left
                z = left2.right
                if left3 == s:
                    return Tree(Tree(z, x), Tree(y, x))
                if left3 == c:
                    return Tree(Tree(x, x), y)
                if left3 == b:
                    return Tree(z, Tree(y, x))
                if left3 == cons:
                    return Tree(Tree(x, z), y)
    return expr



def eval_int(expr: Expr) -> int:
    """ Evaluate an expression to an int """
    value = evaluate(expr)
    if isinstance(value, Value):
        return int(value)
    raise ValueError(f"failed to convert to int {expr} -> {value}")


if __name__ == "__main__":
    import sys

    from expr import parse, unparse

    if len(sys.argv) == 2:
        print(unparse(evaluate(parse(sys.argv[1]))))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")
