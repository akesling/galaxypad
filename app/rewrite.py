#!/usr/bin/env python

from typing import NamedTuple

from tree import Treeish, ProcessFn
from serial import deserialize


class Rewrite(NamedTuple):
    """ Pattern match to a reduction """

    pattern: Treeish
    replace: Treeish
    # Extra processing on the placeholders dictionary
    # good place for arithmetic, or side effects.
    # Returns False if this rewrite is invalid (for misc criterion, like numbers)
    process: ProcessFn = lambda x: True  # No-op default

    @classmethod
    def from_str(cls, s: str, process: ProcessFn = lambda x: True):
        """ Helper to build Rewrite rules in the same notation """
        assert s.count("=") == 1, f'string should have 1 "=", {s}'
        pattern_s, replace_s = s.split("=", 1)
        pattern = deserialize(pattern_s)
        replace = deserialize(replace_s)
        return cls(pattern=pattern, replace=replace, process=process)

