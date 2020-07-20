#!/usr/bin/env python
import re
import os
import sys
import math

# from dataclasses import dataclass
from itertools import zip_longest
from random import randint
from typing import (
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
    Any,
    Sequence,
)

import requests
import sdl2.ext

sys.setrecursionlimit(10000)


class Value:
    """ Atoms are the leaves of our tree """

    name: str
    Evaluated: Optional["Expr"] = None

    def __init__(self, name: Union[str, int]):
        self.name = str(name)
        self.Evaluated = None

    def nlr(self) -> Iterable["Expr"]:
        yield self

    def __eq__(self, other):
        if type(self) == type(other):
            return self.name == other.name
        return False

    def __int__(self) -> int:
        return int(self.name)

    def unparse(self) -> str:
        assert self.name is not None, self
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.name)})"

    def __str__(self) -> str:
        # TODO: deduplicate with unparse
        assert self.name is not None, self
        return self.name


class Tree:
    """ Applications (of a function) are the non-leaf nodes of our tree """

    left: Optional["Expr"] = None
    right: Optional["Expr"] = None
    Evaluated: Optional["Expr"] = None

    def __init__(self, left: Optional["Expr"] = None, right: Optional["Expr"] = None):
        self.left = left
        self.right = right
        self.Evaluated = None

    def nlr(self) -> Iterable["Expr"]:
        """ Generator for all of the Tree nodes in preorder (NLR) """
        stack: List["Expr"] = [self]
        while stack:
            expr: "Expr" = stack.pop()
            yield expr
            if isinstance(expr, Tree):
                assert isinstance(expr.right, (Value, Tree)), f"{expr.right}"
                stack.append(expr.right)
                assert isinstance(expr.left, (Value, Tree)), f"{expr.left}"
                stack.append(expr.left)

    def __eq__(self, other) -> bool:
        """ Non recursive equality checking """
        if type(self) == type(other):
            is_value = lambda expr: isinstance(expr, Value)
            self_itr = filter(is_value, self.nlr())
            other_itr = filter(is_value, other.nlr())
            return all(s == o for s, o in zip_longest(self_itr, other_itr))
        return False

    def unparse(self) -> str:
        return "ap"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)},{repr(self.right)})"


Expr = Union[Tree, Value]
# mypy doesn't support recursive types: https://github.com/python/mypy/issues/731
# Vector = Union[Tuple['Vector', 'Vector'], Tuple[()], int]
Vector = Union[Tuple[Any, Any], Tuple[()], int]  # HACK for type matching
Modulation = str

t: Expr = Value("t")
f: Expr = Value("f")


def vector(expr: Expr) -> Vector:
    """ Vector notation """
    if isinstance(expr, Value):
        if str(expr) == "nil":
            return ()
        return int(expr)
    if isinstance(expr, Tree):
        tok: List[Union[Vector, str]] = unparse(expr).split()  # type: ignore
        again = True
        while again and len(tok) >= 5:
            again = False
            for i in range(len(tok) - 4):
                a, b, c, d, e = tok[i : i + 5]
                if (a, b, c) != ("ap", "ap", "cons") or {d, e} & {"ap", "cons"}:
                    continue
                x: Vector = () if d == "nil" else d if isinstance(d, tuple) else int(d)
                y: Vector = () if e == "nil" else e if isinstance(e, tuple) else int(e)
                tok = tok[:i] + [(x, y)] + tok[i + 5 :]
                again = True
                break
        (result,) = tok  # Everything is always wrapped in an outer list
        return result  # type: ignore
    raise ValueError(f"Cannot vectorize {type(expr)} {expr}")


def unvector(vec: Vector) -> Expr:
    """ Undo a vector into a tree """
    if vec == ():
        return Value("nil")
    if isinstance(vec, int):
        return Value(str(vec))
    if isinstance(vec, tuple):
        assert len(vec) == 2, vec
        return Tree(Tree(Value("cons"), unvector(vec[0])), unvector(vec[1]))  # type: ignore
    raise ValueError(f"Can't unvector type {type(vec)} {vec}")


def demodulate(modulation: Modulation) -> Expr:
    """ Demodulate a complete modulation, Error if leftover """
    treeish, remainder = demodulate_partial(modulation)
    assert remainder == "", f"failed to fully parse {modulation} -> {remainder}"
    return treeish


def demodulate_partial(modulation: Modulation) -> Tuple[Expr, Modulation]:
    """
    Parse the first complete item out of a modulation,
    and return the item and the remainder of the modulation
    """
    assert re.fullmatch(r"[01]*", modulation), f"bad modulation {modulation}"
    # Numbers:
    int_match = re.match(r"(01|10)(1*)0([01]*)", modulation)
    if int_match is not None:
        # Integer prefix, follow with ones and a zero
        # The length of the first group is the rest of the length // 4
        sign, length_specifier, remainder = int_match.groups()
        length = len(length_specifier) * 4
        binary, unparsed = remainder[:length], remainder[length:]
        value = sum(int(n) * 2 ** i for i, n in enumerate(binary[::-1]))
        return Value(str({"01": 1, "10": -1}[sign] * value)), unparsed
    # Empty list
    if modulation.startswith("00"):
        # Hardcode this for now
        return Value("nil"), modulation[2:]
    # List
    if modulation.startswith("11"):
        # I'm pretty sure this is how this works
        remainder = modulation[2:]
        head, remainder = demodulate_partial(remainder)
        tail, remainder = demodulate_partial(remainder)
        return Tree(Tree(Value("cons"), head), tail), remainder
    raise ValueError(f"Unmatched modulation {modulation}")


