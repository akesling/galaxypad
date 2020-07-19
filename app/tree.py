#!/usr/bin/env python

import re
from dataclasses import dataclass
from typing import NamedTuple, Union, Optional, Callable, Dict, List, Tuple

from renderer import DrawState


class Value(NamedTuple):
    """ Leaf in the tree """

    value: Union[int, str, DrawState]


class Placeholder(NamedTuple):
    """ Placeholder value for using in Rewrite expressions """

    x: int


class Procedure(NamedTuple):
    """ A procedure to be lazily invoked through rewriting """

    name: int


@dataclass
class Tree:  # I wish I could make this a NamedTuple, but mypy hates it
    """ Note this might not be a strict tree, and instead be a digraph """

    left: Optional[Union["Tree", Value, Placeholder, Procedure, DrawState]] = None
    right: Optional[Union["Tree", Value, Placeholder, Procedure, DrawState]] = None

    evaluated: Optional[Union["Tree", Value, Placeholder, Procedure, DrawState]] = None


# Taking a line from the "git" book on naming things
Treeish = Optional[Union[Tree, Value, Placeholder, Procedure, DrawState]]
PlaceDict = Dict[int, Treeish]
ProcessFn = Callable[[PlaceDict], bool]


def pair(x: Treeish, y: Treeish) -> Treeish:
    """ Helper function to get the tree representation of a pair"""
    return Tree(Tree(Value("cons"), x), y)
