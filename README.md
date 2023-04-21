# Mandelbrot

Draws images of the Mandelbrot set. There are much faster ways of doing this.

# Setup 

```
pip install -r requirements.txt
```

# Quickstart

```
./mandelbrot.py --iterations 100 --zoom-level 0 --zoom-center 0,0 --resolution 3000 --file mb_1.png --log-level DEBUG
```

Note: If the resolution isn't 3000, you're gonna have a bad time. Round numbers according to current ratio only!

# Usage

```
$ ./mandelbrot.py -h
usage: mandelbrot.py [-h] [-i ITERS] [-l ZOOM_LEVEL] [-z ZOOM_FACTOR] [-c Y,X]
                     [-r RE_RES] [-v IM_RES] [-f OUTFILE]

optional arguments:
  -h, --help            show this help message and exit
  -i ITERS, --iterations ITERS
                        Maximum number of iterations per pixel to determine
                        boundedness
  -l ZOOM_LEVEL, --zoom-level ZOOM_LEVEL
                        Number of times to zoom in
  -z ZOOM_FACTOR, --zoom-factor ZOOM_FACTOR
                        Size of the area to zoom, relative to total render
                        size. The larger the number, the smalled the area that
                        is zoomed.
  -c Y,X, --zoom-center Y,X
                        The y,x coordinates of the center of zoom location.
  -r RE_RES, --resolution RE_RES
                        Horizontal resolution in pixels. Assumes 3:2 aspect
                        ratio.
  -v IM_RES, --height IM_RES
                        Vertical resolution when desired aspect ratio is not
                        3:2
  -f OUTFILE, --file OUTFILE
                        File location to write the frame to
```

# References

https://en.wikipedia.org/wiki/Mandelbrot_set

https://fractaltodesktop.com/mandelbrot-set-basics/index.html

# Example

![Mandelbrot zero](./mb_1.png?raw=true)
