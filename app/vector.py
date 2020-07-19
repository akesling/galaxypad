#!/usr/bin/env python

from typing import Union, List
from tree import Treeish, Value, Tree, pair

from renderer import DrawState

Vector = Union[List, int]


def vector(treeish: Treeish) -> Vector:
    """ Reverse of the vector function """
    if isinstance(treeish, Value):
        if treeish == Value("nil"):
            return []
        if isinstance(treeish.value, int):
            return treeish.value
        if isinstance(treeish.value, DrawState):
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
    if isinstance(vec, DrawState):
        return Value(vec)
    if vec == []:
        return Value("nil")
    if isinstance(vec, list):
        head, *tail = vec
        return pair(unvector(head), unvector(tail))
    raise ValueError(f"Can't unvector (maybe you want vector) {vec}")
