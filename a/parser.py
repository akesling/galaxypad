#!/usr/bin/env python
import re
import sys
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, Dict, NamedTuple

sys.setrecursionlimit(10000)
INT_REGEX = re.compile(r"(-?\d+)")


class Expr:
    """ Expressions are nodes on our parse tree """

    Evaluated: Optional["Expr"]

    def __init__(self, Evaluated: Optional["Expr"] = None):
        assert Evaluated is None or isinstance(Evaluated, Expr), repr(Evaluated)
        self.Evaluated = Evaluated

    def __repr__(self):
        fields = ",".join(
            f"{k}={repr(v)}" for k, v in vars(self).items() if k is not "Evaluated"
        )
        return f"{self.__class__.__name__}({fields})"

    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class Value(Expr):
    """ Atoms are the leaves of our tree """

    Name: Union[str, int]

    def __init__(self, Name: Union[str, int], *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Name, (str, int)), repr(Name)
        self.Name = Name

    def is_int(self):
        return isinstance(self.Name, int) or INT_REGEX.fullmatch(self.Name) is not None


def asNum(n: Expr) -> int:
    if isinstance(n, Value):
        return int(n.Name)
    raise ValueError(f"not a number {n}")


class Tree(Expr):
    """ Applications (of a function) are the non-leaf nodes of our tree """

    Left: Expr
    Right: Expr

    def __init__(self, Left: Expr, Right: Expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Left, Expr) and isinstance(Right, Expr), repr(Left) + repr(
            Right
        )
        self.Left = Left
        self.Right = Right


class Vector(Expr):
    Elements: List[Union[List, int]]

    def __init__(self, Elements: List[Union[List, int]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Elements, list), repr(Elements)
        self.Elements = Elements


class Vect(NamedTuple):
    """ X, Y coordinate """

    X: int
    Y: int


# VECTOR_DETECTOR = re.compile(r"((ap\s+ap\s+cons|\d+|nil)\s+)+nil")
cons: Expr = Value("cons")
t: Expr = Value("t")
f: Expr = Value("f")
nil: Expr = Value("nil")


def parse(expression: str) -> Expr:
    """ Parse a complete expression """
    expr, tokens = parse_tokens(expression.strip().split())
    assert tokens == [], f"Leftover tokens {expression} -> {tokens}"
    return expr


# def parse_vector(tokens: List[str]) -> Tuple[Expr, List[str]]:
#     """ Special handling for vectors since they can get very deep """
#     assert tokens[:3] == 'ap ap cons'.split(), repr(tokens)

#     assert False, tokens


def maybe_vector(expr: Expr) -> Expr:
    """ Try to compress a vector if possible """
    if isinstance(expr, Tree):
        left = expr.Left
        if isinstance(left, Tree) and left.Left == cons:  # Possible vector
            lr = maybe_vector(left.Right)
            right = maybe_vector(expr.Right)
            if right == nil:
                right_vector: List[Union[List, int]] = []  # Vector end
            elif isinstance(right, Vector):
                right_vector = right.Elements  # Nested
            else:
                return expr  # Not a valid vector
            if isinstance(lr, Value) and lr.is_int():
                lr_vector: List[Union[List, int]] = [asNum(lr)]  # Base case
            elif isinstance(lr, Vector):
                lr_vector = [lr.Elements]  # Appending
            else:
                return expr  # Not a valid vector
            return Vector(lr_vector + right_vector)
    return expr

    # left = tree.Left
    # if not isinstance(left, Tree) or left.Left != cons:
    #     return tree


def parse_tokens(tokens: List[str]) -> Tuple[Expr, List[str]]:
    """ Parse and return a complete expression, and leftover tokens """
    token, *tokens = tokens
    if token == "ap":
        left, tokens = parse_tokens(tokens)
        right, tokens = parse_tokens(tokens)
        expr = Tree(Left=left, Right=right)
        return maybe_vector(expr), tokens
    return Value(token), tokens


def parse_file(filename: str) -> Dict[str, Expr]:
    """ Parse a file into a map of names to expressions """
    functions = {}
    for line in open(filename).readlines():
        name, _, *tokens = line.strip().split()
        expr, leftover = parse_tokens(tokens)
        assert leftover == [], f"Got leftover tokens {line} -> {tokens}"
        functions[name] = expr
    return functions


functions: Dict[str, Expr] = {}  # parse_file("galaxy.txt")


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
    if (
        isinstance(expr, Value)
        and isinstance(expr.Name, str)
        and expr.Name in functions
    ):
        return functions[expr.Name]
    if isinstance(expr, Tree):
        left: Expr = evaluate(expr.Left)
        x: Expr = expr.Right
        if isinstance(left, Value):
            if left.Name == "neg":
                return Value(-asNum(evaluate(x)))
            if left.Name == "i":
                return x
            if left.Name == "nil":
                return t
            if left.Name == "isnil":
                return Tree(x, Tree(t, Tree(t, f)))
            if left.Name == "car":
                return Tree(x, t)
            if left.Name == "cdr":
                return Tree(x, f)
        if isinstance(left, Tree):
            left2: Expr = evaluate(left.Left)
            y: Expr = left.Right
            if isinstance(left2, Value):
                if left2.Name == "t":
                    return y
                if left2.Name == "f":
                    return x
                if left2.Name == "add":
                    return Value(asNum(evaluate(x)) + asNum(evaluate(y)))
                if left2.Name == "mul":
                    return Value(asNum(evaluate(x)) * asNum(evaluate(y)))
                if left2.Name == "div":
                    a, b = asNum(evaluate(y)), asNum(evaluate(x))
                    return Value(a // b if a * b > 0 else (a + (-a % b)) // b)
                if left2.Name == "lt":
                    return t if asNum(evaluate(y)) < asNum(evaluate(x)) else f
                if left2.Name == "eq":
                    return t if asNum(evaluate(x)) == asNum(evaluate(y)) else f
                if left2.Name == "cons":
                    return evalCons(y, x)
            if isinstance(left2, Tree):
                left3: Expr = evaluate(left2.Left)
                z: Expr = left2.Right
                if isinstance(left3, Value):
                    if left3.Name == "s":
                        return Tree(Tree(z, x), Tree(y, x))
                    if left3.Name == "c":
                        return Tree(Tree(z, x), y)
                    if left3.Name == "b":
                        return Tree(z, Tree(y, x))
                    if left3.Name == "cons":
                        return Tree(Tree(x, z), y)
    return expr


def evalCons(a: Expr, b: Expr) -> Expr:
    """ Evaluate a pair """
    res: Expr = Tree(Tree(cons, evaluate(a)), evaluate(b))
    res.Evaluated = res
    return res


# See https://message-from-space.readthedocs.io/en/latest/message38.html
def interact(state: Expr, event: Expr) -> Tuple[Expr, Expr]:
    """ Interact with the game """
    expr: Expr = Tree(Tree(Value("galaxy"), state), event)
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


def GET_LIST_ITEMS_FROM_EXPR(res: Expr) -> Tuple[Value, Expr, Expr]:
    return Value("0"), Expr(), Expr()


if __name__ == "__main__":
    # state: Expr = nil
    # vector: Vect = Vect(0, 0)

    # # main loop
    # for _ in range(10):  # while True:
    #     click: Expr = Tree(Tree(cons, Value(vector.X)), Value(vector.Y))
    #     newState, images = interact(state, click)
    #     PRINT_IMAGES(images)
    #     vector = REQUEST_CLICK_FROM_USER()
    #     state = newState
    print(evaluate(parse("ap ap cons 0 nil")))

