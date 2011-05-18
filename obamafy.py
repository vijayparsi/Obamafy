#!/usr/bin/env python2

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import math

from sys import exit, stderr
from argparse import ArgumentParser

from PIL import Image, ImageEnhance, ImageOps, ImageColor, ImageFilter

import numpy


WHITE     = ImageColor.getrgb('#fce4a8')
RED       = ImageColor.getrgb('#d71a20')
DARK_BLUE = ImageColor.getrgb('#00314c')
BLUE      = ImageColor.getrgb('#70969f')

def fatal(msg=''):
    stderr.write(msg)
    exit(1)

def luminance(rgb):
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]

    return math.sqrt(0.241 * (r ** 2) + 0.691 * (g ** 2) + 0.068 * (b ** 2) )

def interpolate(src, dst, base, color):
    a = math.sqrt((color - base) / (luminance(dst) - luminance(src)))

    return tuple(map(lambda (x, y): min(255, int(x + a * (y - x))),
                     zip(src, dst)))

def distance(a, b):
    return abs(a - b) / 255.0

def make_color_table(image, config):
    colors = map(lambda x: x[1],
                 sorted(image.getcolors(),
                        key=lambda (count, color): color))

    table = {}
    state = 'darkest'

    dark_blue = None
    red       = None
    blue      = None

    for color in colors:
        if state == 'darkest':
            dark_blue    = color
            table[color] = DARK_BLUE
            state = 'dark-blue'
        elif state == 'dark-blue':
            if distance(color, dark_blue) < config.dark_blue:
                table[color] = DARK_BLUE
            else:
                table[color] = RED
                red          = color
                state        = 'red'
        elif state == 'red':
            if distance(color, red) < config.red:
                table[color] = RED
            else:
                table[color] = BLUE
                blue         = color
                state        = 'blue'
        else:                   # state == 'blue'
            table[color] = interpolate(BLUE, WHITE, blue, color)

    return table

def get_out_path(path, out_path):
    if out_path != out_path:
        return out_path

    dir, basename  = os.path.split(path)

    components = basename.split(os.path.extsep)

    name = ''.join(components[:-1])
    out_basename = name + '_obamafied' + os.path.extsep + 'png'

    return os.path.join(dir, out_basename)

def enhance(image, enhancer, *args, **kwargs):
    instance = enhancer(image)
    return instance.enhance(*args, **kwargs)

def obamafy(path, out_path, config):
    image = Image.open(path)

    image = ImageOps.posterize(image, config.posterization)
    image = image.filter(ImageFilter.MedianFilter(size=config.median))
    image = ImageOps.grayscale(image)

    color_table = make_color_table(image, config)

    image_array = numpy.array(image)

    transform = numpy.vectorize(lambda c: color_table[c],
                                otypes=[numpy.uint8, numpy.uint8, numpy.uint8])

    image_array = numpy.dstack(transform(image_array))

    obamified = Image.fromarray(image_array)
    obamified.save(get_out_path(path, out_path))

def path(string):
    if not os.path.exists(string):
        raise ValueError('Path "%s" does not exist' % string)

    return string

def even(str):
    n = int(str)

    if n % 2 == 0:
        n += 1

    return n

def main():
    parser = ArgumentParser(description='Obamafy your photo')

    parser.add_argument('input',  type=path, help='a photo to Obamafy')
    parser.add_argument('output', type=str, nargs='?', default=None,
                        help='resulting photo')

    parser.add_argument('--posterization',
                        type=int, default=3, dest='posterization',
                        help='posterize to specified number of bits per color')
    parser.add_argument('--dark-blue',
                        type=float, default=0.15, dest='dark_blue',
                        help='dark-blue color threshold')
    parser.add_argument('--red', type=float, default=0.5, dest='red',
                        help='red color threshold')
    parser.add_argument('--median', type=even, default=5, dest='median',
                        help='median filter size')

    args = parser.parse_args()


    obamafy(args.input, args.output, args)

if __name__ == '__main__':
    main()
