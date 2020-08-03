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

class Mandelbrot():

    def __init__(self):

        logger.info('Initializing Mandelbrot explorer')

        self.iterations = 200

        self.gradient = [50, 200]

        self.res      = {'re': 3000,
                         'im': 2000}

        self.zoom     = {'level': 0,
                         'factor': 2,
                         'center': [0,0]}

        self.bounds   = {'re': [1, -2],
                         'im': [1, -1]}

        self.lengths  = {'re': 3,
                         'im': 2}

        self.incr     = {'re': 0.001,
                         'im': 0.001}

        self.gconf    = [
                         (0, (  0,   0,   0)),
                         (1, (200, 255, 200)),
                         (2, (150, 200, 150)),
                         (3, (100, 150, 100)),
                         (4, ( 50, 100,  50)),
                        ]

        self.c       = np.zeros((self.res['im'], self.res['re']), dtype=np.complex_)
        self.z       = np.zeros((self.res['im'], self.res['re']), dtype=np.complex_)
        self.niters  = np.zeros((self.res['im'], self.res['re']))
        self.img     = np.zeros((self.res['im'], self.res['re'], 3), dtype=np.uint8)

    def brot(self, z, c):

        return (z * z) + c

    def calc_zoom(self):

        logger.info('Zooming to: Level %s @ %sx, centered at %s',
            self.zoom['level'],
            self.zoom['factor'],
            self.zoom['center']
        )

        for z in range(self.zoom['level']):
    
            # The length of line ab, and ad, the left and top edges
            # of the new viewport bounding box
            ab = self.res['im'] / self.zoom['factor']
            ad = self.res['re'] / self.zoom['factor']

            # Calculate the new bounds of each axis, centered about self.zoom['center']
            re_min = self.bounds['re'][1] + ((self.zoom['center'][0] - (ad / 2)) * self.incr['re'])
            im_min = self.bounds['im'][1] + ((self.zoom['center'][1] - (ab / 2)) * self.incr['im'])

            re_max = self.bounds['re'][0] - (((self.res['re'] - self.zoom['center'][0]) - (ad / 2)) * self.incr['re'])
            im_max = self.bounds['im'][0] - (((self.res['im'] - self.zoom['center'][1]) - (ab / 2)) * self.incr['im'])
    
            self.set_bounds(re_min=re_min, re_max=re_max, im_min=im_min, im_max=im_max)

            # Calculate length of each axis
            self.calc_lengths()

            # Calculate the graph-size of each pixel
            self.calc_increments()
    
            # After the first iteration of zoom, the frame is now centered about
            # the original zoom center, so we adjust to continue zooming to the
            # center of the frame in order to continue zooming on the desired pixel
            center = [int(self.res['re'] / 2),
                      int(self.res['im'] / 2)]
            self.set_zoom(center=center)

            # Debug logging
            logger.debug('re_min: %s + ((%s - (%s / 2)) * %s)',
                self.bounds['re'][1],
                self.zoom['center'][0],
                ad,
                self.incr['re']
            )
            logger.debug('re_max: %s - (((%s - %s) - (%s / 2)) * %s)',
                self.bounds['re'][0],
                self.res['re'],
                self.zoom['center'][0],
                ad,
                self.incr['re']
            )
            logger.debug('im_min: %s + ((%s - (%s / 2)) * %s)',
                self.bounds['im'][1],
                self.zoom['center'][1],
                ab,
                self.incr['im']
            )
            logger.debug('im_max: %s - (((%s - %s) - (%s / 2)) * %s)',
                self.bounds['im'][0],
                self.res['im'],
                self.zoom['center'][1],
                ab,
                self.incr['im']
            )

    def calc_increments(self):

        self.incr['re'] = self.lengths['re'] / self.res['re']
        self.incr['im'] = self.lengths['im'] / self.res['im']

        logger.debug('incr[re]: %s, incr[im]: %s', self.incr['re'], self.incr['im'])

    def calc_lengths(self):

        self.lengths['re'] = abs(self.bounds['re'][0] - self.bounds['re'][1])
        self.lengths['im'] = abs(self.bounds['im'][0] - self.bounds['im'][1])

        logger.debug('len[re]: %s, len[im]: %s', self.lengths['re'], self.lengths['im'])


    def set_bounds(self, re_max=None, re_min=None, im_max=None, im_min=None):

        if re_max is not None:
            self.bounds['re'][0] = re_max

        if re_min is not None:
            self.bounds['re'][1] = re_min

        if im_max is not None:
            self.bounds['im'][0] = im_max

        if im_min is not None:
            self.bounds['im'][1] = im_min

        logger.debug('bounds[re]: (%s, %s)', self.bounds['re'][0], self.bounds['re'][1])
        logger.debug('bounds[im]: (%s, %s)', self.bounds['im'][0], self.bounds['im'][1])
          

    def set_resolution(self, re_res, im_res=None):

        self.res['re'] = int(re_res)

        if im_res is None:
            self.res['im'] = int((2 * self.res['re']) / 3)
        else:
            self.res['im'] = int(im_res)

        logger.debug('resolution: (%s, %s)', self.res['im'], self.res['re'])

    def set_zoom(self, level=None, factor=None, center=None):

        if level is not None:
            self.zoom['level'] = level

        if factor is not None:
            self.zoom['factor'] = factor

        if center is not None:
            self.zoom['center'] = center

        logger.debug('zoom: %s', self.zoom)

    def calc_c(self):

        for yidx, y in enumerate(range(1, self.res['im'] + 1)):
            for xidx, x in enumerate(range(1, self.res['re'] + 1)):

                # Calculates the value of c for each pixel on the graph
                cval = complex(
                    self.bounds['re'][1] + (self.incr['re'] * x),
                    self.bounds['im'][1] + (self.incr['im'] * y)
                )
                self.c[yidx][xidx] = cval

    def calc_z(self):

        logger.info('Iterating z values')

        for i in range(self.iterations):

            # All bounded values are contained within 2.0+2.0j, -2.0-2.0j
            self.z = np.where(
                np.logical_and(
                    self.z.real <= 2.0,
                    self.z.imag <= 2.0
                ),
                self.brot(self.z, self.c),
                self.z
            )

            self.niters = self.niters + 1

        logger.info('Rendering complete after %s iterations', i+1)

    def calc_gradient(self):

        logger.info('Generating image data')


        rgbs = []

        # Generates an array of RGB data equal in size to the final image,
        # containing the user-provided gradient configuration
        for niters, rgb in self.gconf:
            rgbs.append((niters, np.full((self.res['im'], self.res['re'], 3), rgb)))

        # Masks the gradient layers into the final image. It does this by
        # placing a layer from the RGB config if the iterations match the
        # config.
        for idx in range(len(rgbs)):

            niters, rgb = rgbs[idx]

            self.img[...,0] = np.where(
                                  self.z.real >= niters,
                                  rgb[...,0],
                                  self.img[...,0]
                              )
            self.img[...,1] = np.where(
                                  self.z.real >= niters,
                                  rgb[...,1],
                                  self.img[...,1]
                              )
            self.img[...,2] = np.where(
                                  self.z.real >= niters,
                                  rgb[...,2],
                                  self.img[...,2]
                              )

    def write_frame(self, filename):

        logger.info('Writing image to %s', args.outfile)

        im = Image.fromarray(np.uint8(self.img))
        im.save(filename)

if __name__ == '__main__':

    start = time.time()

    args = parse_args()

    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(message)s')
    logger = logging.getLogger()

    m = Mandelbrot()

    # Iterations
    m.iterations = args.iters
 
    # Colors
    m.gradient = [50, 200]

    # Image resolution for each axis
    m.set_resolution(args.re_res)

    # Zoom settings
    m.set_zoom(level=args.zoom_level,
        factor=args.zoom_factor,
        center=args.zoom_center
    )

    m.calc_lengths()
    m.calc_increments()
    m.calc_zoom()

    # COMPUTE
    m.calc_c()
    m.calc_z()

    # Generate image data
    m.calc_gradient()

    # Write image
    m.write_frame(args.outfile)

    end = time.time()
    logger.info('Frame rendering complete in %s seconds', (end - start))
