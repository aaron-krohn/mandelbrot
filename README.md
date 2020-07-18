# Mandelbrot

Python library used to explore the Mandelbrot set

# Setup 

```
pip install -r requirements.txt
```

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
