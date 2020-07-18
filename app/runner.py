#!/usr/bin/env python

import re


LINE_REGEX = re.compile(r"(galaxy|:\d+)\s*=\s*(.*)")


def compute_partial(tokens):
    ''' do a single step of reduction, if possible '''
    # Scan for a match-able sub sequence
    for i in range(len(tokens) - 1, -1, -1):
        tok = tokens[i]
        if tokens[]
        if tok == 'cons' and 



class Runner:
    def __init__(self):
        self.lines = []
        self.memory = {}  # map operator -> value

    def run_line(self, line):
        match = LINE_REGEX.match(line)
        assert match is not None, f'bad line {line}'
        operator, code_string = match.groups()
        self.memory[operator] = 

    @property
    def galaxy(self):
        return self.memory['galaxy']

    def evaluate(self, operator):
        pass


if __name__ == '__main__':
    runner = Runner()
    lines = open('galaxy.txt').readlines()
    for line in lines:
        runner.run_line(line)

    compute_partial('ap ap cons 4 ap ap cons 42144 nil'.split())
    