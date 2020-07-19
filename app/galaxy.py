#!/usr/bin/env python
import sys

sys.setrecursionlimit(15000)

from dataclasses import dataclass
from typing import Optional, NamedTuple, Dict, Tuple, Any, Union, List

from tree import Treeish, Tree, Value, Procedure
from serial import deserialize
from modulate import modulate, demodulate


class Vect(NamedTuple):
    X: int
    Y: int


cons = Value('cons')
t = Value('t')
f = Value('f')
nil = Value('nil')


def PARSE_FUNCTIONS(filename) -> Dict[str, Treeish]:
    d: Dict[str, Treeish] = {}
    for line in open(filename).readlines():
        # print("parsing line", line[:100])
        name, string = line.strip().split("=")
        d[name.strip()] = deserialize(string)
    return d


functions: Dict[str, Treeish] = PARSE_FUNCTIONS("galaxy.txt")

# See https://message-from-space.readthedocs.io/en/latest/message39.html
state: Treeish = nil
vector: Vect = Vect(0, 0)


def PRINT_IMAGES(images: Treeish) -> None:
    print("Printing images")
    print(images)


def REQUEST_CLICK_FROM_USER() -> Vect:
    print("Getting vector from user")
    vector = Vect(0, 0)
    print("Got vector", vector)
    return vector


# See https://message-from-space.readthedocs.io/en/latest/message38.html
def interact(state: Treeish, event: Treeish) -> Tuple[Treeish, Treeish]:
    expr: Treeish = Tree(Tree(Value('galaxy'), state), event)
    res: Treeish = evaluate(expr)
    # Note: res will be modulatable here (consists of cons, nil and numbers only)
    demodulate(modulate(res))  # Check that res is modulatable
    flag, newState, data = GET_LIST_ITEMS_FROM_EXPR(res)
    if asNum(flag) == 0:
        return (newState, data)
    return interact(newState, SEND_TO_ALIEN_PROXY(data))


def evaluate(expr: Treeish) -> Treeish:
    if isinstance(expr, Tree):
        if expr.evaluated is not None:
            return expr.evaluated
        initialEval = expr
        while True:
            result: Treeish = tryEval(expr)
            if result == expr:
                initialEval.evaluated = result
                return result
            expr = result
    raise ValueError(f"Cant evaluate non tree {expr}")


def tryEval(expr: Treeish) -> Treeish:
    # Handle the non tree types
    if expr is None:
        return None
    if isinstance(expr, Value):
        return expr
    if isinstance(expr, Procedure):
        return Procedure
    if not isinstance(expr, Tree):
        raise ValueError(f"tryEval {expr} type {type(expr)}")
    # Handle tree types
    if expr.evaluated is not None:
        return expr.evaluated
    if isinstance(expr, Atom) and expr.Name in functions:
        return functions[expr.Name]
    if isinstance(expr, Ap):
        fun: Treeish = evaluate(expr.Fun)
        x: Treeish = expr.Arg
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
            fun2: Treeish = evaluate(fun.Fun)
            y: Treeish = fun.Arg
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
                    return Atom(asNum(evaluate(y)) / asNum(evaluate(x)))
                if fun2.Name == "lt":
                    return t if asNum(evaluate(y)) < asNum(evaluate(x)) else f
                if fun2.Name == "eq":
                    return t if asNum(evaluate(x)) == asNum(evaluate(y)) else f
                if fun2.Name == "cons":
                    return evalCons(y, x)
            if isinstance(fun2, Ap):
                fun3: Treeish = evaluate(fun2.Fun)
                z: Treeish = fun2.Arg
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


def evalCons(a: Treeish, b: Treeish) -> Treeish:
    res = Tree(Tree(cons, evaluate(a)), evaluate(b))
    res.evaluated = res
    return res


def asNum(n: Treeish) -> int:
    if isinstance(n, Value):
        return int(n.value)
    raise ValueError(f"not a number {n}")


while True:
    click: Treeish = Tree(Tree(cons, Value(vector.X)), Value(vector.Y))
    newState, images = interact(state, click)
    PRINT_IMAGES(images)
    vector = REQUEST_CLICK_FROM_USER()
    state = newState
