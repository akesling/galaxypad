import math

def int_to_grid(number):
    bin_string = "{0:b}".format(abs(number))
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
        print(row)
        for value in row[1:]:
            bin_list.append(str(value))

    print(bin_list)
    bin_string = ''.join(reversed(bin_list))
    print(bin_string)
    number = int(bin_string, 2)
    print(number)

    if is_negative:
        return -1 * number
    else:
        return number
