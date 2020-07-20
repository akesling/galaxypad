#!/usr/bin/env python
import re
import os
import sys
import math

# from dataclasses import dataclass
from itertools import zip_longest
from random import randint
from typing import Dict, Iterable, List, NamedTuple, Optional, Tuple, Union, Any

import requests
import sdl2.ext

sys.setrecursionlimit(10000)


class Value:
    """ Atoms are the leaves of our tree """

    Name: Optional[str] = None
    Evaluated: Optional["Expr"] = None

    def __init__(self, Name=None):
        self.Name = Name
        self.Evaluated = None

    def nlr(self) -> Iterable["Expr"]:
        yield self

    def __eq__(self, other):
        if type(self) == type(other):
            return self.Name == other.Name
        return False

    def unparse(self) -> str:
        assert self.Name is not None, self
        return self.Name


class Tree:
    """ Applications (of a function) are the non-leaf nodes of our tree """

    Left: Optional["Expr"] = None
    Right: Optional["Expr"] = None
    Evaluated: Optional["Expr"] = None

    def __init__(self, Left=None, Right=None):
        self.Left = Left
        self.Right = Right
        self.Evaluated = None

    def nlr(self) -> Iterable["Expr"]:
        """ Generator for all of the Tree nodes in preorder (NLR) """
        stack: List["Expr"] = [self]
        while stack:
            expr: "Expr" = stack.pop()
            yield expr
            if isinstance(expr, Tree):
                assert isinstance(expr.Right, (Value, Tree)), f"{expr.Right}"
                stack.append(expr.Right)
                assert isinstance(expr.Left, (Value, Tree)), f"{expr.Left}"
                stack.append(expr.Left)

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


Expr = Union[Tree, Value]


def asNum(n: Expr) -> int:
    if isinstance(n, Value) and n.Name is not None:
        return int(n.Name)
    raise ValueError(f"not a number {n}")


nil: Expr = Value("nil")


cons: Expr = Value("cons")
t: Expr = Value("t")
f: Expr = Value("f")


def vector(expr: Expr) -> Any:
    """ Vector notation """
    if isinstance(expr, Value):
        if expr.Name == "nil":
            return []
        return asNum(expr)
    if isinstance(expr, Tree):
        tok: List[Union[List, Tuple, int]] = unparse(expr).split()  # type: ignore
        again = True
        while again and len(tok) >= 5:
            again = False
            for i in range(len(tok) - 4):
                a, b, c, d, e = tok[i : i + 5]
                if (
                    (a, b, c) == ("ap", "ap", "cons")
                    and d not in ("ap", "cons")
                    and e not in ("ap", "cons")
                ):
                    if isinstance(d, str):
                        d = [] if d == "nil" else int(d)
                    if isinstance(e, str):
                        e = [] if e == "nil" else int(e)
                    if d != [] and isinstance(e, list):
                        tok = tok[:i] + [[d,] + e] + tok[i + 5 :]
                        again = True
                        break
                    else:
                        tok = tok[:i] + [(d, e)] + tok[i + 5 :]
                        again = True
                        break
        (result,) = tok  # Everything is always wrapped in an outer list
        return result  # type: ignore
    raise ValueError(f"Cannot vectorize {type(expr)} {expr}")


def unvector(lst: Any) -> Expr:
    """ Undo a vector into a tree """
    if lst == [] or lst == ():
        return Value("nil")
    if isinstance(lst, int):
        return Value(str(lst))
    if isinstance(lst, tuple):  # Bare pair
        assert len(lst) == 2, lst
        x, y = lst
        return Tree(Tree(Value("cons"), unvector(x)), unvector(y))
    if isinstance(lst, list):  # Recursive list
        assert len(lst) > 0, lst
        x, *rem = lst
        return Tree(Tree(Value("cons"), unvector(x)), unvector(rem))
    raise ValueError(f"Can't unvector type {type(lst)} {lst}")


def demodulate(modulation: str) -> Expr:
    """ Demodulate a complete modulation, Error if leftover """
    treeish, remainder = demodulate_partial(modulation)
    assert remainder == "", f"failed to fully parse {modulation} -> {remainder}"
    return treeish


def demodulate_partial(modulation: str) -> Tuple[Expr, str]:
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


