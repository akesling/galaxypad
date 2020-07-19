#!/usr/bin/env python

procedures = {}  # Map from procedure -> token list
counts = {}  # Map from procedure -> (ap_count, other_count)


for line in open('galaxy.txt').readlines():
    split = line.strip().split()
    procedure, expression = split[0], split[2:]
    assert split[1] == '='
    procedures[procedure] = expression
    assert expression.count('ap') * 2 + 1 == len(expression), procedure