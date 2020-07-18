#!/usr/bin/env python
import re
import requests
import logging
from dataclasses import dataclass
from typing import Tuple, List, Optional, Union, Dict, NamedTuple, Callable

from tree import (
    Tree,
    ProcessFn,
    PlaceDict,
    Value,
    Treeish,
    Placeholder,
    Procedure,
)
from vector import vector, unvector
from rewrite import Rewrite
from serial import deserialize
from modulate import demodulate, modulate
import renderer

logger = logging.getLogger("app.compute")


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


def send(pd: PlaceDict) -> bool:
    res = requests.post(
        "https://icfpc2020-api.testkontur.ru/aliens/send",
        params=dict(apiKey="8f96a989734a45688a78d530f60cce97"),
        data=modulate(pd[0]),
    )
    if res.status_code != 200:
        raise ValueError("Server response:", res.text)
    pd[1] = demodulate(res.text)
    return True


def pd_draw(pd: PlaceDict) -> bool:
    if 0 in pd:
        pd[1] = renderer.draw(vector(pd[0]))
        return True
    return False


def pd_multidraw(pd: PlaceDict) -> bool:
    if 0 in pd:
        pd[1] = unvector(renderer.multidraw(vector(pd[0])))
        return True
    return False


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
            #            "ap ap eq x0 x0 = t",  # Equality Comparison (matching subtrees)
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
            ("ap pwr2 x0 = x1", lambda x: 2 ** x),  # Power of 2
        ]
    ]
    + [
        Rewrite.from_str(s, binop(fn))
        for s, fn in [
            ("ap ap add x0 x1 = x2", lambda x, y: x + y),  # Addition
            ("ap ap mul x0 x1 = x2", lambda x, y: x * y),  # Multiplication
            (  # https://stackoverflow.com/a/19919449
                "ap ap div x0 x1 = x2",  # Division
                lambda a, b: a // b if a * b > 0 else (a + (-a % b)) // b,
            ),
            ("ap ap eq x0 x1 = x2", lambda x, y: "t" if x == y else "f"),  # Equals
            ("ap ap lt x0 x1 = x2", lambda x, y: "t" if x < y else "f"),  # Less Than
            (
                "ap ap checkerboard x0 x1 = x2",
                lambda x, y: renderer.checkerboard((x, y)),
            ),
        ]
    ]
    + [
        Rewrite.from_str("ap send x0 = x1", send),
        Rewrite.from_str("ap draw x0 = x1", pd_draw),
        Rewrite.from_str("ap multipledraw x0 = x1", pd_multidraw),
    ]
)


def match(pattern: Treeish, data: Treeish, placedict: PlaceDict,) -> bool:
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
        left_matches = match(pattern.left, data.left, placedict)
        right_matches = match(pattern.right, data.right, placedict) or isinstance(
            pattern.right, Placeholder
        )
        if left_matches and right_matches:
            logger.debug(f"Candidates {pattern} {data}")
        return left_matches and right_matches
    if isinstance(pattern, Procedure) and isinstance(data, Procedure):
        if pattern.name == data.name:
            return True
    return False


def apply(replace: Treeish, placedict: PlaceDict,) -> Treeish:
    """ Apply the replacement to this tree and return result """
    if replace is None:
        return None
    if isinstance(replace, Value):
        return replace
    if isinstance(replace, Placeholder):
        return placedict[replace.x]
    if isinstance(replace, Procedure):
        return replace
    if isinstance(replace, Tree):
        left = apply(replace.left, placedict)
        right = apply(replace.right, placedict)
        return Tree(left, right)
    raise ValueError(r"invalid replace {replace}")


def compute(
    tree: Treeish, rewrite_rules: List[Rewrite] = REWRITES,
) -> (Tuple[Treeish, bool]):
    """
    NOTE: THIS POSSIBLY MUTATES THE TREE !!! 
    Returns tree, True if the tree was modified, tree, false if failed.
    If this returns True, possibly more rewrites can happen.
    """
    logger.debug(f"Computing Tree {tree}")
    if tree is None:
        return tree, False
    if not isinstance(tree, (Tree, Value, Placeholder, Procedure)):
        raise ValueError(f"Bad type for tree {tree} {type(tree)}")
    if isinstance(tree, Tree):
        # Check subtrees before this tree because matches are more likely in leaves
        tree.left, result = compute(tree.left, rewrite_rules)
        if result:
            return tree, True
    if isinstance(tree, (Tree, Value, Placeholder, Procedure)):
        tree_changed = False
        for rewrite in rewrite_rules:
            pd: PlaceDict = {}
            if match(rewrite.pattern, tree, pd) and rewrite.process(pd):
                # Awkwardly recompute this since we just consumed it
                pd = {}
                match(rewrite.pattern, tree, pd)
                # This is a little awkward because we want processing to occur
                # immediately after expansion without another expansion
                # opportunity to prevent infinite expansion of recursive
                # right-hand recursive procedures.
                if isinstance(tree, Tree) and tree.right:
                    tree.right, result = compute(tree.right, rewrite_rules)
                    if result:
                        tree_changed = True
                logger.debug(f"Tree matches {rewrite}")
                processing_occurred = rewrite.process(pd)
                if processing_occurred:
                    logger.debug("Processing occurred")
                    return apply(rewrite.replace, pd), True
        if tree_changed:
            return tree, True
    if isinstance(tree, Tree):
        tree.right, result = compute(tree.right, rewrite_rules)
        if result:
            return tree, True
    return tree, False


def compute_fully(tree: Treeish, rewrite_rules: List[Rewrite] = REWRITES,) -> (Treeish):
    """ Call compute on a tree until it converges """
    result = True
    while result:
        tree, result = compute(tree, rewrite_rules)
    return tree


def extract_procedures(script_lines: List[str]):
    procedures = []
    for line in script_lines:
        if line.startswith(":"):
            procedures.append(Rewrite.from_str(line))
    return procedures


def compute_script_fully(script: str):
    lines = script.strip().split("\n")
    procedures = extract_procedures(lines)
    for i, line in enumerate(lines):
        if not line.startswith(":"):
            left, right = line.strip().split("=")
            right_tree = deserialize(right)
            print("Executing", right_tree)
            print(compute(right_tree, REWRITES + procedures))


if __name__ == "__main__":
    import sys
    from serial import serialize, deserialize

    if len(sys.argv) == 2:
        tree = deserialize(sys.argv[1])
        print(serialize(compute_fully(tree)))
    else:
        print("Help: Run with a string argument to compute")
        print("  > python compute.py 'ap ap add 1 2'")
