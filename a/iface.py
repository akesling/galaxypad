#!/usr/bin/python2
from math import sin, cos
from sdl2 import SDL_QUIT, SDL_MOUSEMOTION, SDL_MOUSEWHEEL, SDL_MOUSEBUTTONDOWN
import sdl2.ext as sdl2ext
from sys import stdout
import time

BLACK = sdl2ext.Color(0, 0, 0)
WHITE = sdl2ext.Color(255, 255, 255)

sdl2ext.init()
CanvasWidth = 800
CanvasHeight = 600
win = sdl2ext.Window("PySDL2 test", size=(CanvasWidth, CanvasHeight))
win.show()
winsurf = win.get_surface()

def point(x, y):
    #sdl2ext.fill(winsurf, BLACK)
    pixelview = sdl2ext.PixelView(winsurf)
    #pixelview[event.motion.y][event.motion.x] = WHITE
    
    pixelview[y][x] = WHITE
    del pixelview

# def line(x0, y0, x1, y1):
#     #print "x0:{} y0:{} x1:{} y1:{}".format(x0, y0, x1, y1)
#     """draw a line 
    
#     http://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm"""
#     #sdl2ext.fill(winsurf, BLACK)
#     pixelview = sdl2ext.PixelView(winsurf)
#     #pixelview[event.motion.y][event.motion.x] = WHITE
    
#     # dont draw put of screen
#     # this check should be in "while true" loop but for some reason it 
#     # didn't work there
#     x0 = 0 if x0 < 0 else x0
#     x0 = CanvasWidth -1 if x0 >= CanvasWidth else x0
#     x1 = 0 if x1 < 0 else x1
#     x1 = CanvasWidth -1 if x1 >= CanvasWidth else x1
#     y0 = 0 if y0 < 0 else y0
#     y0 = CanvasHeight -1 if y0 >= CanvasHeight else y0
#     y1 = 0 if y1 < 0 else y1
#     y1 = CanvasHeight -1 if y1 >= CanvasHeight else y1
    
    
#     dx = abs(x1-x0)
#     dy = abs(y1-y0) 
#     sx = 1 if (x0 < x1) else -1
#     sy = 1 if (y0 < y1) else -1
#     err = dx-dy
 
#     while True:
#         pixelview[y0][x0] = WHITE
#         if x0 == x1 and y0 == y1: break
#         e2 = 2*err
#         if e2 > -dy:
#            err = err - dy
#            x0  = x0 + sx
#         if x0 == x1 and y0 == y1: 
#             pixelview[y0][x0] = WHITE
#             break
#         if e2 < dx: 
#             err = err + dx
#             y0  =y0 + sy 
   
#     del pixelview

# def draw_box(CameraPos = {"x": 0, "y": 0, "z": -15}, 
#              CameraRot = {"x": 0, "y": 0, "z": 0}):
#     """Draws a rotating box, CameraRot variable is presistant if nobody
#     outside this function doesn't touch it
    
#     http://www.cores2.com/3D_Tutorial/"""
#     sdl2ext.fill(winsurf, BLACK) #fill screen with black
    
#     # draw a 2D box
#     #box={"x0":100,"y0":100, "x1":200, "y1":200}
#     #line(box["x0"], box["y0"], box["x0"], box["y1"])
#     #line(box["x0"], box["y0"], box["x1"], box["y0"])
#     #line(box["x1"], box["y1"], box["x0"], box["y1"])
#     #line(box["x1"], box["y1"], box["x1"], box["y0"])
    
#     # our 3D model
#     CubeVertex = [
#         {"x":-1, "y":-1, "z":1},
#         {"x":-1, "y":1,  "z":1},
#         {"x":1,  "y":1,  "z":1},
#         {"x":1,  "y":-1, "z":1},
#         {"x":-1, "y":-1, "z":-1},
#         {"x":-1, "y":1,  "z":-1},
#         {"x":1,  "y":1,  "z":-1},
#         {"x":1,  "y":-1, "z":-1},
#     ]
#     CubeEdges = [
#         {"i":0, "j":1},
#         {"i":1, "j":2},
#         {"i":2, "j":3},
#         {"i":3, "j":0},
        
#         {"i":4, "j":5},
#         {"i":5, "j":6},
#         {"i":6, "j":7},
#         {"i":7, "j":4},
        
