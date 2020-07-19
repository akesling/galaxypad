#!/usr/bin/env python

from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, Dict


class Expr:
    Evaluated: Optional["Expr"]

    def __init__(self, Evaluated: Optional["Expr"] = None):
        assert Evaluated is None or isinstance(Evaluated, self.__class__), repr(
            Evaluated
        )
        self.Evaluated = Evaluated

    def __repr__(self):
        return f"Expr(Evaluated={repr(self.Evaluated)})"

    # def __eq__(self, other):
    #     return isinstance(other, type(self)) and self.Evaluated == other.Evaluated
    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class Atom(Expr):
    Name: str

    def __init__(self, Name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Name, str), repr(Name)
        self.Name = Name

    def __repr__(self):
        return f"Atom(Name={repr(self.Name)},Evaluated={repr(self.Evaluated)})"

    # def __eq__(self, other):
    #     return (
    #         isinstance(other, type(self))
    #         and self.Name == other.Name
    #         and self.Evaluated == other.Evaluated
    #     )


class Ap(Expr):
    Fun: Expr
    Arg: Expr

    def __init__(self, Fun: Expr, Arg: Expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Fun, Expr) and isinstance(Arg, Expr), repr(Fun) + repr(Arg)
        self.Fun = Fun
        self.Arg = Arg

    def __repr__(self):
        return f"Ap(Fun={repr(self.Fun)},Arg={repr(self.Arg)},Evaluated={repr(self.Evaluated)})"

    # def __eq__(self, other):
    #     return (
    #         isinstance(other, type(self))
    #         and self.Fun == other.Fun
    #         and self.Arg == other.Arg
    #         and self.Evaluated == other.Evaluated
    #     )


cons: Expr = Atom('cons')
t: Expr = Atom('t')
f: Expr = Atom('f')
nil: Expr = Atom('nil')

functions: Dict[str, Expr] = {}


def parse(expression: str) -> Expr:
    """ Parse a complete expression """
    expr, tokens = parse_tokens(expression.strip().split())
    assert tokens == [], f'Leftover tokens {expression} -> {tokens}'
    return expr


def parse_tokens(tokens: List[str]) -> Tuple[Expr, List[str]]:
    """ Parse and return a complete expression, and leftover tokens """
    token, *tokens = tokens
    if token == 'ap':
        fun, tokens = parse_tokens(tokens)
        arg, tokens = parse_tokens(tokens)
        return Ap(Fun=fun, Arg=arg), tokens
    return Atom(token), tokens


if __name__ == "__main__":
    print(Expr())
    print(Ap(Expr(), Expr()))
    print(Atom("hello"))
    print(Ap(Fun=Expr(Evaluated=None), Arg=Expr(Evaluated=None), Evaluated=None))


# @dataclass
# class Expr:
#     Evaluated: Optional['Expr'] = None

# @dataclass
# class Atom(Expr):
#     Name: str = 'invalid'

# @dataclass
# class Ap:
#     Fun: 'Expr'
#     Arg: 'Expr'
#     Evaluated: Optional['Expr'] = None

# Expr = Union[Atom, Ap]
