from typing import Union, Tuple
import logging

__all__ = [
    'compile',
]

logger = logging.getLogger('lib.icfp_interpreter')

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

    def _run(self, tokens: [[str]], *args, line_offset=0, token_offset=0):
        # TODO(akesling): Set initial variables based on args values
        variables = {}

        for li, line in enumerate(tokens):
            active_value = lambda x: x
            for ti, tkn in enumerate(line):
                logger.debug(
                    'Executing Line: %s Token: %s -- %s',
                    line_offset+li, token_offset+ti, tkn)

                if tkn == '#' or tkn == '...':
                    logger.debug(
                        'Skipping comment or block delimeter on line %s',
                        line_offset+li)
                    break

                if tkn in self.non_terminals:
                    active_value = active_value(self.non_terminals[tkn])
                    continue

                if tkn == ':=':
                    left_value = active_value
                    right_value = self._run(
                        tokens=[line[ti+1:]], line_offset=li, token_offset=ti+1)
                    if left_value == right_value:
                        break
                    else:
                        left_is_variable = isinstance(left_value, Variable)
                        right_is_variable = isinstance(right_value, Variable)
                        if left_is_variable and right_is_variable:
                            if left_value.is_equivalent_to(right_value):
                                break
                            raise NotImplementedError(
                                'Resolution of variable co-definition is not '
                                'yet implemented.')
                        elif left_is_variable:
                            # NOTE(akesling): This style of assignment hasn't
                            # been seen in the signals so far.
                            variables[left_value.name] = right_value
                        elif right_is_variable:
                            # NOTE(akesling): This style of assignment hasn't
                            # been seen in the signals so far.
                            variables[right_value.name] = left_value
                        else:
                            raise Exception(
                                'An unknown error occurred for definition with '
                                '"left value" (%s) and "right value" (%s)' % (
                                    left_value, right_value))
                        break

                if tkn.startswith('x'):
                    variables[tkn] = None
                    active_value = active_value(Variable(tkn))
                    continue

                if tkn == 't':
                    active_value = active_value(True)
                    continue

                if tkn == 'f':
                    active_value = active_value(False)
                    continue

                active_value = active_value(int(tkn))

        return active_value

    # Operators
    ap = lambda arg1: lambda arg2: arg1(arg2)

    add = lambda arg1: lambda arg2: arg1 + arg2
    mul = lambda arg1: lambda arg2: arg1 * arg2

    # Integer division rounding toward zero
    div = lambda arg1: lambda arg2: (abs(arg1) // abs(arg2)) * (-1 if (arg1*arg2 < 0) else 1)

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

class Variable:
    # TODO(akesling): Figure out op accumulation
    def __init__(self, name: str):
        self.name = name
        self._ops: [Tuple(str, Union[None, int, Variable])] = []

    def __abs__(self):
        self._ops.append(('abs', None))
        return self

    def __add__(self, other):
        if isinstance(other, Variable):
            self._ops.append(('add', other.copy()))
            return self

        if isinstance(other, int):
            if other == 0:
                return self

            self._ops.append(('add', other))
            return self

        if isinstance(other, bool):
            raise NotImplementedError(
                'Variable addition with booleans is not implemented')

        raise Exception(
            'Addition with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __mul__(self, other):
        if isinstance(other, Variable):
            self._ops.append(('mul', other.copy()))
            return self

        if isinstance(other, int):
            if other == 1:
                return self

            self._ops.append(('mul', other))
            return self

        if isinstance(other, bool):
            raise NotImplementedError(
                'Variable multiplication with booleans is not implemented')

        raise Exception(
            'Multiplication with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __floordiv__(self, other):
        if isinstance(other, Variable):
            self._ops.append(('floordiv', other.copy()))
            return self

        if isinstance(other, int):
            if other == 1:
                return self

            self._ops.append(('floordiv', other))
            return self

        if isinstance(other, bool):
            raise NotImplementedError(
                'Variable division with booleans is not implemented')

        raise Exception(
            'Addition with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __eq__(self, other):
        if isinstance(other, Variable):
            if (other.name == self.name and
                sorted(other._ops) == sorted(self._ops)):
                return True
            self._ops.append(('eq', other.copy()))
            return self

        if isinstance(other, int) or isinstance(other, bool):
            self._ops.append(('eq', other))
            return self

        raise Exception(
            'Equality with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __lt__(self, other):
        if isinstance(other, Variable):
            self._ops.append(('lt', other.copy()))
            return self

        if isinstance(other, int) or isinstance(other, bool):
            self._ops.append(('lt', other))
            return self

        raise Exception(
            'Less-than with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def copy(self):
        new_variable = Variable(self.name)
        new_variable._ops = self._ops[:]
        return new_variable

    def is_modified(self):
        return bool(self._ops)

    def is_equivalent_to(self, other):
        if isinstance(other, Variable):
            if len(self._ops) == 0 and len(other._ops) == 0:
                return True

        raise NotImplementedError(
            'Equivalency between these two values is not yet defined')
