#!/usr/bin/env python3

###
# According to Wikipedia:
#
#    A point c is colored black if it belongs to the set, and white if not.
#    Re[c] and Im[c] denote the real and imaginary parts of c, respectively.
#
# The full set exists in  -1 < Im < 1 and -2 < Re < 1
#
# The objective, then, is to determine, for each pixel, whether or not it
# is "within the [Mandelbrot] set".
#
# To determine if a given pixel is "in", 
#
#    Thus, a complex number c is a member of the Mandelbrot set if,
#    when starting with z0 = 0 and applying the iteration repeatedly,
#    the absolute value of zn remains bounded for all n > 0
#
# The formal definition of the set is:
#
#    The Mandelbrot set is the set of values of c in the complex plane
#    for which the orbit of 0 under iteration of the quadratic map
#    z_{n+1}=z_{n}^{2}+c} remains bounded.
#
# So how do we know if it's "bounded" or not?
# 
#    For example, for c = 1, the sequence is 0, 1, 2, 5, 26, ..., 
#    which tends to infinity, so 1 is not an element of the Mandelbrot set.
#    On the other hand, for c = −1, the sequence is 0, −1, 0, −1, 0, ..., 
#    which is bounded, so −1 does belong to the set.
#
# I think we could probably check boundedness by plugging in a number that
# is really large to see if it returns an answer. Oh, umm... maybe we're
# looking for the concept of "limiting".
#
# So, "what is the limit as n approaches infinity for a given value of c?"
#
# That we can do.
#
# The image resolution needs to be known, and has a 3:2 ratio. 
# 
# So we can the assign each pixel two float values for the coordinates,
# equal to: Im = viewport_width / x_resolution.
#
# Which also means that "zooming in" is simply changing the maximum values
# of Im and Re, and redrawing the frame.
#
# Determining the number of iterations:
#
# "How many iterations of calculating z do we need to do in
#  order to determine whether or not that pixel is bounded?"
#
# If you don't calculate enough iterations, the edges of the image will
# not be well-defined.
#
# So I guess, general rule of thumb, the more iterations, the better quality.
#
# Hint: For each iteration, check if the image is stable from the last frame.
#       If the number of changed pixels is below the threshold, then you can
#       stop iterating.
#
# Colorizing
#
# The color gradient is pretty simple conceptually. Colorizing is for pixels
# that are outside of the set. The longer (more iterations) it takes for the
# 'z' value to escape, the closer the color of that pixel is to the color of
# the pixels in the side. The faster the 'z' value goes out of bounds, the
# closer the color is to an outside pixel.
#
# Bugs
#
#   - 2nd zoom level distorts image, not working as expected 
#
###

from PIL import Image
import pandas as pd
import numpy as np
import argparse
import logging
import time
import re

def coords(arg_value):
    """ Validates the value passed for coordinates """

    pat = re.compile(r'^[0-9]+,[0-9]+$')

    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError('Invalid coordinate format')

    return tuple(map(int, arg_value.split(',')))

def loglevel(arg_value):
    """ Validates log level value """

    if not hasattr(logging, arg_value):
        raise argparse.ArgumentTypeError('Invalid log level')

    return getattr(logging, arg_value)

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--iterations', dest='iters', action='store',
        help='Maximum number of iterations per pixel to determine boundedness',
        default=200, type=int)

    parser.add_argument('-l', '--zoom-level', dest='zoom_level', action='store',
        help='Number of times to zoom in', default=0, type=int)

    parser.add_argument('-z', '--zoom-factor', dest='zoom_factor', action='store',
        help='Size of the area to zoom, relative to total render size. The larger the number, the smalled the area that is zoomed.',
        default=0, type=int)

    parser.add_argument('-c', '--zoom-center', dest='zoom_center', action='store',
        help='The y,x coordinates of the center of zoom location.',
        default='0,0', metavar='Y,X', type=coords)

    parser.add_argument('-r', '--resolution', dest='re_res', action='store',
        help='Horizontal resolution in pixels. Assumes 3:2 aspect ratio.',
        default=3000, type=int)

    parser.add_argument('-v', '--height', dest='im_res', action='store',
        help='Vertical resolution when desired aspect ratio is not 3:2',
        default=None, type=int)

    parser.add_argument('-f', '--file', dest='outfile', action='store',
        help='File location to write the frame to', default='frame.png')

    parser.add_argument('-g', '--log-level', dest='loglevel', action='store',
        help='Log level: [DEBUG|INFO|WARNING|ERROR|CRITICAL]', default='INFO',
        type=loglevel)

    args = parser.parse_args()

    return args

