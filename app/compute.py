#!/usr/bin/env python

import random
import re
from dataclasses import dataclass
from typing import Optional, Union, List, Callable, Any, Tuple


INT_REGEX = re.compile(r"(-?\d+)")
VAR_REGEX = re.compile(r"x(\d+)")

_inc = lambda x: x + 1
_dec = lambda x: x - 1
_i = lambda x: x  # Identity
_add = lambda x: lambda y: y if x == 0 else x if y == 0 else x + y
_mul = lambda x: lambda y: y if x == 1 else x if y == 1 else x * y
_div = lambda x: lambda y: x if y == 1 else (x + (-x % y)) // y
_t = lambda x: lambda y: x
_f = lambda x: lambda y: y
_eq = lambda x: lambda y: _t if x == y else _f  # TODO: any special cases?
_pwr2 = lambda x: 2 ** x
_cons = lambda x: lambda y: lambda z:


LAMBDAS = dict(
    add=_add,
    dec=_dec,
    inc=_inc,
    i=_i,
    mul=_mul,
    div=_div,
    t=_t,
    f=_f,
    eq=_eq,
    pwr2=_pwr2,
)


@dataclass
class Variable:
    x: int


@dataclass
class Tree:
    """ Note this might not be a strict tree, and instead be a digraph """

    left: Optional[Union["Tree", Callable, int]] = None
    right: Optional[Union["Tree", Callable, int]] = None
    parent: Optional["Tree"] = None

    def is_leaf(self):
        return not isinstance(tree.left, Tree) and not isinstance(tree.right, Tree)


TreeOrLeaf = Union[Tree, Callable, int]


def compute(tree: Tree, seed=None, rs=None) -> Tuple[TreeOrLeaf, bool]:
    """ 
    Attempt to perform a computational reduction on the tree.
    If failed, return original tree and False.
    If true, return new (tree or leaf) and True.
    The first return value should be suitable to assign to a Tree.
    """
    pass
    # if rs is None:
    #     rs = random.Random(seed)
    # if tree.is_leaf() and callable(tree.left):
    #     return (tree.left(tree.right),)
    #     # Replace leaf with
    # coinflip = rs.randint(0, 1)
    # order = [[tree.left, tree.right], [tree.right, tree.left]][coin_flip]
    # for child in order:
    #     if child.compute():
    #         return True
    # return False


def get_value(token):
    if token in LAMBDAS:
        return LAMBDAS[token]
    if INT_REGEX.match(token):
        return int(token)
    if VAR_REGEX.match(token):
        return Variable(int(VAR_REGEX.match(token).groups()[0]))
    raise ValueError("Unknown token", token)


def tokens_to_tree(tokens: List[str]) -> Tuple[TreeOrLeaf, List[str]]:
    assert isinstance(tokens, list), f"bad tokens {tokens}"
    token: str = tokens.pop(0)
    if token == "ap":
        if len(tokens) == 0:
            left = None
        else:
            left, tokens = tokens_to_tree(tokens)
        if len(tokens) == 0:
            right = None
        else:
            right, tokens = tokens_to_tree(tokens)
        return Tree(left, right), tokens
    return get_value(token), tokens


if __name__ == "__main__":
    s = "ap"
    # s = 'ap dec ap ap add 1 2'
    tree, tokens = tokens_to_tree(s.split())
    print("tree", tree)
    print("tokens", tokens)
