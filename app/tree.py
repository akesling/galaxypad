#!/usr/bin/env python
import re
from dataclasses import dataclass
from typing import Tuple, List, Optional, Union, Dict, NamedTuple, Callable

INT_REGEX = re.compile(r"(-?\d+)")
VAR_REGEX = re.compile(r"x(\d+)")


class Value(NamedTuple):
    """ Leaf in the tree """

    value: Union[int, str]


class Placeholder(NamedTuple):
    """ Placeholder value for using in Rewrite expressions """

    x: int


@dataclass
class Tree:  # I wish I could make this a NamedTuple, but mypy hates it
    """ Note this might not be a strict tree, and instead be a digraph """

    left: Optional[Union["Tree", Value, Placeholder]] = None
    right: Optional[Union["Tree", Value, Placeholder]] = None


def parse_tree(
    tokens: List[str],
) -> Tuple[Optional[Union[Tree, Value, Placeholder]], List[str]]:
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
    raise ValueError(f"Unknown token {token}")


PlaceDict = Dict[int, Optional[Union[Tree, Value, Placeholder]]]
ProcessFn = Callable[[PlaceDict], bool]


class Rewrite(NamedTuple):
    """ Pattern match to a reduction """

    pattern: Union[Tree, Value, Placeholder]
    replace: Union[Tree, Value, Placeholder]
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


def unop(fn: Callable[[int], int]) -> ProcessFn:
    """ Helper to build unary operator functions for arithmetic """

    def process(pd: PlaceDict) -> bool:
        if 0 in pd and isinstance(pd[0], Value) and isinstance(pd[0].value, int):
            pd[1] = Value(fn(pd[0].value))
            return True
        return False

    return process


def binop(fn: Callable[[int, int], int]) -> Callable[[PlaceDict], bool]:
    """ Helper to build binary operator functions for arithmetic """

    def process(pd: PlaceDict) -> bool:
        if 0 in pd and 1 in pd:
            if isinstance(pd[0], Value) and isinstance(pd[1], Value):
                if isinstance(pd[0].value, int) and isinstance(pd[1].value, int):
                    pd[2] = Value(fn(pd[0].value, pd[1].value))
                    return True
        return False

    return process


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
]
REWRITES = (
    [
        Rewrite.from_str(s)
        for s in [
            "ap i x0 = x0",  # Identity
            "ap add 0 = i",  # Addition -> Identity
            "ap add 1 = inc",  # Addition -> Increment
            "ap add -1 = dec",  # Addition -> Increment
            "ap ap add x0 0 = x0",  # Additive Identity
            "ap ap t x0 x1 = x0",  # True
            "ap f x0 = i",  # False -> Identity
            "ap ap f x0 x1 = x1",  # False
            "ap mul 1 = i",  # Multiplication -> Identity
            "ap ap mul x0 0 = 0",  # Multiplication by Zero
            "ap ap mul x0 1 = x0",  # Multiplicative Identity
            "ap ap div x0 1 = x0",  # Division Identity
            "ap ap eq x0 x0 = t",  # Equality Comparison (matching subtrees)
            "ap dec ap inc x0 = x0",  # Increment/Decrement Annihilation
            "ap inc ap dec x0 = x0",  # Decrement/Increment Annihilation
            "ap ap ap s x0 x1 x2 = ap ap x0 x2 ap x1 x2",  # S Combinator
            "ap ap ap c x0 x1 x2 = ap ap x0 x2 x1",  # C Combinator
            "ap ap ap b x0 x1 x2 = ap x0 ap x1 x2",  # B Combinator
            "ap ap ap cons x0 x1 x2 = ap ap x2 x0 x1",  # Pair
            "ap car ap ap cons x0 x1 = x0",  # Head
            "ap cdr ap ap cons x0 x1 = x1",  # Tail
            "ap nil x0 = t",  # Nil (Empty List)
            "ap isnil nil = t",  # Is Nil (Is Empty List)
            "ap isnil ap ap cons x0 x1 = f",  # Is Not Empty List
            "vec = cons",  # Vector (Alias)
            "if0 = ap eq 0",  # If equal to zero
        ]
    ]
    + [
        Rewrite.from_str(s, unop(fn))
        for s, fn in [
            ("ap inc x0 = x1", lambda x: x + 1),  # Increment
            ("ap dec x0 = x1", lambda x: x - 1),  # Decrement
            ("ap neg x0 = x1", lambda x: -x),  # Negate
            ("ap pwr2 x0 = x1", lambda x: 2**x),  # Power of 2
        ]
    ]
    + [
        Rewrite.from_str(s, binop(fn))
        for s, fn in [
            ("ap ap add x0 x1 = x2", lambda x, y: x + y),  # Addition
            ("ap ap mul x0 x1 = x2", lambda x, y: x * y),  # Multiplication
            (  # https://stackoverflow.com/a/19919449
                "ap ap div x0 x1 = x2",
                lambda a, b: a // b if a * b > 0 else (a + (-a % b)) // b,
            ),  # Division
            ("ap ap eq x0 x1 = x2", lambda x, y: "t" if x == y else "f"),  # Equals
            ("ap ap lt x0 x1 = x2", lambda x, y: "t" if x < y else "f"),  # Less Than
        ]
    ]
)


