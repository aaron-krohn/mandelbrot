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
# TODO
#
#   - Add argparse flags
###

from PIL import Image
import pandas as pd
import numpy as np
import cmath
import time

iters = 200

zoom_level = 2
zoom_factor = 2
zoom_center = (1365, 595) 

Re_res = 3000
Im_res = int((Re_res / 3.0) * 2)

Re_lim = (1, -2)
Im_lim = (1, -1)

for z in range(zoom_level):

    # Absolute size of Re and Im
    Re_abs = abs(Re_lim[0]) + abs(Re_lim[1])
    Im_abs = abs(Im_lim[0]) + abs(Im_lim[1])

    # Location of zoom_center, translated from pixels to graph values
    Re_cen = ((zoom_center[0] / Re_res) * Re_abs) + Re_lim[1]
    Im_cen = ((zoom_center[1] / Im_res) * Im_abs) + Im_lim[1]

    # Absolute lengths of new viewport
    Re_new = Re_abs / zoom_factor
    Im_new = Im_abs / zoom_factor

    # With center of new viewport on the center
    Re_lim = (Re_cen + (Re_new / 2), Re_cen - (Re_new / 2))
    Im_lim = (Im_cen + (Im_new / 2), Im_cen - (Im_new / 2))

Re_incr = (abs(Re_lim[0]) + abs(Re_lim[1])) / float(Re_res)
Im_incr = (abs(Im_lim[0]) + abs(Im_lim[1])) / float(Im_res)

Re_pix = []
Im_pix = []

for Im in [Im_lim[1] + (Im_incr * y) for y in range(1, Im_res + 1)]:
    for Re in [Re_lim[1] + (Re_incr * x) for x in range(1, Re_res + 1)]:

        c = complex(Re, Im)
        z = complex(0,0)

        for i in range(iters):
            z = (z * z) + c
            if z.imag > 2.0 or z.real > 2.0:
                break

        Im_pix.append(True if z.imag < 2.0 else False)
        Re_pix.append(True if z.real < 2.0 else False)

Im_pix = np.array(Im_pix, dtype=bool)
Re_pix = np.array(Re_pix, dtype=bool)

pixels = Im_pix & Re_pix
pixels = pixels.reshape((Im_res, Re_res))

im = Image.fromarray(pixels)
im.save('mandelbrot.png')