def modulate(expr: Expr) -> Modulation:
    """ modulate a value into a modulation """
    if expr == Value("nil"):
        return "00"
    if isinstance(expr, Value):
        value = int(expr)
        if value == 0:
            return "010"
        sign_mod = "01" if value >= 0 else "10"
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4)
        prefix = sign_mod + "1" * length_units + "0"
        binary = "0" * (length_units * 4 - length) + bin(abs(value))[2:]
        return prefix + binary
    if isinstance(expr, Tree):
        left_tree = expr.left
        if isinstance(left_tree, Tree) and left_tree.left == Value("cons"):
            assert left_tree.right is not None, f"Missing left.right {expr}"
            assert expr.right is not None, f"Missing right {expr}"
            left_bits = modulate(left_tree.right)
            right_bits = modulate(expr.right)
            return "11" + left_bits + right_bits
    raise ValueError(f"Can't modulate type {type(expr)} {expr}")


def unparse(expr: Expr) -> str:
    """ Parse an object back into the ap language """
    if isinstance(expr, (Value, Tree)):
        return " ".join(n.unparse() for n in expr.nlr())
    raise ValueError(f"Can't unparse type {type(expr)} {expr}")


def parse(orig: Union[str, List[str]]) -> Expr:
    """ Parse and return a complete expression, and leftover tokens """
    tokens: List[str] = orig.strip().split() if isinstance(orig, str) else orig
    orig_str: str = " ".join(tokens)
    stack: List[Tree] = []
    expr: Optional[Expr] = None  # Contains the object to return at the end
    while tokens:
        token, *tokens = tokens
        expr = Tree() if token == "ap" else Value(token)
        if stack:
            if stack[-1].left is None:
                stack[-1].left = expr
            elif stack[-1].right is None:
                stack[-1].right = expr
                if isinstance(expr, Tree):
                    stack.append(expr)
            else:
                raise ValueError(
                    f"Parser shouldn't have complete tree in stack! {orig_str}"
                )
            while stack and stack[-1].left is not None and stack[-1].right is not None:
                expr = stack.pop()
        if isinstance(expr, Tree) and (expr.left is None or expr.right is None):
            stack.append(expr)
        if not len(stack):
            break

    assert tokens == [], f"Failed to parse tokens {orig_str} -> {tokens}"
    assert isinstance(expr, (Value, Tree)), f"Failed to parse tokens {orig_str}"
    return expr


def parse_file(filename: str) -> Dict[str, Expr]:
    """ Parse a file into a map of names to expressions """
    functions = {}
    with open(filename) as f:
        for line in f.readlines():
            name, _, *tokens = line.strip().split()
            functions[name] = parse(tokens)
    return functions


functions: Dict[str, Expr] = parse_file("galaxy.txt")


def evaluate(orig: Expr) -> Expr:
    """ Fully evaluate an expression and return it """
    current, again = orig, True
    while again:
        current, again = tryEval(current)
    orig.Evaluated = current
    return current


