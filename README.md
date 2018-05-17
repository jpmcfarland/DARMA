# DARMA

A Data Access, Representation, and MAnipulation interface using
AstroPy/PyFITS for FITS input/ouput and NumPy for Array manipulation,
adapted from ESO's Eclipse library Python interface and some of its
C-code (http://www.eso.org/eclipse/).

---

Merriam-Webster's Online Dictionary defines the progenitor term 'dharma'
from Hinduism & Buddhism as:

    2a: the basic principles of cosmic or individual existence

Thus, DARMA objects access, represent, and manipulate the most basic form
of information that the data can take.

---

Author: John P. McFarland <johnpatrickmcfarland@gmail.com>

---

This package provides a number of modules currently interfacing with the
AstroPy.io.fits/PyFITS module to represent many forms of FITS data.  The
PyFITS module was developed by Space Telescope Science Institute (STScI)
and provides an interface between FITS images and NumPy arrays.  The
AstroPy.io.fits module is a port of the PyFITS module by the AstroPy
project.  NumPy was also developed by STScI.  For more information, see:

* http://www.astropy.org/
* http://www.stsci.edu/resources/software_hardware/pyfits
* http://www.numpy.org/

---

This package provides the following modules:

              image: implements the image object with methods to process
                     2D FITS image data
            bitmask: An 8-bit structure to store up to 8 bitmasks
                     parallel with an image
               cube: a cube object is list of images with methods that
                     process stacks of images
             header: a FITS header object, resembling a dictionary
           pixelmap: a map of boolean pixel values indicating good/bad
                    (1/0) data
             common: auxiliary data structures and constants
    image_generator: Genenerate artificial data

Incomplete modules:

              table: a representation of a binary FITS table and
                     associated methods (currently limited to readonly)
             mosaic: a mosaic object is a set of images linked by a
                     common spatial layout (e.g., astrometry)

In addition the package provides:

            bitmask_test: unit tests for bitmask module
             common_test: unit tests for common module
               cube_test: unit tests for cube module
             header_test: unit tests for header module
    image_generator_test: unit tests for image_generator module
              image_test: unit tests for image module
           pixelmap_test: unit tests for pixelmap module
             tables_test: unit tests for tables module

---
