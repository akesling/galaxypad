#!/usr/bin/env python

import math
import re

INT_PREFIX = re.compile(r"(01|10)(1*)0([01]*)")
INT_SIGN = {'01': 1, '10': -1}

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
        value = sum(int(n)*2**i for i, n in enumerate(binary[::-1]))
        return INT_SIGN[sign] * value, unparsed
    # Empty list
    if modulation.startswith('00'):
        # Hardcode this for now
        return [], modulation[2:]
    # List
    if modulation.startswith('11'):
        # I'm pretty sure this is how this works
        remainder = modulation[2:]
        head, remainder = parse_partial(remainder)
        tail, remainder = parse_partial(remainder)
        return [head, tail], remainder
    raise ValueError(f"Unmatched modulation {modulation}")


def unparse(value):
    """ Unparse a value into a modulation """
    if value == 0:
        return '010'
    if isinstance(value, int):
        sign_mod = '01' if value >= 0 else '10'
        length = len(bin(abs(value))) - 2  # Use the python bin() function
        length_units = math.ceil(length / 4)
        prefix = sign_mod + '1' * length_units + '0'
        binary = '0' * (length_units * 4 - length) + bin(abs(value))[2:]
        return prefix + binary
    if isinstance(value, list):
        # Special case empty list
        if value == []:
            return '00'
        assert len(value) == 2, 'Improper cons list'
        prefix = '11'
        head, tail = value
        return prefix + unparse(head) + unparse(tail)
    raise ValueError(f"Don't know what to do with {value}")


if __name__ == '__main__':
    import sys
    query = sys.argv[1]
    print('query', query)
    value, remainder = parse_partial(query)
    print('value', value)
    print('remainder', remainder)
    modulation = unparse(value)
    print('unparse')
    print('modulation', modulation)