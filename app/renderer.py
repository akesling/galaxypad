from typing import NamedTuple, Tuple, List

import numpy as np

class DrawState(NamedTuple):
    """ Type for pixel state of an image """
    pixel_array: np.array

def checkerboard(size: Tuple[int, int]) -> DrawState:
    checkerboard = np.ones(size)
    checkerboard[1::2,::2] = 0
    checkerboard[::2,1::2] = 0
    return DrawState(checkerboard.T)

def draw(indices: List[Tuple[int, int]]) -> DrawState:
    points = np.array(indices)
    bounds = tuple(np.amax(points, 0) + 1)
    pixels = np.zeros(bounds)
    pixels[points[:, 0], points[:, 1]] = 1
    return DrawState(pixels.T)

def multidraw(glyphs: List[List[Tuple[int, int]]]) -> List[DrawState]:
    images = []
    for indices in glyphs:
        images.append(draw(indices))
    return images
