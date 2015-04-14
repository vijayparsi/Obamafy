#!/usr/bin/env python3

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
import operator

from sys import exit, stderr
from argparse import ArgumentParser

from PIL import Image, ImageEnhance, ImageOps, ImageColor, ImageFilter

import numpy
from functools import reduce


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

    return tuple([min(255, int(x_y[0] + a * (x_y[1] - x_y[0]))) for x_y in zip(src, dst)])

def distance(a, b):
    return abs(a - b) / 255.0

def make_color_table(image, config):
    colors = sorted(image.getcolors(), key=lambda count_color: count_color[1])

    table = {}
    state = 'darkest'

    blue      = None

    area    = 0
    residue = 0
    overall_area = reduce(operator.add, [x[0] for x in colors])

    percents = {}

    for count, color in colors:
        percent = 100 * (area / float(overall_area))

        if state == 'darkest':
            dark_blue    = color
            table[color] = DARK_BLUE
            state = 'dark-blue'
        elif state == 'dark-blue':
            if percent < config.dark_blue:
                table[color] = DARK_BLUE
            else:
                table[color] = RED
                state        = 'red'

                percents['dark-blue'] = percent

                area   *= (percent - config.dark_blue) / 100.0
                residue = percent - config.dark_blue
        elif state == 'red':
            if percent < config.red:
                table[color] = RED
            else:
                table[color] = BLUE
                blue         = color
                state        = 'blue'

                percents['red'] = percent - residue
        else:                   # state == 'blue'
            table[color] = interpolate(BLUE, WHITE, blue, color)

        area += count

    stderr.write("Color profile:\n"
                 "\tdark blue: %.2f%%\n"
                 "\tred:       %.2f%%\n"
                 "\tthe rest:  %.2f%%\n" %
                 (percents['dark-blue'],
                  percents['red'],
                  100 - percents['dark-blue'] - percents['red']))

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

    obamafied = Image.fromarray(image_array)
    obamafied.save(get_out_path(path, out_path))

def path(string):
    if not os.path.exists(string):
        raise ValueError('Path "%s" does not exist' % string)

    return string

def even(str):
    n = int(str)

    if n % 2 == 0:
        n += 1

    return n

def percent(str):
    n = int(str)

    if n >= 0 and n < 100:
        return n
    else:
        raise ValueError("Invalid value per cent value %d" % n)

def main():
    parser = ArgumentParser(description='Obamafy your photo')

    parser.add_argument('input',  type=path, help='a photo to Obamafy')
    parser.add_argument('output', type=str, nargs='?', default=None,
                        help='resulting photo')

    parser.add_argument('--posterization',
                        type=int, default=3, dest='posterization',
                        help='posterize to specified number of bits per color')
    parser.add_argument('--dark-blue',
                        type=percent, default=20, dest='dark_blue')
    parser.add_argument('--red',
                        type=percent, default=30, dest='red')
    parser.add_argument('--median', type=even, default=3, dest='median',
                        help='median filter size')

    args = parser.parse_args()


    obamafy(args.input, args.output, args)

if __name__ == '__main__':
    main()
