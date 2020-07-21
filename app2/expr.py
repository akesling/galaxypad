#!/usr/bin/env python

from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable, List, Optional, Tuple, Union, TypeVar


class Expr:
    parent: Optional["Expr"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Value(Expr):
    name: str

    def __init__(self, name: Union[int, str], parent: Optional[Expr] = None):
        self.name = str(name)
        self.parent = parent

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.name == other.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.name)})"

    def complete(self) -> bool:
        return isinstance(self.name, str)


class Tree(Expr):
    left: Expr
    right: Expr

    def __init__(self, left: Expr, right: Expr, parent: Optional[Expr] = None):
        left.parent = self
        right.parent = self
        self.left = left
        self.right = right
        self.parent = parent

    def __eq__(self, other) -> bool:
        if type(self) == type(other):
            for s, o in zip_longest(nlr(self), nlr(other)):
                if isinstance(s, Value) and isinstance(o, Value) and s != o:
                    return False
                if isinstance(s, Tree) and isinstance(o, Tree):
                    continue
                return False
            return True
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)},{repr(self.right)})"

    def complete(self) -> bool:
        return self.left is not None and self.right is not None


def nlr(expr: Expr) -> Iterable[Expr]:
    """ Iterate over a tree in Node-Left-Right order """
    stack: List[Expr] = [expr]
    while stack:
        expr = stack.pop()
        if isinstance(expr, Value):
            yield expr
        elif isinstance(expr, Tree):
            yield expr
            stack.append(expr.right)
            stack.append(expr.left)
        else:
            raise ValueError(f"Invalid expression {expr}")


def parse(string: str) -> Expr:
    """ Parse a string like 'ap inc 0' into an Expr """
    tokens: List[str] = string.strip().split()
    stack: List[Tree] = []
    expr: Optional[Expr] = None  # Contains the object to return at the end
    null = Expr()  # Special placeholder value
    while tokens:
        token, *tokens = tokens
        expr = Tree(null, null) if token == "ap" else Value(token)
        if stack:
            if stack[-1].left == null:
                stack[-1].left = expr
                expr.parent = stack[-1]
            elif stack[-1].right == null:
                stack[-1].right = expr
                expr.parent = stack[-1]
        if isinstance(expr, Tree) and expr.right == null:
            stack.append(expr)
        while stack and stack[-1].right != null:
            expr = stack.pop()
        if not len(stack):
            break

    assert not stack, f"Unconsumed stack, (incomplete expr?): {stack}"
    assert tokens == [], f"Failed to parse tokens {string} -> {tokens}"
    assert isinstance(expr, Expr), f"Invalid expression type {expr} {string}"
    assert not any(n == null for n in nlr(expr)), f"Unparse null {expr}"
    for n in nlr(expr):
        if isinstance(n, Tree):
            assert n.left.parent is n, f"Mismatched tree {n}!={n.left.parent}"
            assert n.right.parent is n, f"Mismatched tree {n}!={n.right.parent}"
    return expr


def unparse(expr: Expr) -> str:
    """ Unparse and Expr into a string like 'ap inc 0' """
    if isinstance(expr, (Value, Tree)):
        tokens: List[str] = []
        for n in nlr(expr):
            if isinstance(n, Value):
                tokens.append(n.name)
            elif isinstance(n, Tree):
                tokens.append('ap')
            else:
                raise ValueError(f"Unparse unknown type {type(n)} {n}")
        return " ".join(tokens)
    raise ValueError(f"Can't unparse type {type(expr)} {expr}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        print(unparse(parse(sys.argv[1])))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")
