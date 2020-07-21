#!/usr/bin/env python

from abc import abstractmethod, ABC
from itertools import zip_longest
from typing import Iterable, Optional, Union, List


class Expr(ABC):
    parent: Optional["Expr"]

    @abstractmethod
    def nlr(self) -> Iterable["Expr"]:
        raise NotImplementedError("Cannot use bare Expr")

    @abstractmethod
    def complete(self) -> bool:
        raise NotImplementedError("Cannot use bare Expr")


class Value(Expr):
    name: str

    def __init__(self, name: Union[int, str], parent: Optional[Expr] = None):
        self.name = str(name)
        self.parent = parent

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.name == other.name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.name)})"

    def nlr(self) -> Iterable[Expr]:
        yield self

    def complete(self) -> bool:
        return isinstance(self.name, str)


class Tree(Expr):
    left: Expr
    right: Expr

    def __init__(self, left: Expr, right: Expr, parent: Optional[Expr] = None):
        left.parent = self
        right.parent = self
        self.left = left
        self.right = right
        self.parent = parent

    def __eq__(self, other) -> bool:
        if type(self) == type(other):
            for s, o in zip_longest(self.nlr(), other.nlr()):
                if isinstance(s, Value) and isinstance(o, Value) and s != o:
                    return False
                if isinstance(s, Tree) and isinstance(o, Tree):
                    continue
                return False
            return True
        return False

    def __str__(self) -> str:
        return f"ap {str(self.left)} {str(self.right)}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)},{repr(self.right)})"

    def nlr(self) -> Iterable[Expr]:
        stack: List[Expr] = [self]
        while stack:
            expr: Expr = stack.pop()
            yield expr
            if isinstance(expr, Tree):
                assert isinstance(expr.right, Expr), f"{expr.right}"
                assert isinstance(expr.left, Expr), f"{expr.left}"
                stack.append(expr.right)
                stack.append(expr.left)

    def complete(self) -> bool:
        for expr in self.nlr():
            if isinstance(expr, Value) and expr.complete():
                continue
            if (
                isinstance(expr, Tree)
                and isinstance(expr.left, Expr)
                and isinstance(expr.right, Expr)
            ):
                continue
            return False
        return True


def parse(string: str) -> Expr:
    raise NotImplementedError('TODO')


def unparse(expr: Expr) -> str:
    raise NotImplementedError('TODO')



if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        print(parse(sys.argv[1]))
    else:
        print(f"Usage: {sys.argv[0]} 'ap inc 0'")