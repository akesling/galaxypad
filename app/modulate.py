#!/usr/bin/env python

import math
import re
from typing import NamedTuple, Tuple, Union

from tree import (
    Placeholder,
    Procedure,
    Tree,
    Treeish,
    Value,
    pair,
)
from vector import Vector, vector, unvector

MOD_PATTERN = re.compile(r"[01]*")
INT_PREFIX = re.compile(r"(01|10)(1*)0([01]*)")
INT_SIGN = {"01": 1, "10": -1}


class Modulation(NamedTuple):
    """ Type for modulation strings """

    bits: str = ""


def demodulate(modulation: Modulation) -> Treeish:
    """ Demodulate a complete modulation, Error if leftover """
    treeish, remainder = demodulate_partial(modulation)
    assert remainder == "", f"failed to fully parse {modulation} -> {remainder}"
    return treeish


def demodulate_partial(modulation: Union[Modulation, str]) -> Tuple[Treeish, str]:
    """
    Parse the first complete item out of a modulation,
    and return the item and the remainder of the modulation
    """
    # For convenience we can just call this method on a bit string
    if isinstance(modulation, Modulation):
        bits = modulation.bits
    elif isinstance(modulation, str):
        bits = modulation
    else:
        raise ValueError(f"Improper modulation {modulation}")
    assert MOD_PATTERN.fullmatch(bits), f"bad bits {bits}"
    # Numbers:
    int_match = INT_PREFIX.match(bits)
    if int_match is not None:
        # Integer prefix, follow with ones and a zero
        # The length of the first group is the rest of the length // 4
        sign, length_specifier, remainder = int_match.groups()
        length = len(length_specifier) * 4
        binary, unparsed = remainder[:length], remainder[length:]
        value = sum(int(n) * 2 ** i for i, n in enumerate(binary[::-1]))
        return Value(INT_SIGN[sign] * value), unparsed
    # Empty list
    if bits.startswith("00"):
        # Hardcode this for now
        return Value("nil"), bits[2:]
    # List
    if bits.startswith("11"):
        # I'm pretty sure this is how this works
        remainder = bits[2:]
        head, remainder = demodulate_partial(remainder)
        tail, remainder = demodulate_partial(remainder)
        return pair(head, tail), remainder
    raise ValueError(f"Unmatched modulation {modulation}")


def modulate(treeish: Treeish) -> Modulation:
    """ modulate a value into a modulation """
    if treeish is None:
        return Modulation("")
    if treeish == Value("nil"):
        return Modulation("00")
    if treeish == Value(0):
        return Modulation("010")
    if isinstance(treeish, Value) and isinstance(treeish.value, int):
        value = treeish.value
        sign_mod = "01" if value >= 0 else "10"
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4)
        prefix = sign_mod + "1" * length_units + "0"
        binary = "0" * (length_units * 4 - length) + bin(abs(value))[2:]
        return Modulation(prefix + binary)
    if isinstance(treeish, Tree):
        # Note: this replicates some of the work in vector()
        # We have to do that because sometimes we modulate improper lists
        # Such as the list "ap ap cons 0 1"
        left_tree = treeish.left
        if isinstance(left_tree, Tree) and left_tree.left in (
            # This is a bit ugly but both are valid unfortunately
            Value("cons"),
            Value("vec"),
        ):
            left_bits = modulate(left_tree.right).bits
            right_bits = modulate(treeish.right).bits
            return Modulation("11" + left_bits + right_bits)
    raise ValueError(f"Don't know what to do with {treeish}")


def modulate_vector(vec: Vector) -> Modulation:
    """ modulate a compact vector into a modulation """
    if isinstance(vec, (int, list)):
        return modulate(unvector(vec))
    raise ValueError(f"Can't modulate vector {vec}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        modulation = Modulation(sys.argv[1])
        print("parsing Modulation", modulation)
        tree, remainder = demodulate_partial(modulation)
        print("tree", tree)
        print("remainder", remainder)
        vec = vector(tree)
        print("vector", vec)
        mod = modulate(unvector(vec))
        print("mod", mod)
    else:
        print("Help: Run with a string argument to demodulate")
        print(
            "  > python mod_parser.py '1101100001111101100010110110001100110110010000'"
        )
