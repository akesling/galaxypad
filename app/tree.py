#!/usr/bin/env python

import re
from dataclasses import dataclass
from typing import NamedTuple, Union, Optional, Callable, Dict, List, Tuple


INT_REGEX = re.compile(r"(-?\d+)")
VAR_REGEX = re.compile(r"x(\d+)")
PROC_REGEX = re.compile(r":(\d+)")
KNOWN_TOKENS = [
    "add",
    "inc",
    "dec",
    "i",
    "t",
    "f",
    "mul",
    "div",
    "eq",
    "lt",
    "neg",
    "s",
    "c",
    "b",
    "pwr2",
    "cons",
    "car",
    "cdr",
    "nil",
    "isnil",
    "vec",
    "if0",
    "send",
]


class Value(NamedTuple):
    """ Leaf in the tree """

    value: Union[int, str]


class Placeholder(NamedTuple):
    """ Placeholder value for using in Rewrite expressions """

    x: int


class Procedure(NamedTuple):
    """ A procedure to be lazily invoked through rewriting """

    name: int


@dataclass
class Tree:  # I wish I could make this a NamedTuple, but mypy hates it
    """ Note this might not be a strict tree, and instead be a digraph """

    left: Optional[Union["Tree", Value, Placeholder, Procedure]] = None
    right: Optional[Union["Tree", Value, Placeholder, Procedure]] = None


# Taking a line from the "git" book on naming things
Treeish = Optional[Union[Tree, Value, Placeholder, Procedure]]
PlaceDict = Dict[int, Treeish]
ProcessFn = Callable[[PlaceDict], bool]


def parse_tree(tokens: List[str],) -> Tuple[Treeish, List[str]]:
    """ Returns parsed tree, and leftover tokens """
    assert isinstance(tokens, list), f"bad tokens {tokens}"
    if tokens == []:
        return None, []
    token, tokens = tokens[0], tokens[1:]
    if token == "ap":
        left, tokens = parse_tree(tokens)
        right, tokens = parse_tree(tokens)
        return Tree(left, right), tokens
    if INT_REGEX.match(token):
        return Value(int(token)), tokens
    if token in KNOWN_TOKENS:
        return Value(token), tokens
    if VAR_REGEX.match(token):
        return Placeholder(int(token[1:])), tokens
    if PROC_REGEX.match(token):
        return Procedure(int(token[1:])), tokens
    raise ValueError(f"Unknown token {token}")


class Rewrite(NamedTuple):
    """ Pattern match to a reduction """

    pattern: Union[Tree, Value, Placeholder, Procedure]
    replace: Union[Tree, Value, Placeholder, Procedure]
    # Extra processing on the placeholders dictionary
    # good place for arithmetic, or side effects.
    # Returns False if this rewrite is invalid (for misc criterion, like numbers)
    process: ProcessFn = lambda x: True  # No-op default

    @classmethod
    def from_str(cls, s: str, process: ProcessFn = lambda x: True):
        """ Helper to build Rewrite rules in the same notation """
        assert s.count("=") == 1, f'string should have 1 "=", {s}'
        pattern_s, replace_s = s.split("=", 1)
        pattern, leftover = parse_tree(pattern_s.strip().split())
        assert pattern is not None, f"failed parsing pattern {pattern_s}"
        assert leftover == [], f"leftover parsing pattern {pattern_s}"
        replace_s, replace_s = s.split("=", 1)
        replace, leftover = parse_tree(replace_s.strip().split())
        assert replace is not None, f"failed parsing replace {replace_s}"
        assert leftover == [], f"leftover parsing replace {replace_s}"
        return cls(pattern=pattern, replace=replace, process=process)


def pair(x: Treeish, y: Treeish) -> Treeish:
    """ Helper function to get the tree representation of a pair"""
    return Tree(Tree(Value("cons"), x), y)


Vector = Union[List, int]


def vector(treeish: Treeish) -> Vector:
    """ Reverse of the vector function """
    if isinstance(treeish, Value):
        if treeish == Value("nil"):
            return []
        if isinstance(treeish.value, int):
            return treeish.value
        raise ValueError(f"Can't vector value {treeish}")
    if isinstance(treeish, Tree):
        left_tree = treeish.left
        # Specifically match the cons construction pattern
        if isinstance(left_tree, Tree) and left_tree.left in (
            # This is a bit ugly but both are valid unfortunately
            Value("cons"),
            Value("vec"),
        ):
            left = vector(left_tree.right)
            right = vector(treeish.right)
            if isinstance(right, list):
                return [left] + right
            return [left, right]
    raise ValueError(f"Don't know how to vector {treeish}")


def unvector(vec: Vector) -> Treeish:
    """ Helper to get a tree version of a vector """
    if isinstance(vec, int):
        return Value(vec)
    if vec == []:
        return Value("nil")
    if isinstance(vec, list):
        head, *tail = vec
        return pair(unvector(head), unvector(tail))
    raise ValueError(f"Can't vectorize {vec}")


if __name__ == "__main__":
    d = [[2, 3]]
    print("d", d)
    t = unvector(d)
    print("t\n", t)
    v = vector(t)
    print("v", v)
    print(d == v)

