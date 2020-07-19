#!/usr/bin/env python
import re
import sys
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, Dict, NamedTuple

# sys.setrecursionlimit(10000)
INT_REGEX = re.compile(r"(-?\d+)")


class Expr:
    """ Expressions are nodes on our parse tree """

    Evaluated: Optional["Expr"]


@dataclass
class Value(Expr):
    """ Atoms are the leaves of our tree """

    Name: Optional[Union[str, int]] = None

    def is_int(self):
        return isinstance(self.Name, int) or INT_REGEX.fullmatch(self.Name) is not None


def asNum(n: Expr) -> int:
    if isinstance(n, Value) and n.Name is not None:
        return int(n.Name)
    raise ValueError(f"not a number {n}")


@dataclass
class Tree(Expr):
    """ Applications (of a function) are the non-leaf nodes of our tree """

    Left: Optional[Expr] = None
    Right: Optional[Expr] = None


nil: Expr = Value("nil")


@dataclass
class Vector(Expr):
    Elements: Optional[List[Union[List, int]]] = None

    def car(self) -> Expr:
        assert isinstance(self.Elements, list), self
        head = self.Elements[0]
        if isinstance(head, int):
            return Value(head)
        if isinstance(head, list) and len(head):
            return Vector(head)
        raise ValueError(f"bad head {head}")

    def cdr(self) -> Expr:
        assert isinstance(self.Elements, list), self
        tail = self.Elements[1:]
        if len(tail):
            return Vector(tail)
        return nil


class Vect(NamedTuple):
    """ X, Y coordinate """

    X: int
    Y: int


# VECTOR_DETECTOR = re.compile(r"((ap\s+ap\s+cons|\d+|nil)\s+)+nil")
cons: Expr = Value("cons")
t: Expr = Value("t")
f: Expr = Value("f")


# def parse(expression: str) -> Expr:
#     """ Parse a complete expression """
#     expr, tokens = parse_tokens(expression.strip().split())
#     assert tokens == [], f"Leftover tokens {expression} -> {tokens}"
#     return expr


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


def check_expr_inner(expr: Expr) -> None:
    assert isinstance(expr, (Value, Vector, Tree)), f"type(expr) {type(expr)}"
    if isinstance(expr, Tree):
        check_expr(expr.Left)
        check_expr(expr.Right)


def check_expr(expr: Expr) -> None:
    try:
        check_expr_inner(expr)
    except Exception as e:
        raise ValueError(f"Bad {expr} \n {e}")


# def parse_tokens(tokens: List[str]) -> Tuple[Expr, List[str]]:
#     """ Parse and return a complete expression, and leftover tokens """
#     token, *tokens = tokens
#     if token == "ap":
#         left, tokens = parse_tokens(tokens)
#         right, tokens = parse_tokens(tokens)
#         expr = Tree(Left=left, Right=right)
#         check_expr(expr)
#         return maybe_vector(expr), tokens
#     return Value(token), tokens


def parse(orig: Union[str, List[str]]) -> Expr:
    """ Parse and return a complete expression, and leftover tokens """
    tokens: List[str] = orig.strip().split() if isinstance(orig, str) else orig
    orig_str: str = ' '.join(tokens)
    stack: List[Tree] = []
    expr: Optional[Expr] = None  # Contains the object to return at the end
    while tokens:
        token, *tokens = tokens
        # print("parser step")
        # print("stack", stack)
        # print("token[s]", token, tokens)
        expr = Tree() if token == "ap" else Value(token)
        if stack:
            if stack[-1].Left is None:
                # print("Connecting to stack head left")
                stack[-1].Left = expr
            elif stack[-1].Right is None:
                # print("Connecting to stack head right")
                stack[-1].Right = expr
                if isinstance(expr, Tree):
                    # print("Append Expr", expr)
                    stack.append(expr)
            else:
                raise ValueError(f"Parser shouldn't have complete tree in stack! {orig_str}")
            while stack and stack[-1].Left is not None and stack[-1].Right is not None:
                expr = stack.pop()
        # print("Got expr", expr)
        if isinstance(expr, Tree) and (expr.Left is None or expr.Right is None):
            stack.append(expr)
        if not len(stack):
            # print("Breaking, stack", stack)
            break

    assert tokens == [], f"Failed to parse tokens {orig_str} -> {tokens}"
    assert isinstance(expr, Expr), f"Failed to parse tokens {orig_str}"
    return expr


