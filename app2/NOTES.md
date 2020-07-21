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

