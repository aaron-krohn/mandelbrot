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
# TODO:
#
#   - Implement "zoom path", a series of zoom center pixel coordinates
#   - Add some color, make gradients easy
#   - Convert to class
#   - Make it fast
#   - Function to convert pixels to graph coords
#   - Create graph overlay
#
###

from PIL import Image
from matplotlib import cm
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

    # Iterations
    iters = args.iters
 
    # Zoom settings
    zoom_level = args.zoom_level
    zoom_factor = args.zoom_factor
    zoom_center = args.zoom_center

    # Colors
    color_bound = 50
    color_unbound = 200

    # Image resolution for each axis
    Re_res = args.re_res
    if args.im_res is None:
        Im_res = int((2 * Re_res) / 3)
    else:
        Im_res = args.im_res

    # Upper and lower bounds of each axis
    Re_lim = (1, -2)
    Im_lim = (1, -1)

    Re_len = abs(Re_lim[0] - Re_lim[1])
    Im_len = abs(Im_lim[0] - Im_lim[1])

    Re_incr = Re_len / Re_res
    Im_incr = Im_len / Im_res

    logger.info('Zooming to: Level %s @ %sx, centered at %s', zoom_level, zoom_factor, zoom_center)

    for z in range(zoom_level):

        # The length of line ad, the top of the new bounding box
        ad = Re_res / zoom_factor
        # Calculate the new bounds of the real axis, centered about zoom_center
        Re_min = Re_lim[1] + ((zoom_center[0] - (ad / 2)) * Re_incr)
        Re_max = Re_lim[0] - (((Re_res - zoom_center[0]) - (ad / 2)) * Re_incr)

        logger.debug('Re_min: %s + ((%s - (%s / 2)) * %s)', Re_lim[1], zoom_center[0], ad, Re_incr)
        logger.debug('Re_max: %s - (((%s - %s) - (%s / 2)) * %s)', Re_lim[0], Re_res, zoom_center[0], ad, Re_incr)

        # The length of line ab, the left side of new bounding box
        ab = Im_res / zoom_factor
        # Calculate the new bounds of the imaginary axis, centered about zoom_center
        Im_min = Im_lim[1] + ((zoom_center[1] - (ab / 2)) * Im_incr)
        Im_max = Im_lim[0] - (((Im_res - zoom_center[1]) - (ab / 2)) * Im_incr)

        logger.debug('Im_min: %s + ((%s - (%s / 2)) * %s)', Im_lim[1], zoom_center[1], ab, Im_incr)
        logger.debug('Im_max: %s - (((%s - %s) - (%s / 2)) * %s)', Im_lim[0], Im_res, zoom_center[1], ab, Im_incr)

        # Update bounds
        Re_lim = (Re_max, Re_min)
        Im_lim = (Im_max, Im_min)

        # Calculate length of each axis
        Re_len = abs(Re_lim[0] - Re_lim[1])
        Im_len = abs(Im_lim[0] - Im_lim[1])

        # Calculate the graph-size of each pixel
        Re_incr = Re_len / Re_res
        Im_incr = Im_len / Im_res

        # After the first iteration of zoom, the frame is now centered about
        # the original zoom center, so we adjust to continue zooming to the
        # center of the frame in order to continue zooming on the desired pixel
        zoom_center = (int(Re_res / 2), int(Im_res / 2))

    logger.info('Re bounds: %s', Re_lim)
    logger.info('Im bounds: %s', Im_lim)
    logger.info('Re increment: %s', Re_incr)
    logger.info('Im increment: %s', Im_incr)

    logger.info('Initializing c values for frame')
    cdata = np.zeros((Im_res, Re_res), dtype=np.complex_)
    for yidx, y in enumerate(range(1, Im_res + 1)):
        for xidx, x in enumerate(range(1, Re_res + 1)):

            # Calculates the value of c for each pixel on the graph
            cdata[yidx,xidx] = complex(Re_lim[1] + (Re_incr * x), Im_lim[1] + (Im_incr * y))

    # This simple lambda function is responsible for the magic
    brot = lambda z, c: (z * z) + c
    # Array of z values to be manipulated
    pixels = np.full((Im_res, Re_res), complex(0,0))
    unbound = np.zeros((Im_res, Re_res))

    logger.info('Iterating z values')
    for i in range(iters):

        # All bounded values are contained within 2.0+2.0j, -2.0-2.0j
        pixels = np.where(
            np.logical_and(
                pixels.real <= 2.0,
                pixels.imag <= 2.0
            ),
            brot(pixels, cdata),
            pixels
        )

        unbound = np.where(
            np.logical_or(
                pixels.real >= 2.0,
                pixels.imag >= 2.0
            ),
            unbound + 1,
            unbound
         )
                

    logger.info('Rendering complete after %s iterations', i+1)
    logger.info('Generating image data')

    img_data = (unbound / iters) * 255

    logger.info('Writing image to %s', args.outfile)
    im = Image.fromarray(np.uint8(img_data))
    im.save(args.outfile)

    end = time.time()
    logger.info('Frame rendering complete in %s seconds', (end - start))
