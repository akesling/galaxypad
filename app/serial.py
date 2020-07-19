#!/usr/bin/env python

import re
from dataclasses import dataclass
from typing import NamedTuple, Union, Optional, Callable, Dict, List, Tuple

from tree import Value, Placeholder, Procedure, Tree, Treeish
from vector import unvector


INT_REGEX = re.compile(r"(-?\d+)")
VAR_REGEX = re.compile(r"x(\d+)")
PROC_REGEX = re.compile(r":(\d+)")
# VECT_MATCH = re.compile(r"[^(]")
# VECTOR_MATCH = re.compile(r"\s*(ap\s+ap\s+cons\s+\d+\s+)+nil\s*")
# VECTOR_PARSE = re.compile(r"\s*ap\s+ap\s+cons\s+(\d+)\s+")
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
    "checkerboard",
    "draw",
    "multipledraw",
    "modem",
    "f38",
    "statelessdraw",
    "interact",
]


def deserialize(serial: str) -> Treeish:
    """ Read 'ap ap add 1 2' language into a Tree """
    # HACK: special case super-long vectors
    # if VECTOR_MATCH.fullmatch(serial) is not None:
    #     print('vector match')
    #     vector = [int(i) for i in VECTOR_PARSE.findall(serial)]
    #     return unvector(vector)
    # print('vector not match', serial[:100])
    treeish, remainder = deserialize_tokens(serial.strip().split())
    assert remainder == [], f"Deserialize failed {serial} -> {remainder}"
    return treeish


def deserialize_tokens(tokens: List[str],) -> Tuple[Treeish, List[str]]:
    """ Returns parsed tree, and leftover tokens """
    assert isinstance(tokens, list), f"bad tokens {tokens}"
    if tokens == []:
        return None, []
    token, tokens = tokens[0], tokens[1:]
    if token == "ap":
        left, tokens = deserialize_tokens(tokens)
        right, tokens = deserialize_tokens(tokens)
        return Tree(left, right), tokens
    if INT_REGEX.match(token):
        return Value(int(token)), tokens
    if token in KNOWN_TOKENS:
        return Value(token), tokens
    if VAR_REGEX.match(token):
        return Placeholder(int(token[1:])), tokens
    if PROC_REGEX.match(token):
        return Procedure(int(token[1:])), tokens
    raise ValueError(f"Unknown token {token} (probably add to KNOWN_TOKENS)")


def serialize(treeish: Treeish) -> str:
    """ Reverse back into the 'ap ap add 1 2' language form """
    if treeish is None:
        return ""
    if isinstance(treeish, Value):
        return f"{treeish.value}"
    if isinstance(treeish, Placeholder):
        return f"s{treeish.x}"
    if isinstance(treeish, Procedure):
        return f":{treeish.name}"
    if isinstance(treeish, Tree):
        return " ".join(
            ["ap", serialize(treeish.left), serialize(treeish.right)]
        ).strip()
    raise ValueError(f"Don't know how to serialize {treeish}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        print(deserialize(sys.argv[1]))
    else:
        print("Help: Run with a string argument to deserialize")
        print("  > python app/serial.py 'ap ap add 1 2'")
