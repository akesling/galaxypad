import math

def int_to_grid(number):
    bin_string = '{0:b}'.format(abs(number))
    negative = number < 0
    size = math.ceil(math.sqrt(len(bin_string)))
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
        is_negative = height > width
        bin_list = [str(0 + (is_negative*1)), str(1 - (is_negative*1))]

        number = grid_to_int(grid)
        number_bin_string = '{0:b}'.format(abs(number))

        block_spacing = math.ceil(len(number_bin_string)/4)
        bin_list.extend(['1']*block_spacing)
        bin_list.append('0')
        bin_list.extend(['0']*(block_spacing*4 - len(number_bin_string)))
        bin_list.append(number_bin_string)

        return ''.join(bin_list)

    raise NotImplementedError('Grid represents an unknown type: %s' % grid)

