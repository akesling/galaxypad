#!/usr/bin/env python
import pickle
from PIL import Image
from imgcat import imgcat


SIZE = 320
BIG = 1


def print_image_stack(imvec):
    print("Printing image stack")
    while imvec != []:
        image, imvec = imvec  # type: ignore
        print(image)
        im = Image.new('RGB', [SIZE * BIG, SIZE* BIG])
        maxx, maxy, minx, miny = 0, 0, 0, 0
        while image != []:
            pixel, image = image  # type: ignore
            maxx = max(maxx, pixel[0])
            maxy = max(maxy, pixel[1])
            minx = min(minx, pixel[0])
            miny = min(miny, pixel[1])
            offset = [(p + SIZE // 2) * BIG for p in pixel]
            for x in range(max(offset[0], 0), min(offset[0] + BIG, SIZE * BIG)):
                for y in range(max(offset[1], 0), min(offset[1] + BIG, SIZE * BIG)):
                    im.putpixel([x, y], (255,255,255))
        imgcat(im)
        print(minx, miny, maxx, maxy)
        return  # XXX
    print("Done with image stack")


if __name__ == '__main__':
    imvec = pickle.load(open('images.pkl', 'rb'))
    print_image_stack(imvec)