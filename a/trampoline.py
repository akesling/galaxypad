def trampoline(f, *args):
    v = f(*args)
    while callable(v):
        v = v()
    return v


def fact(n):
    if n == 0:
        return 1
    return fact(n - 1) * n


def fact_thunked(n, cont):
    if n == 0:
        return cont(1)
    else:
        return lambda: fact_thunked(n - 1, lambda value: lambda: cont(n * value))


def is_even(n):
    if n == 0:
        return True
    return is_odd(n - 1)


def is_odd(n):
    if n == 0:
        return False
    return is_even(n - 1)


def is_even_thunked(n, cont):
    if n == 0:
        return cont(True)
    return lambda: is_odd_thunked(n - 1, cont)


def is_odd_thunked(n, cont):
    if n == 0:
        return cont(False)
    return lambda: is_even_thunked(n - 1, cont)


MEMO = {}


def fib(n):
    if n < 2:
        return 1
    if n in MEMO:
        return MEMO[n]
    a = fib(n - 1)
    b = fib(n - 2)
    v = a + b
    MEMO[n] = v
    return v


def fib_thunked(n, cont):
    if n < 2:
        return cont(1)
    if n in MEMO:
        return cont(MEMO[n])

    def f1():
        def f1v(a):
            def f2():
                def f2v(b):
                    v = a + b
                    MEMO[n] = v
                    return cont(v)

                return fib_thunked(n - 2, f2v)

            return f2

        return fib_thunked(n - 1, f1v)

    return f1


# print(fib(10000))  # Explodes stack
# print(trampoline(lambda: fib_thunked(100000, lambda x: x)))


def evaluate(tree):
    if isinstance(tree, int):
        return tree
    op, left, right = tree
    if op == "+":
        return evaluate(left) + evaluate(right)
    elif op == "-":
        return evaluate(left) - evaluate(right)
    raise ValueError(f"bad tree {tree}")


def evaluate_thunked(tree, cont):
    if isinstance(tree, int):
        return cont(tree)
    op, left, right = tree

    def f1():
        def f1v(v1):
            def f2():
                def f2v(v2):
                    if op == "+":
                        return cont(v1 + v2)
                    elif op == "-":
                        return cont(v1 - v2)
                    raise ValueError(f"bad tree {tree}")

                return evaluate_thunked(right, f2v)

            return f2

        return evaluate_thunked(left, f1v)

    return f1


# big_tree = ('+', 1, 1)
# for i in range(10000):
#     left = big_tree
#     right = big_tree if i % 1000 == 0 else 1
#     big_tree = ('+', left, right)
# # print(evaluate(big_tree)) # Raises RecursionError
# print(trampoline(evaluate_thunked(big_tree, lambda x: x)))


from dataclasses import dataclass
from typing import Union


# @dataclass
# class Tree:
#     left: Union["Tree", str, int, None] = None
#     right: Union["Tree", str, int, None] = None
#     value: Union[int, None] = None


# def evaluate_tree(tree):
#     if isinstance(tree, int):
#         return tree
#     if isinstance(tree, Tree):
#         if tree.value is not None:
#             return tree.value
#         left = tree.left
#         if isinstance(left, Tree):
#             op = left.left
#             x = evaluate_tree(left.right)
#             y = evaluate_tree(tree.right)
#             if op == '+':
#                 z = x + y
#             else:
#                 raise ValueError(f"bad op {op}")
#             tree.value = z
#             return z
#     raise ValueError(f"bad tree {tree}")


# def evaluate_tree_thunked(tree, cont):
#     if isinstance(tree, int):
#         return cont(tree) # tree
#     if isinstance(tree, Tree):
#         if tree.value is not None:
#             return cont(tree.value)
#         left = tree.left
#         if isinstance(left, Tree):
#             op = left.left
#             # Start continuation block
#             def f1():
#                 def f1v(v1):
#                     def f2():
#                         def f2v(v2):
#                             x = v1  # evaluate_tree(left.right)
#                             y = v2  # evaluate_tree(tree.right)
#                             if op == '+':
#                                 z = x + y
#                             else:
#                                 raise ValueError(f"bad op {op}")
#                             tree.value = z
#                             return cont(z)
#                         return evaluate_tree_thunked(left.right, f2v)
#                     return f2
#                 return evaluate_tree_thunked(tree.right, f1v)
#             return f1
#             # Done continuation block
#     raise ValueError(f"bad tree {tree}")


# big_tree = Tree(Tree('+', 1), 1)
# for i in range(1000):
#     big_tree = Tree(Tree('+', big_tree), big_tree)
# # print(evaluate_tree(big_tree)) # Raises RecursionError
# print(trampoline(evaluate_tree_thunked(big_tree, lambda x: x)))


@dataclass
class Tree:
    left: Union["Tree", str, int, None] = None
    right: Union["Tree", str, int, None] = None
    value: Union[int, None] = None


# def evaluate_tree(tree):
#     if isinstance(tree, int):
#         return tree
#     if isinstance(tree, Tree):
#         if tree.value is not None:
#             return tree.value
#         x = evaluate_tree(tree.right)
#         left = tree.left
#         if left == 'inc':
#             value = x + 1
#         elif isinstance(left, Tree):
#             y = evaluate_tree(left.right)
#             left2 = left.left
#             if left2 == '+':
#                 value = y + x
#             else:
#                 raise ValueError(f"bad left2 {left2}")
#         else:
#             raise ValueError(f"bad left {left}")
#         tree.value = value
#         return value
#     raise ValueError(f"bad tree {tree}")


