#!/usr/bin/env python

from PIL import Image
from imgcat import imgcat


SIZE = 512
BIG = 1


def print_image_stack(imvec):
    print("Printing image stack")
    while imvec != []:
        image, imvec = imvec  # type: ignore
        print(image)
        im = Image.new('RGB', [SIZE * BIG, SIZE* BIG])
        while image != []:
            pixel, image = image  # type: ignore
            offset = [(p + SIZE // 2) * BIG for p in pixel]
            for x in range(max(offset[0], 0), min(offset[0] + BIG, SIZE * BIG)):
                for y in range(max(offset[1], 0), min(offset[1] + BIG, SIZE * BIG)):
                    im.putpixel([x, y], (255,255,255))
        imgcat(im)
    print("Done with image stack")

images = [
    [
        [8, 10],
        [
            [8, 9],
            [
                [8, 8],
                [
                    [8, 7],
                    [
                        [8, 6],
                        [
                            [8, 5],
                            [
                                [8, 4],
                                [
                                    [8, 3],
                                    [
                                        [8, 2],
                                        [
                                            [8, 1],
                                            [
                                                [8, 0],
                                                [
                                                    [8, -1],
                                                    [
                                                        [8, -2],
                                                        [
                                                            [8, -3],
                                                            [
                                                                [8, -4],
                                                                [
                                                                    [8, -5],
                                                                    [
                                                                        [16, 4],
                                                                        [
                                                                            [15, 4],
                                                                            [
                                                                                [14, 4],
                                                                                [
                                                                                    [
                                                                                        13,
                                                                                        4,
                                                                                    ],
                                                                                    [
                                                                                        [
                                                                                            12,
                                                                                            4,
                                                                                        ],
                                                                                        [
                                                                                            [
                                                                                                11,
                                                                                                4,
                                                                                            ],
                                                                                            [
                                                                                                [
                                                                                                    10,
                                                                                                    4,
                                                                                                ],
                                                                                                [
                                                                                                    [
                                                                                                        9,
                                                                                                        4,
                                                                                                    ],
                                                                                                    [
                                                                                                        [
                                                                                                            8,
                                                                                                            4,
                                                                                                        ],
                                                                                                        [
                                                                                                            [
                                                                                                                7,
                                                                                                                4,
                                                                                                            ],
                                                                                                            [
                                                                                                                [
                                                                                                                    6,
                                                                                                                    4,
                                                                                                                ],
                                                                                                                [
                                                                                                                    [
                                                                                                                        5,
                                                                                                                        4,
                                                                                                                    ],
                                                                                                                    [
                                                                                                                        [
                                                                                                                            4,
                                                                                                                            4,
                                                                                                                        ],
                                                                                                                        [
                                                                                                                            [
                                                                                                                                3,
                                                                                                                                4,
                                                                                                                            ],
                                                                                                                            [
                                                                                                                                [
                                                                                                                                    2,
                                                                                                                                    4,
                                                                                                                                ],
                                                                                                                                [
                                                                                                                                    [
                                                                                                                                        1,
                                                                                                                                        4,
                                                                                                                                    ],
                                                                                                                                    [],
                                                                                                                                ],
                                                                                                                            ],
                                                                                                                        ],
                                                                                                                    ],
                                                                                                                ],
                                                                                                            ],
                                                                                                        ],
                                                                                                    ],
                                                                                                ],
                                                                                            ],
                                                                                        ],
                                                                                    ],
                                                                                ],
                                                                            ],
                                                                        ],
                                                                    ],
                                                                ],
                                                            ],
                                                        ],
                                                    ],
                                                ],
                                            ],
                                        ],
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ],
    ],
    [],
]

if __name__ == '__main__':
    print_image_stack(images)