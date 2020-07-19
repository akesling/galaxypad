#!/usr/bin/env python
import sys
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, Dict, NamedTuple

sys.setrecursionlimit(10000)


class Expr:
    """ Expressions are nodes on our parse tree """

    Evaluated: Optional["Expr"]

    def __init__(self, Evaluated: Optional["Expr"] = None):
        assert Evaluated is None or isinstance(Evaluated, Expr), repr(Evaluated)
        self.Evaluated = Evaluated

    def __repr__(self):
        fields = ",".join(f"{k}={repr(v)}" for k, v in sorted(vars(self).items()))
        return f"{self.__class__.__name__}({fields})"

    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class Atom(Expr):
    """ Atoms are the leaves of our tree """

    Name: Union[str, int]

    def __init__(self, Name: Union[str, int], *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Name, (str, int)), repr(Name)
        self.Name = Name


class Ap(Expr):
    """ Applications (of a function) are the non-leaf nodes of our tree """

    Fun: Expr
    Arg: Expr

    def __init__(self, Fun: Expr, Arg: Expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Fun, Expr) and isinstance(Arg, Expr), repr(Fun) + repr(Arg)
        self.Fun = Fun
        self.Arg = Arg


class Vect(NamedTuple):
    """ X, Y coordinate """

    X: int
    Y: int


def parse(expression: str) -> Expr:
    """ Parse a complete expression """
    expr, tokens = parse_tokens(expression.strip().split())
    assert tokens == [], f"Leftover tokens {expression} -> {tokens}"
    return expr


def parse_tokens(tokens: List[str]) -> Tuple[Expr, List[str]]:
    """ Parse and return a complete expression, and leftover tokens """
    token, *tokens = tokens
    if token == "ap":
        fun, tokens = parse_tokens(tokens)
        arg, tokens = parse_tokens(tokens)
        return Ap(Fun=fun, Arg=arg), tokens
    return Atom(token), tokens


def parse_file(filename: str) -> Dict[str, Expr]:
    """ Parse a file into a map of names to expressions """
    functions = {}
    for line in open(filename).readlines():
        name, _, *tokens = line.strip().split()
        expr, leftover = parse_tokens(tokens)
        assert leftover == [], f"Got leftover tokens {line} -> {tokens}"
        functions[name] = expr
    return functions


cons: Expr = Atom("cons")
t: Expr = Atom("t")
f: Expr = Atom("f")
nil: Expr = Atom("nil")

functions: Dict[str, Expr] = parse_file("galaxy.txt")


def evaluate(expr: Expr) -> Expr:
    """ Evaluate a node in the tree """
    if expr.Evaluated is not None:
        return expr.Evaluated
    initialExpr: Expr = expr
    while True:
        result: Expr = tryEval(expr)
        if result == expr:
            initialExpr.Evaluated = result
            return result
        expr = result


def tryEval(expr: Expr) -> Expr:
    """ Try to perform a computation or reduction on the tree """
    if expr.Evaluated is not None:
        return expr.Evaluated
    if isinstance(expr, Atom) and isinstance(expr.Name, str) and expr.Name in functions:
        return functions[expr.Name]
    if isinstance(expr, Ap):
        fun: Expr = evaluate(expr.Fun)
        x: Expr = expr.Arg
        if isinstance(fun, Atom):
            if fun.Name == "neg":
                return Atom(-asNum(evaluate(x)))
            if fun.Name == "i":
                return x
            if fun.Name == "nil":
                return t
            if fun.Name == "isnil":
                return Ap(x, Ap(t, Ap(t, f)))
            if fun.Name == "car":
                return Ap(x, t)
            if fun.Name == "cdr":
                return Ap(x, f)
        if isinstance(fun, Ap):
            fun2: Expr = evaluate(fun.Fun)
            y: Expr = fun.Arg
            if isinstance(fun2, Atom):
                if fun2.Name == "t":
                    return y
                if fun2.Name == "f":
                    return x
                if fun2.Name == "add":
                    return Atom(asNum(evaluate(x)) + asNum(evaluate(y)))
                if fun2.Name == "mul":
                    return Atom(asNum(evaluate(x)) * asNum(evaluate(y)))
                if fun2.Name == "div":
                    a, b = asNum(evaluate(y)), asNum(evaluate(x))
                    return Atom(a // b if a * b > 0 else (a + (-a % b)) // b)
                if fun2.Name == "lt":
                    return t if asNum(evaluate(y)) < asNum(evaluate(x)) else f
                if fun2.Name == "eq":
                    return t if asNum(evaluate(x)) == asNum(evaluate(y)) else f
                if fun2.Name == "cons":
                    return evalCons(y, x)
            if isinstance(fun2, Ap):
                fun3: Expr = evaluate(fun2.Fun)
                z: Expr = fun2.Arg
                if isinstance(fun3, Atom):
                    if fun3.Name == "s":
                        return Ap(Ap(z, x), Ap(y, x))
                    if fun3.Name == "c":
                        return Ap(Ap(z, x), y)
                    if fun3.Name == "b":
                        return Ap(z, Ap(y, x))
                    if fun3.Name == "cons":
                        return Ap(Ap(x, z), y)
    return expr


def evalCons(a: Expr, b: Expr) -> Expr:
    """ Evaluate a pair """
    res: Expr = Ap(Ap(cons, evaluate(a)), evaluate(b))
    res.Evaluated = res
    return res


def asNum(n: Expr) -> int:
    if isinstance(n, Atom):
        return int(n.Name)
    raise ValueError(f"not a number {n}")


# See https://message-from-space.readthedocs.io/en/latest/message38.html
def interact(state: Expr, event: Expr) -> Tuple[Expr, Expr]:
    """ Interact with the game """
    expr: Expr = Ap(Ap(Atom("galaxy"), state), event)
    res: Expr = evaluate(expr)
    # Note: res will be modulatable here (consists of cons, nil and numbers only)
    flag, newState, data = GET_LIST_ITEMS_FROM_EXPR(res)
    if asNum(flag) == 0:
        return (newState, data)
    return interact(newState, SEND_TO_ALIEN_PROXY(data))


# Stubs
def PRINT_IMAGES(images: Expr) -> None:
    pass


def REQUEST_CLICK_FROM_USER() -> Vect:
    return Vect(0, 0)


def SEND_TO_ALIEN_PROXY(data: Expr) -> Expr:
    return data


def GET_LIST_ITEMS_FROM_EXPR(res: Expr) -> Tuple[Atom, Expr, Expr]:
    return Atom("0"), Expr(), Expr()


if __name__ == "__main__":
    state: Expr = nil
    vector: Vect = Vect(0, 0)


    # main loop
    for _ in range(10):  # while True:
        click: Expr = Ap(Ap(cons, Atom(vector.X)), Atom(vector.Y))
        newState, images = interact(state, click)
        PRINT_IMAGES(images)
        vector = REQUEST_CLICK_FROM_USER()
        state = newState
