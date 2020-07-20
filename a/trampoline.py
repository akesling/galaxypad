def trampoline(v):
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
print(trampoline(lambda: fib_thunked(100000, lambda x: x)))