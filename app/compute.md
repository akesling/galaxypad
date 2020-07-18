# `compute.py` - Tree-based Pattern Matching

After failing to figure out how to un-vector curried `cons` in the interpreter,
I decided to build a different method of evaluating code.

`compute.py` is a simple interpreter that uses tree-matching rules to evaluate.

## Rewriting Logic

The core logic is all in the `REWRITES` list:
```
REWRITES = (
    [
        Rewrite.from_str(s)
        for s in [
            "ap i x0 = x0",  # Identity
            "ap add 0 = i",  # Addition -> Identity
            "ap add 1 = inc",  # Addition -> Increment
...
        Rewrite.from_str(s, unop(fn))
        for s, fn in [
            ("ap inc x0 = x1", lambda x: x + 1),  # Increment
...
        Rewrite.from_str(s, binop(fn))
        for s, fn in [
            ("ap ap add x0 x1 = x2", lambda x, y: x + y),  # Addition
```

These are defined with the same syntax as the language, and take an optional method.

These methods can do a bunch of things:
    * Validate the internal data for whether or not the pattern is really a match
    * Type check the arguments and only validate if types are correct
    * Launch side effects

The `send` method is implemented with a side effect to talk to the server:
```
    Rewrite.from_str("ap send x0 = x1", send)
```

## Tests and tests and tests

I copied a bunch of the extracted examples from the images over into a tests file.

Check it out if you want to see all of the things it can and can't do.

## Current limitations

The biggest issue presently, is we assume the rewrite rules are convergent.

**The Fundamental Assumption:** is that we can repeatedly apply all the rewrite rules,
until there are no more changes to make.


**This assumption is wrong in the general case.**
I had to leave out commutative rules, etc.  Some of the missing patterns:
```
# Basic commutative addition/Multiplication is missing as a step
ap ap add x0 x1   =   ap ap add x1 x0
ap ap mul x0 x1   =   ap ap mul x1 x0

# Require commutative transform then -> convert to inc -> then annihilate w/ dec
ap dec ap ap add x0 1   =   x0

# This has the potential to explode the tree, Not sure what to do with it
f   =   ap s t

# Fairly complex inversion of the car op
ap car x2   =   ap x2 t

# Similar inversion of the cdr op
ap cdr x2   =   ap x2 f
```

## What's next, if you want to play with it

The simplest thing would be to test it against the interpreter and check that it works / does the same thing on the same inputs.

Parsing the `galaxy.txt` file line-by-line and then seeing how the tree-replacement strategy does might be useful.

Adding the missing functions via rewrite rules and a new datatype for draw might be cool too.

## Tinkering

Run `python app/compute.py 'ap ap add 1 2'` to evaluate a string.

Run `python app/compute.py 'ap ap add ap ap add 2 3 4'` to evaluate a bigger example.

Run `python app/compute.py 'ap send 0'` to try sending to the server

Run `python app/compute.py 'ap send ap ap cons 0 nil'` to try sending to the server