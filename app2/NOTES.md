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

eval scratchpad
```python

def tryEval(expr: Expr) -> Tuple[Expr, bool]:
    """ Try to perform a computation, return result and success """
    assert isinstance(expr, (Value, Tree)), expr
    t, f = Value("t"), Value("f")
    if expr.Evaluated:
        return expr.Evaluated, False
    if isinstance(expr, Value) and str(expr) in functions:
        return functions[str(expr)], True
    if isinstance(expr, Tree):
        assert isinstance(expr.left, (Value, Tree)), expr
        assert isinstance(expr.right, (Value, Tree)), expr
        left: Expr = evaluate(expr.left)
        x: Expr = expr.right
        if left == Value("neg"):
            return Value(-evalint(x)), True
        if isinstance(left, Value):
            if str(left) == "i":
                return x, True
            if str(left) == "nil":
                return t, True
            if str(left) == "isnil":
                return Tree(x, Tree(t, Tree(t, f))), True
            if str(left) == "car":
                return Tree(x, t), True
            if str(left) == "cdr":
                return Tree(x, f), True
        if isinstance(left, Tree):
            assert isinstance(left.left, (Value, Tree)), left
            assert isinstance(left.right, (Value, Tree)), left
            left2: Expr = evaluate(left.left)
            y: Expr = left.right
            if isinstance(left2, Value):
                if str(left2) == "t":
                    return y, True
                if str(left2) == "f":
                    return x, True
                if str(left2) == "add":
                    return Value(evalint(x) + evalint(y)), True
                if str(left2) == "mul":
                    return Value(evalint(x) * evalint(y)), True
                if str(left2) == "div":
                    a, b = evalint(y), evalint(x)
                    return Value(a // b if a * b > 0 else (a + (-a % b)) // b), True
                if str(left2) == "lt":
                    return (t, True) if evalint(y) < evalint(x) else (f, True)
                if str(left2) == "eq":
                    return (t, True) if evalint(y) == evalint(x) else (f, True)
                if str(left2) == "cons":
                    return evalCons(y, x), True
            if isinstance(left2, Tree):
                assert isinstance(left2.left, (Value, Tree)), left2
                assert isinstance(left2.right, (Value, Tree)), left2
                left3: Expr = evaluate(left2.left)
                z: Expr = left2.right
                if isinstance(left3, Value):
                    if str(left3) == "s":
                        return Tree(Tree(z, x), Tree(y, x)), True
                    if str(left3) == "c":
                        return Tree(Tree(z, x), y), True
                    if str(left3) == "b":
                        return Tree(z, Tree(y, x)), True
                    if str(left3) == "cons":
                        return Tree(Tree(x, z), y), True
    return expr, False
```