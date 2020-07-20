#!/usr/bin/env python
import sys
from itertools import zip_longest
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, Dict, NamedTuple, Iterable

# from PIL import Image
# from imgcat import imgcat

import sdl2.ext
from random import randint


@dataclass
class Value:
    """ Atoms are the leaves of our tree """

    Name: Optional[str] = None
    Evaluated: Optional["Expr"] = None

    def nlr(self) -> Iterable["Expr"]:
        yield self

    def unparse(self) -> str:
        assert self.Name is not None, self
        return self.Name


@dataclass
class Tree:
    """ Applications (of a function) are the non-leaf nodes of our tree """

    Left: Optional["Expr"] = None
    Right: Optional["Expr"] = None
    Evaluated: Optional["Expr"] = None

    def nlr(self) -> Iterable["Expr"]:
        """ Generator for all of the Tree nodes in preorder (NLR) """
        stack: List["Expr"] = [self]
        while stack:
            expr: "Expr" = stack.pop()
            yield expr
            if isinstance(expr, Tree):
                assert isinstance(expr.Right, (Value, Tree)), self
                stack.append(expr.Right)
                assert isinstance(expr.Left, (Value, Tree)), self
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


def vector(expr: Expr) -> List[Union[List, int]]:
    """ Vector notation """
    if isinstance(expr, Tree):
        tok: List[Union[List, int]] = unparse(expr).split()  # type: ignore
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
                    e = e if isinstance(e, list) else [] if e == "nil" else int(e)
                    d = d if isinstance(d, list) else [] if d == "nil" else int(d)
                    tok = tok[:i] + [[d, e]] + tok[i + 5 :]
                    again = True
                    break
        (result,) = tok  # Everything is always wrapped in an outer list
        return result  # type: ignore
    raise ValueError(f"Cannot vectorize {type(expr)} {expr}")


def unvector(lst: Union[List, int]) -> Expr:
    """ Undo a vector into a tree """
    # Todo: make iterative
    if lst == []:
        return Value("nil")
    if isinstance(lst, int):
        return Value(str(lst))
    if isinstance(lst, list):
        assert len(lst) == 2, lst
        x = unvector(lst[0])
        y = unvector(lst[1])
        return Tree(Tree(Value("cons"), x), y)
    raise ValueError(f"Can't unvector type {type(lst)} {lst}")


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
                # expr = maybe_vector(expr)
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


# See https://message-from-space.readthedocs.io/en/latest/message38.html
def interact(state: Expr, event: Expr) -> Tuple[Expr, Expr]:
    """ Interact with the game """
    expr: Expr = Tree(Tree(Value("galaxy"), state), event)
    res: Expr = evaluate(expr)
    assert unparse(res) == unparse(unvector(vector(res))), f"Modem check {unparse(res)}"
    flag, (newState, (data, v)) = vector(res)  # type: ignore
    assert isinstance(flag, int), f"bad flag {flag}"
    assert v == [], f"Failed to parse res correctly {unparse(res)} {v}"
    if flag == 0:
        return (unvector(newState), unvector(data))
    assert False
    return interact(unvector(newState), SEND_TO_ALIEN_PROXY(data))


def print_images(images: Expr, pixelview, SIZE) -> None:
    sdl2.ext.fill(winsurf, BLACK)
    imvec = vector(images)  # convert to lists
    print("imvec", imvec)
    while imvec != []:
        image, imvec = imvec  # type: ignore
        print("image", image)
        # im = Image.new("RGB", (SIZE * 2, SIZE * 2))
        color = sdl2.ext.Color(randint(128, 255), randint(128, 255), randint(128, 255))
        while image != []:
            pixel, image = image  # type: ignore
            pixelview[pixel[0] + SIZE // 2][pixel[1] + SIZE // 2] = color
    print("Printed images")


def REQUEST_CLICK_FROM_USER() -> Expr:
    x, y = 0, 0
    return Tree(Tree(cons, Value(str(x))), Value(str(y)))


def SEND_TO_ALIEN_PROXY(data: Expr) -> Expr:
    assert False


if __name__ == "__main__":
    # Initial state
    state: Expr = Value("nil")
    click: Expr = unvector([0, 0])
    state, images = interact(state, click)
    # # main loop
    # while True:
    #     click: Expr = unvector([0, 0])
    #     newState, images = interact(state, click)
    #     PRINT_IMAGES(images)
    #     click = REQUEST_CLICK_FROM_USER()
    #     state = newState


    BLACK = sdl2.ext.Color(0, 0, 0)

    sdl2.ext.init()
    SIZE = 512
    win = sdl2.ext.Window("Galaxy", size=(SIZE, SIZE))
    win.show()
    winsurf = win.get_surface()
    running = True
    pixelview = sdl2.ext.PixelView(winsurf)

    # Initial image
    sdl2.ext.fill(winsurf, BLACK)
    print_images(images, pixelview, SIZE)
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                print('click', event.button.x, event.button.y)
                click = unvector([event.button.x - SIZE // 2, event.button.y - SIZE // 2])
                state, images = interact(state, click)
                print_images(images, pixelview, SIZE)
        win.refresh()
    sdl2.ext.quit()