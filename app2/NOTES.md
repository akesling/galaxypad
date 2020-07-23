# Notes

- All python files are executable
- All tests runs w/ unittest main
- All module files function as some sort of script / program

Rough breakdown:

* expr.py - Owns the expression types and parsing to/from strings
* modulate.py - Owns the modulation type and convertion to/from modulation
* evaluate.py - Owns the core computation / tree reduction: evaluate()
* vectorize.py - Owns the conversions to/from the Vector type
    * **NOTE** This type is difficult for python, use sparingly. Probably most useful for headless AI
* galaxy.py - Owns processing the `galaxy.txt` file and running it headless
* interface.py - Owns the graphical user interface, which handles rendering images and clicks


UI Wish list:
- Cursor always visible / moves with the mouse (maybe implement with alpha mask, and save old location to restore when moving)
- Better colors (monokai pro?)

CODE Wish list
- parse_tokens and unparse_tokens (generator compatible)


Write up blog post:
- recursive vs non recursive functions


Trampolines
https://eli.thegreenplace.net/2017/on-recursion-continuations-and-trampolines/
hat tip alex kesling

```python
def trampoline(f, *args):
    v = f(*args)
    while callable(v):
        v = v()
    return v
```

```python
def my_func(..., cont: Callable[[], Callable]):
    ...
    # Maybe call cont(result) if base case
    ...
    def f1():
        def f1v(v1):
            def f2():
                def f2v(v2):
                    ...
                    # Use v1 as if it were
                    # v1 = my_func(..., cont) below
                    # v2 = my_func(..., cont) below
                    ...
                    return cont(...)  # needs some base case
                    ...
                return my_func(..., f2v)  # this sets up v2
            return f2
        return my_func(..., f1v)  # this sets up v1
    return f1
```

```python
# Called like
trampoline(my_func, ..., lambda x: x)
```



Rewrite rules
```python
'''
:# -> function replacement

ap i x -> x
ap nil x -> t
ap isnil x -> ap x ap t ap t f
ap car x -> ap x t
ap cdr x -> ap x f

ap ap t y x -> y
ap ap f y x -> x
ap ap add y x -> int(y) + int(x)
ap ap mul y x -> int(y) * int(x)
ap ap div y x -> int(y) / int(x) # see python division towards zero
ap ap lt y x -> t if int(y) < int(x) else f
ap ap eq y x -> t if int(y) == int(x) else f
ap ap cons y x -> eval(ap ap cons eval(y) eval(x))  # special evals

ap ap ap s z y x -> ap ap z x ap y x
ap ap ap c z y x -> ap ap z x y
ap ap ap b z y x -> ap z ap y x
ap ap ap cons z y x -> ap ap x z y
'''


REWRITES = [
    (Tree(i, x), x)
    (Tree(Tree(f, y), x), x)
    (Tree(Tree(Tree(cons, z), y), x), Tree(Tree(x, z), y))
]
PATTERN_NAMES = ('x', 'y', 'z')

match() puts Exprs in under placeholder name, like 'x' 'y' 'z' etc


def match(pattern: Expr, expr: Expr, matches: Dict[str: Expr]) -> bool:
    """ Return true if data matches pattern, also fills out placedict dict """
    if isinstance(pattern, Value) and pattern.name in PATTERN_NAMES:
        matches[pattern.name] = expr
        return True
    if isinstance(pattern, Value) and isinstance(expr, Value):
        return pattern == expr
    if isinstance(pattern, Tree) and isinstance(expr, Tree):
        return (match(pattern.left, expr.left, placedict) and 
            match(pattern.right, expr.right, placedict))
    return False


def apply(replace: Expr, matches: Dict[str: Expr]) -> expr:
    """ Apply the replacement to this tree and return result """
    if isinstance(replace, Value):
        if replace.name in PATTERN_NAMES:
            return matches[replace.name]
        return replace
    if isinstance(replace, Tree):
        return Tree(apply(replace.left, matches), apply(replace.right, matches))
    raise ValueError(f"invalid replace {result},{expr},{matches}")


def insert(old: Expr, new: Expr) -> Expr:
    for parent in old.parents:
        if parent.left is old:
            parent.left = new
        if parent.right is old:
            parent.right = new
        new.parents.append(parent)
    return new


def try_evaluate(expr, rewrites) -> Expr:
    if isinstance(expr, Value) and expr.name in functions:
        return insert(expr, functions[expr.name])
    for pattern, replace in REWRITES:
        matches = {}
        if match(pattern, expr, matches):
            return insert(expr, apply(replace, matches))
    return expr



```

basic algorithm
```python
def try_evaluate(root):
    expr = root
    while True:
        success = False  # Modified this iteration
        # try current node
        # ... individual replacements
        # f y x -> x
        if expr.left.left == f:
            success = True
            # need to correctly handle root/leaves
            # and also maybe just make a re-writer for this
            expr.parent.left = expr.right
        # ...
        if success:  # Jump up 3 since that might have changed eval
            # Maybe make parent = self for the root instead of None?
            # Would make this work
            expr = expr.parent.parent.parent
        else:
            expr = next_in_NLR_order(expr)
            if expr.parents == []:
                break  # done with NLR order, jumped off root

    # in evaluate(), check that try_evaluate(e) == e for convergence?
    # check how many times it takes, predict only one
    return expr
```

Notes on parents:
- expressions can have multiple parents due to s-combinator
- need to correctly update _all_ parents when child updates
- maybe ignore the "back 3" idea and just catch in the next pass

FIRST
- try naively just breaking out of the evaluation when ANY update is made
- other speedups are just minor optimizations from this base case
- benchmark and count e.g how many reprocessings happen, how much time they take on average
