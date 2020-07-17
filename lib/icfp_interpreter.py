from typing import Union, Tuple, List
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

# Operators
ap = lambda arg1: lambda arg2: arg1(arg2)
substitution = lambda arg1: lambda arg2: lambda arg3: arg1(arg3)(arg2(arg3))

add = lambda arg1: lambda arg2: arg1 + arg2
mul = lambda arg1: lambda arg2: arg1 * arg2
neg = lambda arg1: arg1 * -1

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
    'neg': neg,
    'div': div,
    'inc': inc,
    'dec': dec,
    'eq': eq,
    'lt': lt,
    'tx': transmit,
    's': substitution,
}

# Make sure to preserve the interface between this Interpreter and the ICFP JIT
# in `sidecar`.
class _ICFPTokenInterpreter:
    def __init__(self, tokens: [[str]]):
        self._program = tokens

    def __call__(self, *args):
        return self._run(self._program, args)

    def _run(
            self, tokens: [[str]], *args, line_offset=0, token_offset=0,
            init_variables=None) -> (
                List[List]):
        # TODO(akesling): Set initial variables based on args values
        variables = {}
        if init_variables:
            variables.update(init_variables)

        line_results = []
        for li, line in enumerate(tokens):
            if len(line) and (line[0] == '#' or line[0] == '...'):
                logger.debug(
                    'Skipping comment or block delimeter on line %s',
                    line_offset+li)
                continue

            definition_index = [i for i,x in enumerate(line) if x == ':=']
            if len(definition_index):
                definition_index = definition_index[0]
                try:
                    runner = self._run(
                        tokens=[line[:definition_index]],
                        line_offset=li,
                        token_offset=0,
                        init_variables=variables)
                    msg_received = None
                    while True:
                        msg_received = (yield runner.send(msg_received))
                except StopIteration as result:
                    left_value = result.value

                try:
                    runner = self._run(
                        tokens=[line[definition_index+1:]],
                        line_offset=li,
                        token_offset=definition_index+1,
                        init_variables=variables)
                    msg_received = None
                    while True:
                        msg_received = (yield runner.send(msg_received))
                except StopIteration as result:
                    right_value = result.value

                self._define(left_value[0][0], right_value[0][0], variables)
                continue

            stack = []
            for ti, tkn in reversed(list(enumerate(line))):
                logger.debug(
                    'Executing Line: %s Token: %s -- %s',
                    line_offset+li, token_offset+ti, tkn)

                try:
                    parsed_token = self._parse(tkn)
                    if (not isinstance(parsed_token, Variable) 
                            and parsed_token == ap):
                        tmp = parsed_token(stack.pop())
                        stack.append(tmp(stack.pop()))
                    else:
                        stack.append(parsed_token)

                except Transmission as t:
                    tx_value = self._serialize(t.value, variables)
                    logger.debug('Transmitting value "%s"', tx_value)

                    received_message = (yield tx_value)

                    logger.debug('Received value "%s"', received_message)
                    # NOTE(akesling): If this is `ap`, it won't be applied
                    stack.append(self._parse(received_message))
                    continue
                    # TODO(akesling): Figure out what form the received value
                    # should *actually* be.  Is it a set of arbitrary
                    # expressions?  If so, we'll need to manage nested
                    # transmission.
            line_results.append(stack)

        return line_results

    def _parse(self, token):
        if token in non_terminals:
            return non_terminals[token]

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
            if value.name not in variable_lookup:
                raise ValueError(
                    'Variable cannot be serialized as it is not yet defined.')
            return self._serialize(
                variable_lookup[value.name], variable_lookup)

        if value is True:
            return 't'

        if value is False:
            return 'f'

        if isinstance(value, int):
            return str(value)

        raise ValueError(
            'Value provided is not of a serializable type %s' % value)

    def _define(self, left_value, right_value, variable_lookup):
        left_is_variable = isinstance(left_value, Variable)
        right_is_variable = isinstance(right_value, Variable)
        if (not left_is_variable and not right_is_variable
                and left_value == right_value):
            logger.debug('Left and right values are equal in definition %s' %
                left_value)
            return

        if left_is_variable and right_is_variable:
            # TODO(akesling): Implement definition for two
            # variables relative to each other
            if left_value.is_equivalent_to(right_value):
                return
            raise NotImplementedError(
                'Resolution of variable co-definition is not '
                'yet implemented.')
        elif left_is_variable:
            # NOTE(akesling): This style of assignment hasn't
            # been seen in the signals so far.
            if (left_value.name in variable_lookup
                    and variable_lookup[left_value.name]
                    and variable_lookup[left_value.name] != right_value):
                raise Exception(
                    'Variable "%s" has been defined twice, '
                    'first with value "%s" and second with '
                    'value "%s"' % (
                        left_value.name,
                        variable_lookup[left_value.name],
                        right_value))
            variable_lookup[left_value.name] = right_value
        elif right_is_variable:
            # NOTE(akesling): This style of assignment hasn't
            # been seen in the signals so far.
            if (right_value.name in variable_lookup
                    and variable_lookup[right_is_variable.name]):
                raise Exception(
                    'Variable "%s" has been defined twice, '
                    'first with value "%s" and second with '
                    'value "%s"' % (
                        right_value.name,
                        variable_lookup[right_value.name],
                        left_value))
            variable_lookup[right_value.name] = left_value
        else:
            raise Exception(
                'An unknown error occurred for definition with '
                '"left value" (%s) and "right value" (%s)' % (
                    left_value, right_value))

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
