from typing import Union, Tuple

__all__ = [
    'compile',
]

def compile(code: str):
    return _ICFPTokenInterpreter(_tokenize(code.split('\n')))

def _tokenize(code: [str]):
    return [list(filter(lambda x: x, line.strip().split(' '))) for line in code]

# Make sure to preserve the interface between this Interpreter and the ICFP JIT
# in `sidecar`.
class _ICFPTokenInterpreter:
    def __init__(self, tokens: [[str]]):
        self._program = tokens

    def __call__(self, *args):
        return self._run(self._program, args)

    def _run(self, tokens: [[str]], *args):
        # TODO(akesling): Set initial variables based on args values
        variables = {}

        for line in tokens:
            active_value = lambda x: x
            for i, tkn in enumerate(line):
                print(tkn)

                if tkn == '#' or tkn == '...':
                    break

                if tkn in self.non_terminals:
                    active_value = active_value(self.non_terminals[tkn])
                    continue

                if tkn == ':=':
                    left_value = active_value
                    right_value = self._run([line[i+1:]])
                    if left_value == right_value:
                        break
                    else:
                        # NOTE(akesling): This style of assignment hasn't been
                        # seen in the signals so far.
                        if isinstance(left_value, self.Variable):
                            variables[left_value.name] = (
                                self.Variable.copy(left_value))
                            break
                        else:
                            raise Exception(
                                'An unknown error occurred for definition with '
                                '"left value" (%s) and "right value" (%s)' % (
                                    left_value, right_value))

                if tkn.startswith('x'):
                    variables[tkn] = None
                    active_value = active_value(self.Variable(tkn))
                    continue

                active_value = active_value(int(tkn))

        return active_value

    class Variable:
        # TODO(akesling): Figure out op accumulation
        def __init__(self, name: str):
            self.name = name
            self._ops: [Tuple(str, Union[int, Variable])] = []

        @staticmethod
        def copy(self, other):
            raise NotImplementedError(
                'Variable copying is not yet implemented.')

    # Operators
    ap = lambda arg1: lambda arg2: arg1(arg2)

    add = lambda arg1: lambda arg2: arg1 + arg2
    mul = lambda arg1: lambda arg2: arg1 * arg2

    # Integer division rounding toward zero
    div = lambda arg1: lambda arg2: (-1 * (arg1*arg2 < 0)) * (abs(arg1) // abs(arg2))

    inc = lambda arg: arg + 1
    dec = lambda arg: arg - 1

    eq = lambda arg1: lambda arg2: arg1 == arg2
    lt = lambda arg1: lambda arg2: arg1 < arg2

    non_terminals = {
        'ap': ap,
        'add': add,
        'mul': mul,
        'div': div,
        'inc': inc,
        'dec': dec,
        'eq': eq,
        'lt': lt,
    }
