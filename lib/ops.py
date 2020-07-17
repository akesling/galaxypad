import math

def int_to_grid(number):
    bin_string = '{0:b}'.format(abs(number))
    negative = number < 0
    size = int(math.ceil(math.sqrt(len(bin_string))))
    grid = [[0]*(size+1) for i in range(size + 1 + (negative*1))]

    for i in range(len(grid[0])):
        grid[0][i] = 1
    for row in grid:
        row[0] = 1
    grid[0][0] = 0

    for i, char in enumerate(reversed(list(bin_string))):
        row = (i // size) + 1
        col = (i % size) + 1
        grid[row][col] = int(char)

    return grid

def list_to_cons_form(lst):
    if not isinstance(lst, list):
        return lst

    if len(lst) == 0 or lst == [None]:
        return [None]

    if len(lst) == 1:
        return [lst[0], None]

    if len(lst) == 2 and lst[1] is None:
        return lst

    head = lst[0]
    tail = lst[1:]
    if len(tail) == 1 and isinstance(tail[0], list):
        tail = tail[0]
    return [list_to_cons_form(head), list_to_cons_form(tail)]

linear_list_leader = '11'
def list_to_linear(lst):
    if not lst or lst == [None]:
        return '00'

    head = lst[0]
    tail = lst[1:]
    if not tail:
        tail_string = ''
    elif len(tail) == 1:
        tail_string = to_linear(tail[0])
    else:
        tail_string = to_linear(tail)
    linear = linear_list_leader + to_linear(head) + tail_string
    return linear

def to_linear(value):
    linear = {
        type(None): lambda x: '00',
        list: list_to_linear,
        int: lambda x: grid_to_linear(int_to_grid(x)),
        str: lambda x: x,
    }[type(value)](value)
    return linear

def grid_to_int(grid):
    height = len(grid)
    width = len(grid[0])
    is_negative = height > width

    bin_list = []
    for i in range(1, height-(is_negative*1)):
        row = grid[i]
        for value in row[1:]:
            bin_list.append(str(value))

    bin_string = ''.join(reversed(bin_list))
    number = int(bin_string, 2)

    if is_negative:
        return -1 * number
    else:
        return number

def grid_to_linear(grid):
    height = len(grid)
    width = len(grid[0])
    is_int = (
        not bool(grid[0][0])
        and all(grid[0][1:])
        and all((grid[i+1][0] for i in range(len(grid)-1))))

    if is_int:
        number = grid_to_int(grid)
        if number == 0:
            return '010'

        is_negative = height > width
        bin_list = [str(0 + (is_negative*1)), str(1 - (is_negative*1))]

        number_bin_string = '{0:b}'.format(abs(number))

        block_spacing = int(math.ceil(len(number_bin_string)/4))
        bin_list.extend(['1']*block_spacing)
        bin_list.append('0')
        bin_list.extend(['0']*(block_spacing*4 - len(number_bin_string)))
        bin_list.append(number_bin_string)

        return ''.join(bin_list)

    raise NotImplementedError('Grid represents an unknown type: %s' % grid)

def linear_to_list(linear):
    raise NotImplementedError('Linear represents an unknown type: %s' % grid)

def linear_to_int(linear):
    if linear == '010':
        return 0

    is_negative = linear[0] == '1'
    num_bits = 0
    for bit in linear[2:]:
        if bit == '1':
            num_bits = num_bits + 4
        else:
            break
    bin_string = linear[-num_bits:]
    number = int(bin_string, 2)
    if is_negative:
        return -1 * number
    return number

def linear_to_grid(linear):
    is_int = int(linear[0]) != int(linear[1])
    if is_int:
        number = linear_to_int(linear)
        return int_to_grid(number)

    raise NotImplementedError('Linear represents an unknown type: %s' % linear)
