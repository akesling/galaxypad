

def reduce_identity(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce identity function """
    if tree.left == _i and tree.right is not None:
        return tree.right, True
    return tree, False


def reduce_inc(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce increment with integer """
    if tree.left == _inc and isinstance(tree.right, int):
        return tree.right + 1, True
    return tree, False


def reduce_dec(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce decrement with integer """
    if tree.left == _dec and isinstance(tree.right, int):
        return tree.right - 1, True
    return tree, False


def reduce_add_identity(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce additive identity """
    if isinstance(tree.left, Tree) and tree.left.left == _add and tree.right == 0:
        return tree.left.right, True  # type: ignore
    if tree.left == _add and tree.right == 0:
        return _i, True
    return tree, False


def reduce_add(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce addition with integers """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _add
        and isinstance(tree.left.right, int)
        and isinstance(tree.right, int)
    ):
        return tree.left.right + tree.right, True
    return tree, False


def reduce_mul_identity(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce multiplicative identity """
    if isinstance(tree.left, Tree) and tree.left.left == _mul and tree.right == 1:
        return tree.left.right, True  # type: ignore
    if tree.left == _mul and tree.right == 1:
        return _i, True
    return tree, False


def reduce_mul(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce multiplication with integers """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _mul
        and isinstance(tree.left.right, int)
        and isinstance(tree.right, int)
    ):
        return tree.left.right * tree.right, True
    return tree, False


def reduce_div_identity(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce division identity """
    if isinstance(tree.left, Tree) and tree.left.left == _div and tree.right == 1:
        return tree.left.right, True  # type: ignore
    return tree, False


def reduce_div(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce division with integers """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _div
        and isinstance(tree.left.right, int)
        and isinstance(tree.right, int)
    ):
        x = tree.left.right
        y = tree.right
        return (x + (-x % y)) // y, True
    return tree, False


def reduce_eq(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce equality check """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _eq
        and tree.left.right is not None
        and tree.right is not None
    ):
        if type(tree.left.right) == type(tree.right) and tree.left.right == tree.right:
            return _t, True
        else:
            return _f, True
    return tree, False


def reduce_t(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce true check """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _t
        and tree.left.right is not None
        and tree.right is not None
    ):
        return tree.left.right, True
    return tree, False


def reduce_f_identity(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce false to identity """
    if tree.left == _f and tree.right is not None:
        return _i, True
    return tree, False


def reduce_f(tree) -> Tuple[TreeOrLeaf, bool]:
    """ Reduce false check """
    if (
        isinstance(tree.left, Tree)
        and tree.left.left == _f
        and tree.left.right is not None
        and tree.right is not None
    ):
        return tree.right, True
    return tree, False


REDUCTIONS = [
    reduce_identity,
    reduce_inc,
    reduce_dec,
    reduce_add_identity,
    reduce_add,
    reduce_mul_identity,
    reduce_mul,
    reduce_div_identity,
    reduce_div,
    reduce_eq,
    reduce_t,
    reduce_f_identity,
    reduce_f,
]