def evaluate_tree(tree):
    if isinstance(tree, int):
        return tree
    if isinstance(tree, Tree):
        if tree.value is not None:
            return tree.value
        x = evaluate_tree(tree.right)
        left = tree.left
        if left == "inc":
            value = x + 1
        elif isinstance(left, Tree):
            y = evaluate_tree(left.right)
            left2 = left.left
            if left2 == "+":
                value = y + x
            else:
                raise ValueError(f"bad left2 {left2}")
            tree.value = value
            return value
        else:
            raise ValueError(f"bad left {left}")
        tree.value = value
        return value
    raise ValueError(f"bad tree {tree}")


# Show these side-by-side with monaco diff?


def evaluate_tree_thunked(tree, cont):
    if isinstance(tree, int):
        return cont(tree)
    if isinstance(tree, Tree):
        if tree.value is not None:
            return cont(tree.value)

        def fx(x):
            left = tree.left
            if left == "inc":
                value = x + 1
            elif isinstance(left, Tree):

                def fy(y):
                    left2 = left.left
                    if left2 == "+":
                        value = y + x
                    else:
                        raise ValueError(f"bad left2 {left2}")
                    tree.value = value
                    return cont(value)

                return lambda: evaluate_tree_thunked(left.right, fy)
            else:
                raise ValueError(f"bad left {left}")
            tree.value = value
            return cont(value)

        return lambda: evaluate_tree_thunked(tree.right, fx)
    raise ValueError(f"bad tree {tree}")


# one = Tree("inc", 0)
# big_tree = Tree(Tree("+", one), one)
# for i in range(1000):
#     big_tree = Tree(Tree("+", big_tree), big_tree)
# # print(evaluate_tree(big_tree)) # Raises RecursionError
# print(trampoline(evaluate_tree_thunked(big_tree, lambda x: x)))

monaco_js = '''
var originalModel = monaco.editor.createModel("\ndef evaluate_tree(tree, cont):\n    if isinstance(tree, int):\n        return tree\n    if isinstance(tree, Tree):\n        if tree.value is not None:\n            return tree.value\n        x = evaluate_tree(tree.right)\n        left = tree.left\n        if left == \"inc\":\n            value = x + 1\n        elif isinstance(left, Tree):\n            y = evaluate_tree(left.right)\n            left2 = left.left\n            if left2 == \"+\":\n                value = y + x\n            else:\n                raise ValueError(f\"bad left2 {left2}\")\n            tree.value = value\n            return value\n        else:\n            raise ValueError(f\"bad left {left}\")\n        tree.value = value\n        return value\n    raise ValueError(f\"bad tree {tree}\")\n", "text/plain");
var modifiedModel = monaco.editor.createModel("\ndef evaluate_tree_thunked(tree, cont):\n    if isinstance(tree, int):\n        return cont(tree)\n    if isinstance(tree, Tree):\n        if tree.value is not None:\n            return cont(tree.value)\n\n        def fx(x):\n            left = tree.left\n            if left == \"inc\":\n                value = x + 1\n            elif isinstance(left, Tree):\n\n                def fy(y):\n                    left2 = left.left\n                    if left2 == \"+\":\n                        value = y + x\n                    else:\n                        raise ValueError(f\"bad left2 {left2}\")\n                    tree.value = value\n                    return cont(value)\n\n                return lambda: evaluate_tree_thunked(left.right, fy)\n            else:\n                raise ValueError(f\"bad left {left}\")\n            tree.value = value\n            return cont(value)\n\n        return lambda: evaluate_tree_thunked(tree.right, fx)\n    raise ValueError(f\"bad tree {tree}\")\n");

var diffEditor = monaco.editor.createDiffEditor(document.getElementById("container"));
diffEditor.setModel({
	original: originalModel,
	modified: modifiedModel
});

'''



def evaluate(tree_or_value):
    if isinstance(tree_or_value, int):
        return tree_or_value
    if isinstance(tree_or_value, Tree):
        value = evaluate_tree(tree_or_value)
        tree_or_value.value = value
        return value
    raise ValueError(f"bad tree_or_value {tree_or_value}")


def evaluate_tree(tree):
    if tree.value is not None:
        return tree.value
    x = evaluate(tree.right)
    left = tree.left
    if left == "inc":
        return x + 1
    elif isinstance(left, Tree):
        y = evaluate(left.right)
        left2 = left.left
        if left2 == "+":
            return y + x
        raise ValueError(f"bad left2 {left2}")
    raise ValueError(f"bad left {left}")


def evaluate_c(tree_or_value, cont):
    if isinstance(tree_or_value, int):
        return cont(tree_or_value)
    if isinstance(tree_or_value, Tree):
        def fv(value):
            tree_or_value.value = value
            return cont(value)
        return lambda: evaluate_tree_c(tree_or_value, fv)
    raise ValueError(f"bad tree_or_value {tree_or_value}")


def evaluate_tree_c(tree, cont):
    if tree.value is not None:
        return cont(tree.value)

    def fx(x):
        left = tree.left
        if left == "inc":
            return cont(x + 1)
        elif isinstance(left, Tree):
            def fy(y):
                y = evaluate(left.right)
                left2 = left.left
                if left2 == "+":
                    return cont(y + x)
                raise ValueError(f"bad left2 {left2}")
            return lambda: evaluate_c(left.right, fy)
        raise ValueError(f"bad left {left}")
    return lambda: evaluate_c(tree.right, fx)



one = Tree("inc", 0)
big_tree = Tree(Tree("+", one), one)
for i in range(10000):
    big_tree = Tree(Tree("+", big_tree), big_tree)
# print(evaluate(big_tree)) # Raises RecursionError
print(trampoline(evaluate_c(big_tree, lambda x: x)))
