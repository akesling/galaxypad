#!/usr/bin/env python

import math
import re

INT_PREFIX = re.compile(r"(01|10)(1*)0([01]*)")
INT_SIGN = {'01': 1, '10': -1}

def parse_binary_int(binary):
    """ Directly parse a sequence into a binary int """
    return sum(int(n)*2**i for i, n in enumerate(binary[::-1]))


def parse_partial(modulation):
    """ Parse the first complete item out of a modulation,
    and return the item and the remainder of the modulation """
    assert isinstance(modulation, str), f'bad type {type(modulation)}'
    assert modulation.count('1') + modulation.count('0') == len(modulation), modulation
    # Numbers:
    if INT_PREFIX.match(modulation):
        # Integer prefix, follow with ones and a zero
        # The length of the first group is the rest of the length // 4
        match = INT_PREFIX.match(modulation)
        sign, length_specifier, remainder = match.groups()
        length = len(length_specifier) * 4
        binary, unparsed = remainder[:length], remainder[length:]
        value = parse_binary_int(binary)
        return INT_SIGN[sign] * value, unparsed


def unparse(value):
    """ Unparse a value into a modulation """
    if isinstance(value, int):
        sign_mod = '01' if value >= 0 else '10'
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4) * 4
        prefix = sign_mod + '1' * length_units + '0'
        binary = '0' * (length_units * 4 - length) + bin(abs(value))[2:]
        return prefix + binary
    raise ValueError(f"Don't know what to do with {value}")