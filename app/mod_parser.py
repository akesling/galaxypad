#!/usr/bin/env python

import math
import re
from typing import NamedTuple, Tuple, Union

from tree import Value, pair, Tree, unvector, Treeish

MOD_PATTERN = re.compile(r"[01]*")
INT_PREFIX = re.compile(r"(01|10)(1*)0([01]*)")
INT_SIGN = {"01": 1, "10": -1}


class Modulation(NamedTuple):
    """ Type for modulation strings """

    bits: str = ""


def parse(modulation: Modulation) -> Treeish:
    """ Wrap parse_partial with assertion that parse is complete """
    treeish, remainder = parse_partial(modulation)
    assert remainder == "", f"failed to fully parse {modulation}"
    return treeish


def parse_partial(modulation: Union[Modulation, str]) -> Tuple[Treeish, str]:
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
        head, remainder = parse_partial(remainder)
        tail, remainder = parse_partial(remainder)
        return pair(head, tail), remainder
    raise ValueError(f"Unmatched modulation {modulation}")


def unparse(value):
    """ Unparse a value into a modulation """
    if isinstance(value, Value):
        if isinstance(value.value, int):
            value = value.value  # Unpack from value object
        if value == Value("nil"):
            value = []
        else:
            raise ValueError(f"Can't parse value {value}")
    if value == 0:
        return "010"
    if isinstance(value, int):
        sign_mod = "01" if value >= 0 else "10"
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4)
        prefix = sign_mod + "1" * length_units + "0"
        binary = "0" * (length_units * 4 - length) + bin(abs(value))[2:]
        return prefix + binary
    if isinstance(value, Tree):
        value = unvector(value)  # Unpack a cons list
    if isinstance(value, list):
        # Special case empty list
        if value == []:
            return "00"
        assert len(value) == 2, "Improper cons list"
        prefix = "11"
        head, tail = value
        return prefix + unparse(head) + unparse(tail)
    raise ValueError(f"Don't know what to do with {value}")


if __name__ == "__main__":
    import sys

    query = sys.argv[1]
    print("query", query)
    value, remainder = parse_partial(query)
    print("value", value)
    print("remainder", remainder)
    modulation = unparse(value)
    print("unparse")
    print("modulation", modulation)