def match(
    pattern: Optional[Union[Tree, Value, Placeholder]],
    data: Optional[Union[Tree, Value, Placeholder]],
    placedict: PlaceDict,
) -> bool:
    """ Return true if data matches pattern, also fills out placedict dict """
    if pattern is None and data is None:
        return True
    if isinstance(pattern, Value) and isinstance(data, Value):
        return pattern == data
    if isinstance(pattern, Placeholder):
        if pattern.x in placedict:  # Already in pattern, check tree matches
            return placedict[pattern.x] == data
        placedict[pattern.x] = data  # Else add to placeholders dict
        return True
    if isinstance(pattern, Tree) and isinstance(data, Tree):
        return match(pattern.left, data.left, placedict) and match(
            pattern.right, data.right, placedict
        )
    return False


def apply(
    replace: Optional[Union[Tree, Value, Placeholder]], placedict: PlaceDict,
) -> Optional[Union[Tree, Value, Placeholder]]:
    """ Apply the replacement to this tree and return result """
    if replace is None:
        return None
    if isinstance(replace, Value):
        return replace
    if isinstance(replace, Placeholder):
        return placedict[replace.x]
    if isinstance(replace, Tree):
        left = apply(replace.left, placedict)
        right = apply(replace.right, placedict)
        return Tree(left, right)
    raise ValueError(r"invalid replace {replace}")


def compute(
    tree: Optional[Union[Tree, Value, Placeholder]]
) -> Tuple[Optional[Union[Tree, Value, Placeholder]], bool]:
    """
    NOTE: THIS POSSIBLY MUTATES THE TREE !!! 
    Returns tree, True if the tree was modified, tree, false if failed.
    If this returns True, possibly more rewrites can happen.
    """
    if tree is None:
        return tree, False
    if isinstance(tree, Tree):
        # Check subtrees before this tree because matches are more likely in leaves
        tree.left, result = compute(tree.left)
        if result:
            return tree, True
        tree.right, result = compute(tree.right)
        if result:
            return tree, True
    if isinstance(tree, (Tree, Value, Placeholder)):
        for rewrite in REWRITES:
            pd: PlaceDict = {}
            if match(rewrite.pattern, tree, pd) and rewrite.process(pd):
                return apply(rewrite.replace, pd), True
        return tree, False
    raise ValueError(f"Bad type for tree {tree} {type(tree)}")


def compute_fully(
    tree: Optional[Union[Tree, Value, Placeholder]]
) -> Optional[Union[Tree, Value, Placeholder]]:
    """ Call compute on a tree until it converges """
    result = True
    while result:
        tree, result = compute(tree)
    return tree


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        tree, leftover = parse_tree(sys.argv[1].strip().split())
        if leftover:
            print("Missed this bit", leftover)
        print("computed", compute_fully(tree))
    else:
        print("Help: Run with a string argument to compute")
        print("  > python tree.py 'ap ap add 1 2'")