def tryEval(expr: Expr) -> Tuple[Expr, bool]:
    """ Try to perform a computation, return result and success """
    assert isinstance(expr, (Value, Tree)), expr
    if expr.Evaluated:
        return expr.Evaluated, False
    if isinstance(expr, Value) and str(expr) in functions:
        return functions[str(expr)], True
    if isinstance(expr, Tree):
        assert isinstance(expr.left, (Value, Tree)), expr
        assert isinstance(expr.right, (Value, Tree)), expr
        left: Expr = evaluate(expr.left)
        x: Expr = expr.right
        if isinstance(left, Value):
            if str(left) == "neg":
                return Value(-int(evaluate(x))), True  # type: ignore
            if str(left) == "i":
                return x, True
            if str(left) == "nil":
                return t, True
            if str(left) == "isnil":
                return Tree(x, Tree(t, Tree(t, f))), True
            if str(left) == "car":
                return Tree(x, t), True
            if str(left) == "cdr":
                return Tree(x, f), True
        if isinstance(left, Tree):
            assert isinstance(left.left, (Value, Tree)), left
            assert isinstance(left.right, (Value, Tree)), left
            left2: Expr = evaluate(left.left)
            y: Expr = left.right
            if isinstance(left2, Value):
                if str(left2) == "t":
                    return y, True
                if str(left2) == "f":
                    return x, True
                if str(left2) == "add":
                    return Value(int(evaluate(x)) + int(evaluate(y))), True  # type: ignore
                if str(left2) == "mul":
                    return Value(int(evaluate(x)) * int(evaluate(y))), True  # type: ignore
                if str(left2) == "div":
                    a, b = int(evaluate(y)), int(evaluate(x))  # type: ignore
                    return Value(a // b if a * b > 0 else (a + (-a % b)) // b), True
                if str(left2) == "lt":
                    return (
                        (t, True) if int(evaluate(y)) < int(evaluate(x)) else (f, True)
                    )
                if str(left2) == "eq":
                    return (
                        (t, True) if int(evaluate(y)) == int(evaluate(x)) else (f, True)
                    )
                if str(left2) == "cons":
                    return evalCons(y, x), True
            if isinstance(left2, Tree):
                assert isinstance(left2.left, (Value, Tree)), left2
                assert isinstance(left2.right, (Value, Tree)), left2
                left3: Expr = evaluate(left2.left)
                z: Expr = left2.right
                if isinstance(left3, Value):
                    if str(left3) == "s":
                        return Tree(Tree(z, x), Tree(y, x)), True
                    if str(left3) == "c":
                        return Tree(Tree(z, x), y), True
                    if str(left3) == "b":
                        return Tree(z, Tree(y, x)), True
                    if str(left3) == "cons":
                        return Tree(Tree(x, z), y), True
    return expr, False


def evalCons(a: Expr, b: Expr) -> Expr:
    """ Evaluate a pair """
    res: Expr = Tree(Tree(Value('cons'), evaluate(a)), evaluate(b))
    res.Evaluated = res
    return res


def SEND_TO_ALIEN_PROXY(data: Vector) -> Vector:
    server_url = "https://icfpc2020-api.testkontur.ru/aliens/send"
    api_key = os.environ["ICFP_API_KEY"]
    print("Sending vector:", data)
    modulation = modulate(unvector(data))
    res = requests.post(server_url, params=dict(apiKey=api_key), data=modulation)
    if res.status_code != 200:
        print('Unexpected server response from URL "%s":' % server_url)
        print("HTTP code:", res.status_code)
        print("Response body:", res.text)
        raise ValueError("Server response:", res.text)
    result = vector(demodulate(res.text))
    print("Received vector:", result)
    return result


# See https://message-from-space.readthedocs.io/en/latest/message38.html
def interact(state: Vector, event: Vector) -> Tuple[Vector, Vector]:
    """ Interact with the game """
    expr: Expr = Tree(Tree(Value("galaxy"), unvector(state)), unvector(event))
    res: Expr = evaluate(expr)
    assert unparse(res) == unparse(demodulate(modulate(res))), f"modem {unparse(res)}"
    flag, (state, (data, term)) = vector(res)
    assert vector(unvector(state)) == state
    assert vector(unvector(data)) == data
    assert isinstance(flag, int), f"bad flag {flag}"
    assert isinstance(state, (list, tuple)), f"bad state {state}"
    assert isinstance(data, (list, tuple)), f"bad data {data}"
    if flag == 0:
        return state, data
    return interact(state, SEND_TO_ALIEN_PROXY(data))


def print_images(images: Vector, pixelview, SIZE, BIG) -> None:
    assert isinstance(images, tuple), f"Images must be tuple {images}"
    while images:
        image, images = images
        while image:
            pixel, image = image
            offset = [(p + SIZE // 2) * BIG for p in pixel]
            for x in range(offset[0], offset[0] + BIG):
                for y in range(offset[1], offset[1] + BIG):
                    assert 0 <= x < SIZE * BIG and 0 <= y < SIZE * BIG, f"offscreen {x, y}"
                    pixelview[y][x] = (pixelview[y][x] + 0x202020) & 0xFFFFFF + 0xFF000000


if __name__ == "__main__":
    state: Vector = ()
    click: Vector
    for click in [(0, 0)] * 8 + [
        (8, 4),
        # (2, -8),
        # (3, 6),
        # (0, -14),
        # (-4, 10),
        # (9, -3),
        # (-4, 10),
        # (1, 4),
        # (0, 1),  # Uncomment to skip galaxy screen
    ]:
        state, images = interact(state, click)

    sdl2.ext.init()
    SIZE = 320  # Size of the display in game pixels
    BIG = 3  # How much "bigger" each pixel should be, scales up

    win = sdl2.ext.Window("Galaxy", size=(SIZE * BIG, SIZE * BIG))
    win.show()
    winsurf = win.get_surface()
    running = True
    pixelview = sdl2.ext.PixelView(winsurf)

    # Initial image
    sdl2.ext.fill(winsurf, sdl2.ext.Color(0, 0, 0))
    print_images(images, pixelview, SIZE, BIG)
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                pixel = [event.button.x, event.button.y]
                point = tuple([(i // BIG) - SIZE // 2 for i in pixel])
                print("click", point)
                state, images = interact(state, point)
                sdl2.ext.fill(winsurf, sdl2.ext.Color(0, 0, 0))
                print_images(images, pixelview, SIZE, BIG)
        win.refresh()
    sdl2.ext.quit()
