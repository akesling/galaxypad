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


PlaceDict = Dict[int, Optional[Union[Tree, Value, Placeholder, Procedure]]]
ProcessFn = Callable[[PlaceDict], bool]


def parse_tree(
    tokens: List[str],
) -> Tuple[Optional[Union[Tree, Value, Placeholder, Procedure]], List[str]]:
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


def pair(x, y):
    """ Helper function to get the tree representation of a pair"""
    return Tree(Tree(Value('cons'), x), y)


def vector(l):
    """ Helper to get a tree version of a vector """
    if isinstance(l, Value):
        return l
    if isinstance(l, int):
        return Value(l)
    assert isinstance(l, list), f"Bad vector {l}"
    if len(l) == 0:
        return Value('nil')
    if len(l) == 1:
        return pair(vector(l[0]), Value('nil'))
    head, *tail = l
    return pair(vector(head), vector(tail))


def unvector(tree):
    """ Reverse of the vector function """
    if tree == Value('nil'):
        return []
    if isinstance(tree, Value) and isinstance(tree.value, int):
        return tree.value
    if isinstance(tree, int):
        return tree
    if isinstance(tree.left, Tree) and tree.left.left == Value('cons'):
        v0 = unvector(tree.left.right)
        v1 = unvector(tree.right)
        if v1 == []:
            return [v0]
        if isinstance(v1, list):
            return [v0] + v1
        return [v0, v1]
    raise ValueError(f"Don't know how to unvector {tree}")
        


if __name__ == '__main__':
    d = [1, [2, 3], 4]
    print('d', d)
    v = vector(d)
    print('v', v)
    u = unvector(v)
    print('u', u)
    print(d == u)

