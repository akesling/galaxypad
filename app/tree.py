#!/usr/bin/env python
import re
from dataclasses import dataclass
from typing import Tuple, List, Optional, Union, Dict, NamedTuple

INT_REGEX = re.compile(r"(-?\d+)")
TOKENS = "add i".split()


class Value(NamedTuple):
    """ Leaf in the tree """

    value: Union[int, str]

    @classmethod
    def from_token(cls, token):
        if INT_REGEX.match(token):
            return cls(int(token))
        assert token in TOKENS, f"bad token {token}"
        return cls(token)


class Placeholder(NamedTuple):
    """ Placeholder value for using in Rewrite expressions """

    x: int


@dataclass
class Tree:  # I wish I could make this a NamedTuple, but mypy hates it
    """ Note this might not be a strict tree, and instead be a digraph """

    left: Optional[Union["Tree", Value, Placeholder]] = None
    right: Optional[Union["Tree", Value, Placeholder]] = None


class Rewrite(NamedTuple):
    """ Pattern match to a reduction """

    pattern: Tree
    replace: Union[Tree, Value, Placeholder]


_i = Value("i")
_add = Value("add")
_0 = Value(0)
x0 = Placeholder(0)
REDUCTIONS = [
    Rewrite(Tree(_i, x0), x0),  # Identity
    Rewrite(Tree(_add, _0), _i),  # Additive identity
    Rewrite(Tree(Tree(_add, x0), _0), x0),  # Additive identity
]

PlaceDict = Dict[int, Optional[Union[Tree, Value, Placeholder]]]


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
    If this returns True, possibly more reductions can happen.
    """
    if tree is None or isinstance(tree, Value) or isinstance(tree, Placeholder):
        return tree, False
    if not isinstance(tree, Tree):
        raise ValueError(f'bad tree {tree}')
    for evaluation in EVALUATIONS:

    for reduction in REDUCTIONS:
        placedict: PlaceDict = {}
        if match(reduction.pattern, tree, placedict):
            return apply(reduction.replace, placedict), True
    if isinstance(tree.left, Tree):
        tree.left, result = compute(tree.left)
        if result:
            return tree, True
    if isinstance(tree.right, Tree):
        tree.right, result = compute(tree.right)
        if result:
            return tree, True
    return tree, False


def parse_tree(tokens: List[str]) -> Union[Tree, Value]:
    """ NOTE: THIS MUTATES THE TOKENS LIST !!! """
    assert isinstance(tokens, list), f"bad tokens {tokens}"
    token: str = tokens.pop(0)
    if token == "ap":
        left = parse_tree(tokens) if len(tokens) else None
        right = parse_tree(tokens) if len(tokens) else None
        return Tree(left, right)
    return Value.from_token(token)


if __name__ == "__main__":
    tokens = "ap ap add 0 1".split()
    tree = parse_tree(tokens)
    print("tree", tree)

    result = True
    while result:
        tree, result = compute(tree)  # type: ignore
        print("tree", tree)