def modulate(expr: Expr) -> str:
    """ modulate a value into a modulation """
    if expr == Value("nil"):
        return "00"
    if isinstance(expr, Value):
        value = asNum(expr)
        if value == 0:
            return "010"
        sign_mod = "01" if value >= 0 else "10"
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4)
        prefix = sign_mod + "1" * length_units + "0"
        binary = "0" * (length_units * 4 - length) + bin(abs(value))[2:]
        return prefix + binary
    if isinstance(expr, Tree):
        left_tree = expr.Left
        if isinstance(left_tree, Tree) and left_tree.Left == Value("cons"):
            assert left_tree.Right is not None, f"Missing left.right {expr}"
            assert expr.Right is not None, f"Missing right {expr}"
            left_bits = modulate(left_tree.Right)
            right_bits = modulate(expr.Right)
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
            if stack[-1].Left is None:
                stack[-1].Left = expr
            elif stack[-1].Right is None:
                stack[-1].Right = expr
                if isinstance(expr, Tree):
                    stack.append(expr)
            else:
                raise ValueError(
                    f"Parser shouldn't have complete tree in stack! {orig_str}"
                )
            while stack and stack[-1].Left is not None and stack[-1].Right is not None:
                expr = stack.pop()
        if isinstance(expr, Tree) and (expr.Left is None or expr.Right is None):
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
    if isinstance(expr, Value) and expr.Name in functions:
        return functions[expr.Name], True
    if isinstance(expr, Tree):
        assert isinstance(expr.Left, (Value, Tree)), expr
        assert isinstance(expr.Right, (Value, Tree)), expr
        left: Expr = evaluate(expr.Left)
        x: Expr = expr.Right
        if isinstance(left, Value):
            if left.Name == "neg":
                return Value(str(-asNum(evaluate(x)))), True
            if left.Name == "i":
                return x, True
            if left.Name == "nil":
                return t, True
            if left.Name == "isnil":
                return Tree(x, Tree(t, Tree(t, f))), True
            if left.Name == "car":
                return Tree(x, t), True
            if left.Name == "cdr":
                return Tree(x, f), True
        if isinstance(left, Tree):
            assert isinstance(left.Left, (Value, Tree)), left
            assert isinstance(left.Right, (Value, Tree)), left
            left2: Expr = evaluate(left.Left)
            y: Expr = left.Right
            if isinstance(left2, Value):
                if left2.Name == "t":
                    return y, True
                if left2.Name == "f":
                    return x, True
                if left2.Name == "add":
                    return (
                        Value(str(asNum(evaluate(x)) + asNum(evaluate(y)))),
                        True,
                    )
                if left2.Name == "mul":
                    return (
                        Value(str(asNum(evaluate(x)) * asNum(evaluate(y)))),
                        True,
                    )
                if left2.Name == "div":
                    a, b = asNum(evaluate(y)), asNum(evaluate(x))
                    return (
                        Value(str(a // b if a * b > 0 else (a + (-a % b)) // b)),
                        True,
                    )
                if left2.Name == "lt":
                    return (
                        (t, True)
                        if asNum(evaluate(y)) < asNum(evaluate(x))
                        else (f, True)
                    )
                if left2.Name == "eq":
                    return (
                        (t, True)
                        if asNum(evaluate(y)) == asNum(evaluate(x))
                        else (f, True)
                    )
                if left2.Name == "cons":
                    return evalCons(y, x), True
            if isinstance(left2, Tree):
                assert isinstance(left2.Left, (Value, Tree)), left2
                assert isinstance(left2.Right, (Value, Tree)), left2
                left3: Expr = evaluate(left2.Left)
                z: Expr = left2.Right
                if isinstance(left3, Value):
                    if left3.Name == "s":
                        return Tree(Tree(z, x), Tree(y, x)), True
                    if left3.Name == "c":
                        return Tree(Tree(z, x), y), True
                    if left3.Name == "b":
                        return Tree(z, Tree(y, x)), True
                    if left3.Name == "cons":
                        return Tree(Tree(x, z), y), True
    return expr, False


def evalCons(a: Expr, b: Expr) -> Expr:
    """ Evaluate a pair """
    res: Expr = Tree(Tree(cons, evaluate(a)), evaluate(b))
    res.Evaluated = res
    return res


def SEND_TO_ALIEN_PROXY(data: Any) -> Any:
    data = vector(data) if isinstance(data, (Value, Tree)) else data
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
def interact(state: Any, event: Any) -> Tuple[Any, Any]:
    """ Interact with the game """
    state = state if isinstance(state, (Value, Tree)) else unvector(state)
    event = event if isinstance(event, (Value, Tree)) else unvector(event)
    expr: Expr = Tree(Tree(Value("galaxy"), state), event)
    res: Expr = evaluate(expr)
    assert unparse(res) == unparse(demodulate(modulate(res))), f"modem {unparse(res)}"
    flag, state, data = vector(res)
    assert vector(unvector(state)) == state
    assert vector(unvector(data)) == data
    assert isinstance(flag, int), f"bad flag {flag}"
    assert isinstance(state, (list, tuple)), f"bad state {state}"
    assert isinstance(data, (list, tuple)), f"bad data {data}"
    if flag == 0:
        return state, data
    return interact(state, SEND_TO_ALIEN_PROXY(data))


def print_images(images: Any, pixelview, SIZE, BIG) -> None:
    # TODO: ugly hack because of the fact our vector format has multiple reps
    if isinstance(images, tuple):
        imvec = images
        images = []
        while imvec:
            if isinstance(imvec, tuple):
                image, imvec = imvec
                images.append(image)
            elif isinstance(imvec, list):
                images.append(imvec.pop())
            else:
                raise ValueError(f"bad imvec {imvec}")
    # print('images', images)
    for image in images[::-1]:
        # print('image', image)
        color = sdl2.ext.Color(randint(32, 255), randint(32, 255), randint(32, 255))
        for pixel in image:
            # print('pixel', pixel)
            offset = [(p + SIZE // 2) * BIG for p in pixel]
            for x in range(max(offset[0], 0), min(offset[0] + BIG, SIZE * BIG)):
                for y in range(max(offset[1], 0), min(offset[1] + BIG, SIZE * BIG)):
                    pixelview[y][x] = color


if __name__ == "__main__":
    state: Expr = Value("nil")
    for click in [(0, 0)] * 8 + [
        (8, 4),
        (2, -8),
        (3, 6),
        (0, -14),
        (-4, 10),
        (9, -3),
        (-4, 10),
        (1, 4),
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
