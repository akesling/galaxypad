#!/usr/bin/python2
from math import sin, cos
# from sdl2 import SDL_QUIT, SDL_MOUSEMOTION, SDL_MOUSEWHEEL, SDL_MOUSEBUTTONDOWN
import sdl2.ext
import time
from random import randint

BLACK = sdl2.ext.Color(0, 0, 0)
WHITE = sdl2.ext.Color(255, 255, 255)

sdl2.ext.init()
SIZE = 512
win = sdl2.ext.Window("PySDL2 test", size=(SIZE, SIZE))
win.show()
winsurf = win.get_surface()
sdl2.ext.fill(winsurf, BLACK)
running = True

pixelview = sdl2.ext.PixelView(winsurf)
while running:
    t = time.time()
    events = sdl2.ext.get_events()
    for event in events:
        if event.type == sdl2.SDL_QUIT:
            running = False
            break
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            print('click', event.button.x, event.button.y)
            sdl2.ext.fill(winsurf, BLACK)
            color = sdl2.ext.Color(randint(128, 255), randint(128, 255), randint(128, 255))
            for _ in range(10000):
                 pixelview[randint(0, SIZE - 1)][randint(0, SIZE - 1)] = color
    win.refresh()
sdl2.ext.quit()