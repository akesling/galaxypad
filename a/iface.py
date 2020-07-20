#!/usr/bin/python2
import sdl2.ext
from random import randint

BLACK = sdl2.ext.Color(0, 0, 0)

sdl2.ext.init()
SIZE = 512
win = sdl2.ext.Window("Galaxy", size=(SIZE, SIZE))
win.show()
winsurf = win.get_surface()
sdl2.ext.fill(winsurf, BLACK)
running = True

pixelview = sdl2.ext.PixelView(winsurf)
while running:
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