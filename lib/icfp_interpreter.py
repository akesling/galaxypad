from typing import Union, Tuple
import logging

__all__ = [
    'compile',
]

logger = logging.getLogger('lib.icfp_interpreter')

class Transmission(BaseException):
    def __init__(self, value):
        self.value = value

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

                if tkn == ':=':
                    left_value = active_value
                    try:
                        runner = self._run(
                            tokens=[line[ti+1:]], line_offset=li, token_offset=ti+1)
                        while True:
                            # TODO(akesling): Handle the case where the
                            # subexpression contains tx
                            runner.send(None)
                    except StopIteration as result:
                        right_value = result.value

                    left_is_variable = isinstance(left_value, Variable)
                    right_is_variable = isinstance(right_value, Variable)
                    if (not left_is_variable and not right_is_variable
                            and left_value == right_value):
                        break
                    else:
                        if left_is_variable and right_is_variable:
                            # TODO(akesling): Implement definition for two
                            # variables relative to each other
                            if left_value.is_equivalent_to(right_value):
                                break
                            raise NotImplementedError(
                                'Resolution of variable co-definition is not '
                                'yet implemented.')
                        elif left_is_variable:
                            # NOTE(akesling): This style of assignment hasn't
                            # been seen in the signals so far.
                            if (left_value.name in variables
                                    and variables[left_value.name]):
                                raise Exception(
                                    'Variable "%s" has been defined twice, '
                                    'first with value "%s" and second with '
                                    'value "%s"' % (
                                        left_value.name,
                                        variables[left_value.name],
                                        right_value))
                            variables[left_value.name] = right_value
                        elif right_is_variable:
                            # NOTE(akesling): This style of assignment hasn't
                            # been seen in the signals so far.
                            if (right_value.name in variables
                                    and variables[right_is_variable.name]):
                                raise Exception(
                                    'Variable "%s" has been defined twice, '
                                    'first with value "%s" and second with '
                                    'value "%s"' % (
                                        right_value.name,
                                        variables[right_value.name],
                                        left_value))
                            variables[right_value.name] = left_value
                        else:
                            raise Exception(
                                'An unknown error occurred for definition with '
                                '"left value" (%s) and "right value" (%s)' % (
                                    left_value, right_value))
                        break

                try:
                    active_value = active_value(self._parse(tkn))
                except Transmission as t:
                    tx_value = self._serialize(t.value, variables)
                    logger.debug('Transmitting value "%s"', tx_value)

                    received_message = (yield tx_value)

                    logger.debug('Received value "%s"', received_message)
                    active_value = self._parse(received_message)
                    continue
                    # TODO(akesling): Figure out what form the received value
                    # should *actually* be.  Is it a set of arbitrary
                    # expressions?  If so, we'll need to manage nested
                    # transmission.

        return active_value

    def _parse(self, token):
        if token in self.non_terminals:
            return self.non_terminals[token]

        if token.startswith('x'):
            return Variable(token)

        if token == 't':
            return True

        if token == 'f':
            return False

        return int(token)

    def _serialize(self, value, variable_lookup):
        if isinstance(value, Variable):
            if value.is_modified():
                raise NotImplementedError(
                    'Transmitting modified variables is not yet '
                    'implemented')
            return self._serialize(variable_lookup[value.name], variable_lookup)

        if value is True:
            return 't'

        if value is False:
            return 'f'

        if isinstance(value, int):
            return str(value)

        raise ValueError(
            'Value provided is not of a serializable type %s' % value)

    # Operators
    ap = lambda arg1: lambda arg2: arg1(arg2)

    add = lambda arg1: lambda arg2: arg1 + arg2
    mul = lambda arg1: lambda arg2: arg1 * arg2

    def transmit(arg1):
        raise Transmission(arg1)

    # Integer division rounding toward zero
    # div = lambda arg1: lambda arg2: (abs(arg1) // abs(arg2)) * (-1 if (arg1*arg2 < 0) else 1)
    def div(arg1):
        def apply(arg2):
            left_is_variable = isinstance(arg1, Variable)
            right_is_variable = isinstance(arg2, Variable)
            # To avoid accumulating unnecessary ops on Variables, distinguish
            # whether to delegate to the Variable or apply here.
            if left_is_variable or right_is_variable:
                return arg1 // arg2
            else:
                return (abs(arg1) // abs(arg2)) * (-1 if (arg1*arg2 < 0) else 1)
        return apply

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
        'tx': transmit,
    }

class Variable:
    # TODO(akesling): Figure out op accumulation
    def __init__(self, name: str):
        self.name = name
        self._ops: [Tuple(str, Union[None, int, Variable])] = []

    def __repr__(self):
        return 'Variable<Name: %s, Ops: %s>' % (
            self.name, self._ops)

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

    def __radd__(self, other):
        return self.__add__(other)

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

    def __rmul__(self, other):
        return self.__mul__(other)

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

    def __rfloordiv__(self, other):
        raise NotImplementedError(
            'A Variable being divided into non-variable is not yet supported')

    def __eq__(self, other):
        if isinstance(other, Variable):
            if self.is_equivalent_to(other):
                return True
            self._ops.append(('eq', other.copy()))
            return self

        if isinstance(other, int) or isinstance(other, bool):
            self._ops.append(('eq', other))
            return self

        raise Exception(
            'Equality with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __req__(self, other):
        return self.__eq__(other)

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

    def __gt__(self, other):
        if isinstance(other, Variable):
            self._ops.append(('gt', other.copy()))
            return self

        if isinstance(other, int) or isinstance(other, bool):
            self._ops.append(('gt', other))
            return self

        raise Exception(
            'Greater-than with unknown value/type detected, %s/%s' % (
                other, type(other)))

    def __rlt__(self, other):
        return self.__gt__(other)

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

            if (other.name == self.name and
                sorted(other._ops) == sorted(self._ops)):
                return True

        raise NotImplementedError(
            'Equivalency between these two values is not yet defined: '
            '%s ?= %s' % (self, other))