def parse_file(filename: str) -> Dict[str, Expr]:
    """ Parse a file into a map of names to expressions """
    functions = {}
    for line in open(filename).readlines():
        name, _, *tokens = line.strip().split()
        functions[name] = parse(tokens)
    return functions


functions: Dict[str, Expr] = {} # parse_file("galaxy.txt")


def evaluate(expr: Expr) -> Expr:
    """ Evaluate a node in the tree """
    check_expr(expr)
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
    check_expr(expr)
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
        check_expr(left)
        check_expr(x)
        print("left", type(left))
        print("x", type(x))
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
                if isinstance(x, Vector):
                    return x.car()
                return Tree(x, t)
            if left.Name == "cdr":
                if isinstance(x, Vector):
                    return x.cdr()
                return Tree(x, f)
        if isinstance(left, Tree):
            left2: Expr = evaluate(left.Left)
            y: Expr = left.Right
            check_expr(left2)
            check_expr(y)
            print("left2", type(left2))
            print("y", type(y))
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
                    return t if asNum(evaluate(y)) == asNum(evaluate(x)) else f
                if left2.Name == "cons":
                    return evalCons(y, x)
            if isinstance(left2, Tree):
                left3: Expr = evaluate(left2.Left)
                z: Expr = left2.Right
                check_expr(left3)
                check_expr(z)
                if isinstance(left3, Value):
                    if left3.Name == "s":
                        return Tree(Tree(z, x), Tree(y, x))
                    if left3.Name == "c":
                        return Tree(Tree(z, x), y)
                    if left3.Name == "b":
                        return Tree(z, Tree(y, x))
                    if left3.Name == "cons":
                        return maybe_vector(Tree(Tree(x, z), y))
    return expr


def evalCons(a: Expr, b: Expr) -> Expr:
    """ Evaluate a pair """
    res: Expr = Tree(Tree(cons, evaluate(a)), evaluate(b))
    res = maybe_vector(res)
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
    assert False


if __name__ == "__main__":
    # state: Expr = nil
    # vector: Vect = Vect(0, 0)

    # # main loop
    # for _ in range(1):  # while True:
    #     click: Expr = Tree(Tree(cons, Value(vector.X)), Value(vector.Y))
    #     newState, images = interact(state, click)
    #     PRINT_IMAGES(images)
    #     vector = REQUEST_CLICK_FROM_USER()
    #     state = newState
    print(parse("ap ap cons 7 ap ap cons 123 nil"))
    print(parse('ap ap cons ap ap cons 0 ap ap cons ap ap :1162 14 ap neg 64 ap ap cons :1043 ap ap cons :1059 ap ap cons ap neg 1 nil ap ap cons ap ap cons 1 ap ap cons ap ap :1162 ap neg 4 94 ap ap cons :1044 ap ap cons :1060 ap ap cons 2 nil ap ap cons ap ap cons 2 ap ap cons ap ap :1162 ap neg 78 ap neg 67 ap ap cons :1045 ap ap cons :1061 ap ap cons 1 nil ap ap cons ap ap cons 3 ap ap cons ap ap :1162 ap neg 38 ap neg 46 ap ap cons :1046 ap ap cons :1062 ap ap cons ap neg 1 nil ap ap cons ap ap cons 4 ap ap cons ap ap :1162 44 ap neg 34 ap ap cons :1047 ap ap cons :1063 ap ap cons ap neg 1 nil ap ap cons ap ap cons 5 ap ap cons ap ap :1162 60 ap neg 30 ap ap cons :1048 ap ap cons :1064 ap ap cons 3 nil ap ap cons ap ap cons 6 ap ap cons ap ap :1162 ap neg 81 11 ap ap cons :1049 ap ap cons :1065 ap ap cons 0 nil ap ap cons ap ap cons 7 ap ap cons ap ap :1162 ap neg 49 34 ap ap cons :1050 ap ap cons :1066 ap ap cons ap neg 1 nil ap ap cons ap ap cons 8 ap ap cons ap ap :1162 52 27 ap ap cons :1051 ap ap cons :1067 ap ap cons ap neg 1 nil ap ap cons ap ap cons 9 ap ap cons ap ap :1162 99 15 ap ap cons :1052 ap ap cons :1068 ap ap cons ap neg 1 nil ap ap cons ap ap cons 10 ap ap cons ap ap :1162 96 35 ap ap cons :1053 ap ap cons :1069 ap ap cons ap neg 1 nil nil'))
    parse_file('galaxy.txt')