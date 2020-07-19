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
        fields = ",".join(f"{k}={repr(v)}" for k, v in sorted(vars(self).items()))
        return f"{self.__class__.__name__}({fields})"
    
    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class Atom(Expr):
    Name: str

    def __init__(self, Name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Name, str), repr(Name)
        self.Name = Name



class Ap(Expr):
    Fun: Expr
    Arg: Expr

    def __init__(self, Fun: Expr, Arg: Expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(Fun, Expr) and isinstance(Arg, Expr), repr(Fun) + repr(Arg)
        self.Fun = Fun
        self.Arg = Arg


cons: Expr = Atom("cons")
t: Expr = Atom("t")
f: Expr = Atom("f")
nil: Expr = Atom("nil")

functions: Dict[str, Expr] = {}


def parse(expression: str) -> Expr:
    """ Parse a complete expression """
    expr, tokens = parse_tokens(expression.strip().split())
    assert tokens == [], f"Leftover tokens {expression} -> {tokens}"
    return expr


def parse_tokens(tokens: List[str]) -> Tuple[Expr, List[str]]:
    """ Parse and return a complete expression, and leftover tokens """
    token, *tokens = tokens
    if token == "ap":
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
