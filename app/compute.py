#!/usr/bin/env python



# LIST_REGEXP = re.compile(r'')
# INT_REGEX = re.compile(r"(-?\d+)")

from dataclasses import dataclass
from typing import Optional, Union, List
import re


@dataclass
class Tree:
    token: str
    number: Union[List, int]
    left: Optional["Tree"]
    right: Optional["Tree"]

    def is_leaf(self):
        return self.left is None and self.right is None


def tokens_to_tree(tokens):
    assert len(tokens), "cant process empty tokens"
    if tokens[0] == 'ap':
        left, right_tokens = tokens_to_tree(tokens[1:])
        right, remainder = tokens_to_tree(right_tokens)
        return Tree('ap', left, right), remainder
    return tokens[0], tokens[1:]


if __name__ == '__main__':
    s = 'ap dec ap ap add 1 2'
    tree, tokens = tokens_to_tree(s.split())
    print('tree', tree)
    print('tokens', tokens)
