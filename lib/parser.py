#!/usr/bin/env python

INT_PREFIX = re.compile(r"01(1*)0([01]*)")
NEG_PREFIX = re.compile(r"10(1*)0([01]*)")

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
        length_specifier, remainder = match.groups()
        length = len(length_specifier) * 4
        binary, unparsed = remainder[:length], remainder[length:]
        value = parse_binary_int(binary)
        return value, unparsed
    if NEG_PREFIX.match(modulation):
        # Same as integer but for negative numbers
        match = NEG_PREFIX.match(modulation)
        length_specifier, remainder = match.groups()
        length = len(length_specifier) * 4
        binary, unparsed = remainder[:length], remainder[length:]
        value = -parse_binary_int(binary)  # Negative!
        return value, unparsed
