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

    for i, char in enumerate(bin_string):
        row = (i // size) + 1
        col = (i % size) + 1
        grid[row][col] = int(char)

    return grid
