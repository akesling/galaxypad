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
flip = lambda arg1: lambda arg2: lambda arg3: arg1(arg3)(arg2)
b_combinator = lambda arg1: lambda arg2: lambda arg3: arg1(arg2(arg3))
t = lambda arg1: lambda arg2: arg1
false = lambda arg1: lambda arg2: arg2
i_combinator = lambda arg1: arg1
nil = lambda arg1: t
isnil = lambda arg1: t if arg1 == nil else false
pwr2 = lambda arg1: pow(2, arg1)

add = lambda arg1: lambda arg2: arg1 + arg2
mul = lambda arg1: lambda arg2: arg1 * arg2
neg = lambda arg1: arg1 * -1

make_pair = lambda arg1: lambda arg2: [arg1, arg2]
pick_head = lambda arg1: arg1[0]
pick_tail = lambda arg1: arg1[1]

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
    'send': transmit,
    's': substitution,
    'c': flip,
    'b': b_combinator,
    't': t,
    'f': false,
    'i': i_combinator,
    'nil': nil,
    'isnil': isnil,
    'cons': make_pair,
    'car': pick_head,
    'cdr': pick_tail,
    'pwr2': pwr2,
}

# Make sure to preserve the interface between this Interpreter and the ICFP JIT
# in `sidecar`.
class _ICFPTokenInterpreter:
    def __init__(self, tokens: [[str]]):
        self._program = tokens

    def __call__(self, *args):
        return self._run(self._program)

    def _run(
            self, tokens: [[str]], line_offset=0, token_offset=0,
            init_variables=None, init_procedures=None) -> (
                List[List]):
        variables = {}
        if init_variables:
            variables.update(init_variables)

        procedures = {}
        if init_procedures:
            procedures.update(init_procedures)

        line_results = []
        for li, line in enumerate(tokens):
            if len(line) and (line[0] == '#' or line[0] == '...'):
                logger.debug(
                    'Skipping comment or block delimeter on line %s',
                    line_offset+li)
                continue

            definition_index_list = [i for i,x in enumerate(line) if x == '=']
            if (len(line)
                    and line[0].startswith(':')
                    and len(definition_index_list)):
                procedure_name = line[0]
                definition_index = definition_index_list[0]
                procedures[procedure_name] = (
                    Procedure(
                        procedure_name,
                        Expression(line[definition_index+1:]),
                        start=(li+line_offset, definition_index+1),
                        end=(li+line_offset, len(line))))
                continue

            if len(definition_index_list):
                definition_index = definition_index_list[0]
                try:
                    runner = self._run(
                        tokens=[line[:definition_index]],
                        line_offset=li,
                        token_offset=0,
                        init_variables=variables,
                        init_procedures=procedures)
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
                        init_variables=variables,
                        init_procedures=procedures)
                    msg_received = None
                    while True:
                        msg_received = (yield runner.send(msg_received))
                except StopIteration as result:
                    right_value = result.value

                self._define(left_value[0][0], right_value[0][0], variables)
                continue

            stack = []
            instructions = list(reversed(line))
            cursor = 0
            while cursor < len(instructions):
                ti, tkn = cursor, instructions[cursor]
                cursor += 1

                logger.debug(
                    'Executing Line: %s Token (after proc expansion): %s -- %s',
                    line_offset+li, token_offset+ti, tkn)

                try:
                    parsed_token = self._parse(tkn, procedures)
                    if parsed_token == ap:
                        tmp = parsed_token(stack.pop())
                        stack.append(tmp(stack.pop()))
                    elif isinstance(parsed_token, Procedure):
                        instructions = (instructions[:cursor] +
                            list(reversed(parsed_token.expression.tokens)) +
                            instructions[cursor:])
                    else:
                        stack.append(parsed_token)

                except Transmission as t:
                    tx_value = self._serialize(t.value, variables)
                    logger.debug('Transmitting value "%s"', tx_value)

                    received_message = (yield tx_value)

                    logger.debug('Received value "%s"', received_message)
                    # NOTE(akesling): If this is `ap`, it won't be applied
                    value = self._parse(received_message, procedures)
                    continue
                    # TODO(akesling): Figure out what form the received value
                    # should *actually* be.  Is it a set of arbitrary
                    # expressions?  If so, we'll need to manage nested
                    # transmission.
            line_results.append(stack)

        return line_results

    def _parse(self, token, procedure_lookup):
        if token in non_terminals:
            return non_terminals[token]

        if token.startswith('x'):
            return Variable(token)

        if token.startswith(':'):
            return procedure_lookup[token]

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

        if value is t:
            return 't'

        if value is f:
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

class Expression:
    def __init__(self, tokens: [str]):
        self.tokens = tokens

    def __repr__(self):
        return 'Expression<Tokens: %s>' % (self.tokens)

class Procedure:
    def __init__(self,
            name: str,
            expr: Expression,
            start: Tuple[int, int],
            end: Tuple[int, int]):
        self.name = name
        self.expression = expr
        self.start = start
        self.end = end

    def __repr__(self):
        return 'Procedure<Name: %s, Expr: %s>' % (self.name, self.expression)

    def get_span(self):
        return (self.start, self.end)

class Variable:
    # TODO(akesling): Figure out op accumulation
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return 'Variable<Name: %s>' % (self.name)