if __name__ == '__main__':

    start = time.time()

    args = parse_args()

    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(message)s')
    logger = logging.getLogger()

    logger.info('Initializing Mandelbrot explorer')

    iters = args.iters
    
    zoom_level = args.zoom_level
    zoom_factor = args.zoom_factor
    zoom_center = args.zoom_center

    Re_res = args.re_res
    if args.im_res is None:
        Im_res = int((2 * Re_res) / 3)
    else:
        Im_res = args.im_res

    Re_lim = (1, -2)
    Im_lim = (1, -1)

    Re_len = abs(Re_lim[0] - Re_lim[1])
    Im_len = abs(Im_lim[0] - Im_lim[1])

    Re_incr = Re_len / Re_res
    Im_incr = Im_len / Im_res

    logger.info('Zooming to: Level %s @ %sx, centered at %s', zoom_level, zoom_factor, zoom_center)

    for z in range(zoom_level):

        ad = Re_res / zoom_factor
        Re_min = Re_lim[1] + ((zoom_center[0] - (ad / 2)) * Re_incr)
        Re_max = Re_lim[0] - (((Re_res - zoom_center[0]) - (ad / 2)) * Re_incr)

        logger.debug('Re_min: %s + ((%s - (%s / 2)) * %s)', Re_lim[1], zoom_center[0], ad, Re_incr)
        logger.debug('Re_max: %s - (((%s - %s) - (%s / 2)) * %s)', Re_lim[0], Re_res, zoom_center[0], ad, Re_incr)

        ab = Im_res / zoom_factor
        Im_min = Im_lim[1] + ((zoom_center[1] - (ab / 2)) * Im_incr)
        Im_max = Im_lim[0] - (((Im_res - zoom_center[1]) - (ab / 2)) * Im_incr)

        logger.debug('Im_min: %s + ((%s - (%s / 2)) * %s)', Im_lim[1], zoom_center[1], ab, Im_incr)
        logger.debug('Im_max: %s - (((%s - %s) - (%s / 2)) * %s)', Im_lim[0], Im_res, zoom_center[1], ab, Im_incr)

        Re_lim = (Re_max, Re_min)
        Im_lim = (Im_max, Im_min)

        Re_len = abs(Re_lim[0] - Re_lim[1])
        Im_len = abs(Im_lim[0] - Im_lim[1])
    
        Re_incr = Re_len / Re_res
        Im_incr = Im_len / Im_res

        # After the first iteration of zoom, the frame is now centered about
        # the original zoom center, so we adjust to continue zooming to the
        # center of the frame in order to continue zooming on the desired pixel
        zoom_center = (int(Re_res / 2), int(Im_res / 2))

    pixels = []

    logger.info('Re bounds: %s', Re_lim)
    logger.info('Im bounds: %s', Im_lim)
    logger.info('Re increment: %s', Re_incr)
    logger.info('Im increment: %s', Im_incr)

    ratio = 255 / iters
    for Im in [Im_lim[1] + (Im_incr * y) for y in range(1, Im_res + 1)]:
        for Re in [Re_lim[1] + (Re_incr * x) for x in range(1, Re_res + 1)]:
    
            c = complex(Re, Im)
            z = complex(0,0)
            count = 0

            for i in range(iters):
                z = (z * z) + c
                count += 1
                if z.imag > 2.0 or z.real > 2.0:
                    break

            if count > iters:
                app = 255
            else:
                app = int(255 * (count / iters))

            pixels.append([app, app, app])
    
    pixels = np.array(pixels, dtype=np.uint8)
    pixels = pixels.reshape((Im_res, Re_res, 3))

    logger.info('Writing image data to %s', args.outfile)
    im = Image.fromarray(pixels)
    im.save(args.outfile)

    end = time.time()
    logger.info('Frame rendering complete in %s seconds', (end - start))