#         {"i":0, "j":4},
#         {"i":1, "j":5},
#         {"i":2, "j":6},
#         {"i":3, "j":7},
#     ]
    
    
#     #CameraPos = {"x": 0, "y": 0, "z": -10};
#     #CameraRot = {"x": 0, "y": 0, "z": 0};
#     RatioConst = 320
    
#     CenterX = CanvasWidth / 2
#     CenterY = CanvasHeight / 2
    
#     #Rotate camera
#     CameraRot["x"] += 0.02
#     CameraRot["y"] += 0.02
#     CameraRot["z"] += 0.02
    
#     PointList = []
    
#     for ccv in CubeVertex:
#         WorkingVertex = { "x":ccv["x"], "y":ccv["y"], "z":ccv["z"] }
        
#         Temp = WorkingVertex["z"]
#         WorkingVertex["z"] = -WorkingVertex["x"] * sin(CameraRot["y"]) - WorkingVertex["z"] * cos(CameraRot["y"])
#         WorkingVertex["x"] = -WorkingVertex["x"] * cos(CameraRot["y"]) + Temp * sin(CameraRot["y"])
        
#         Temp = WorkingVertex["z"]
#         WorkingVertex["z"] = -WorkingVertex["y"] * sin(CameraRot["x"]) + WorkingVertex["z"] * cos(CameraRot["x"])
#         WorkingVertex["y"] = WorkingVertex["y"] * cos(CameraRot["x"]) + Temp * sin(CameraRot["x"])
        
#         Temp = WorkingVertex["x"]
#         WorkingVertex["x"] = WorkingVertex["x"] * cos(CameraRot["z"]) - WorkingVertex["y"] * sin(CameraRot["z"])
#         WorkingVertex["y"] = WorkingVertex["y"] * cos(CameraRot["z"]) + Temp * sin(CameraRot["z"])
        
#         WorkingVertex["x"] -= CameraPos["x"];
#         WorkingVertex["y"] -= CameraPos["y"];
#         WorkingVertex["z"] -= CameraPos["z"];
        
#         # Convert from x,y,z to x,y
#         # This is called a projection transform
#         # We are projecting from 3D back to 2D
#         ScreenX = (RatioConst * (WorkingVertex["x"])) / WorkingVertex["z"];
#         ScreenY = (RatioConst * (WorkingVertex["y"])) / WorkingVertex["z"];
        
#         # Save this on-screen position to render the line locations
#         PointList.append({"x":int(CenterX + ScreenX), "y":int(CenterY + ScreenY)})
        
#     for cce in CubeEdges:
#         # Find the two points we are working on
#         Point1 = PointList[cce["i"]];
#         Point2 = PointList[cce["j"]];
        
#         # Render the edge by looking up our vertex list
#         line(Point1["x"], Point1["y"], Point2["x"], Point2["y"]);
        


# draw_box() 
point(0, 0)
running = True
lastm=(0,0) #last mouse position
# CameraPos = {"x": 0, "y": 0, "z": -5}
# CameraRot = {"x": 0, "y": 0, "z": 0}
# print("hold down mouse button to move camera")
# print("use scroll wheel to change how far camera is")
while running:
    t = time.time()
    events = sdl2ext.get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
            break
        if event.type == SDL_MOUSEMOTION:
            if event.motion.state == 1:# 1st mouse button is down
                # paint a line
                #line(lastm[0], lastm[1], event.motion.x, event.motion.y)
                
                # change camera pos
                # mouse_sens = 50.0 # mouse sensitivity
                # CameraPos["x"] = (event.motion.x - CanvasHeight / 2)/ mouse_sens
                # CameraPos["y"] = (event.motion.y - CanvasWidth / 2)/ mouse_sens
                lastm=event.motion.x, event.motion.y
                print('motion', event.motion.x, event.motion.y)
            else: #no buttons pressed
                lastm=event.motion.x, event.motion.y
        elif event.type == SDL_MOUSEBUTTONDOWN:
            print('buttondown', event.button.x, event.button.y)
        # elif event.type == SDL_MOUSEWHEEL:
        #     # change how far camera is 
        #     CameraPos["z"] += event.motion.x 
    stdout.flush()
    # draw_box(CameraPos=CameraPos)
    point(0, 0)
    win.refresh()
sdl2ext.quit()
print() # make a empty line