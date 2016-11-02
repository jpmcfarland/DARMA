'''Implements the image object with methods to process a 2D FITS image.
'''

__version__ = '@(#)$Revision$'

import math
import os

#from .common import Array, Arrayfft, Arrayfilters
from .common import fits, Array, Arrayfft, fits_open
from .common import DARMAError, _HAS_NUMPY, DataStruct, StatStruct, FLOAT
from .common import update_header
from .pixelmap import pixelmap
from .bitmask import bitmask
try:
    range = xrange  # Python 2
except NameError:
    pass  # Python 3


class image(DataStruct):

    '''
       A 2D FITS image

       This is the basic object used to manipulate FITS images.  This object
       interfaces Array objects to provide a far greater range of image
       manipulation and direct access to the data.

       NOTE: All interfaces through the image object have the axes in the
             expected order: x,y (or NAXIS1,NAXIS2) with a unity-index access
             to the data (FITS standard), but the PyFITS interface returns an
             Array object with them in a swapped format due to row-major to
             column-major conversion: (y,x) assigned to the data attribute of
             the image object that is zero-indexed.  This is due to the way
             Array counts axes slow to fast.  Logically, data is stored in the
             array as a list of lists, where the first axis refers to
             individual lists, and the second refers to the list elements:
             rows then columns respectively (or NAXIS2 index then NAXIS1 index
             respectively in FITS terms).  Data in a FITS file is stored in
             exactly this same way making the loading and unloading of data
             arrays most efficient if this convention is used.

             When accessing array elements through the data attribute
             directly, be aware of these inconsistencies.  Also, if manually
             creating a data array for inclusion into an image, the shape
             should be (NAXIS2, NAXIS1).  For example:

                 img = image()
                 img.data = Array.array((NAXIS2, NAXIS1), dtype='float32')

             or preferably

                 img = img(data=Array.array((NAXIS2, NAXIS1)))

       The image object provides several classes of operations:

       Data Access
       ===========

       The data of the image can be accessed directly from the image object
       itself in the typical Python way.  Regardless of whether the index is a
       slice, coordinate tuple, or single coordinate, an image containing the
       requested data is returned.  This means that accessing one data element
       is possible, but a one element image is returned.  To get the value of
       that one element, it is a simple matter to access the data Array
       directly:

       > number = img[x,y].data[()]
       > print number
       <value at FITS coordinates (x,y)>

       Note: A single element (scalar) array results from the above operation.
             The index '()' is used to 'extract' that scalar in it's native
             format (using data[0] will not work).  The scalar array can also
             be cast into any other Python data-type or be used directly in
             arithmetic operations.  In the latter case, a scalar array
             results from the operation.

       Note: As mentioned above, data access directly from the image object
             follows FITS convention (unity-indexed [NAXIS1, NAXIS2).
             Attempting to access the [0,0] element of an image will results
             in an error:

             > img[0,0]
             DARMAError, Index [%d, _] not in FITS convention!
             Index [0, _] not in FITS convention!

       Indexes
       -------
       Positive indexes go from 1...n, negative indexes are supported and mimic
       the standard Python conventions (e.g., -1 is the last element).

       Slices
       ------
       Slices work a little differently from Python standard.  A little thought
       on the index behavior will reveal that a blank initial index means start
       at index 1, blank terminal index means stop at and include index n, and
       the range of the slice is terminal_index - initial_index + 1.  Normal
       Python behavior says stop at and include n-1.  For example:

       > img = image.make_image(20, 20)
       > img.shape
       (20, 20)
       > img[1:10, :].shape
       (10, 20)
       > img.data[:, 1:10].shape
       (20, 9)

       Note the data Array is stored with the axes in reversed order as is the
       PyFITS standard.

       Introspection
       =============

       >>> xsize, ysize = img.xsize(), img.ysize()

       Arithmetic
       ==========

       Given two images, one can:

       >>> newima = ima1 + ima2    # add them
       >>> newima = ima1 - ima2    # subtract them
       >>> newima = ima1 * ima2    # multiply them
       >>> newima = ima1 / ima2    # divide them

       One can also use constants in arithmetic operations:

       >>> newima = ima + 2.5
       >>> newima = ima - 3.2
       >>> newima = ima * 1.7
       >>> newima = ima / 1.11111
       >>> newima = ima ** 2       # squared image

       Note that arithmetic operations copy results. It might be more
       efficient to perform in-place operations:

       >>> ima1 += ima2
       >>> ima1 **= 0.5            # a sqrt image

       However, in-place operations cannot be performed on images that are
       read-only.

       image extraction
       ================

       One can use

       >>> newima = ima.extract_region(x0, y0, x1, y1)

       to extract a sub region from ima, or use a slice directly:

       >>> newima = ima[x0:x1, y0:y1]

       Statistics
       ==========

       A number of operations allow one to obtain statstics for an image or
       some specified part of an image

       >>> img.stat(domedian=1)

       is used to obtain a common.StatStruct object (q.v.) containg
       statistics values (a.o.: mean, median, minimum, and maximum)

       >>> img.get_mean()
       >>> img.get_median()

       return just the mean and median respectively

       >>> img.stat_opts(...)

       allows one to specify a pixelmap of valid pixels and/or an area of
       valid data and/or a range of valid pixel values to specify which
       data should be included when computing statistics


       Filtering
       =========

       >>> img.filter_mean(xsize, ysize)
       >>> img.filter_median(xsize, ysize)

       Can be used to produce mean and median filters using rectangular
       kernels of arbitrary size (in both cases the default size is 3x3).
       In addition a number of named filters can be used: filter_dx(),
       filter_dy(), filter_dx2(), filter_dy2() filter_contour1(),
       filter_contour2(), filter_contour3(), and filter_contrast1()


       Normalization
       =============

       Using the stat method and in_place multiplication, a number of
       normalization methods have been defined.

       >>> img.normalize_mean()
       >>> img.normalize_median()
       >>> img.normalize_flux()
       >>> img.normalize_absolute_flux()

       normalize the image to a mean, median, flux or absolute flux of 1
       (other scales are possible too).  It is possible to specify relevant
       regions the same way as in image.stat_opts()

    '''

    def __init__(self, filename=None, extension=0, plane=0, readonly=0,
                 memmap=1, data=None, datatype=None, bmask=None, bit=0,
                 *args, **kwargs):
        '''
            filename: The name of a FITS file
           extension: The FITS extension number
               plane: The plane in a 3D image stack
            readonly: Indicate that the FITS file is readonly
              memmap: use memory mapping for data access (NOT IMPLEMENTED)
                data: A data array (Python sequence, Array, etc.)
            datatype: datatype of internal representation
               bmask: A bitmask of data with good pixels set to 0 and bad
                      pixels set to some non-zero value (opposite of pixelmap)
                 bit: value of the non-number bit in bitmask

           If both filename and data are set, the image is created from data.

           NOTE: self.bmask (set from the bmask option) will be regenerated
                 whenever a method requiring masking is called on this image.
                 This guarantees that if no such method is called, no memory
                 is wasted, and if one is, that the mask stays up to date.
                 See the help for bitmask for more information.
        '''

        DataStruct.__init__(self, *args, **kwargs)
        self.log('image constructor', 'verbose')
        self.log('image constructor: filename=%s, extension=%s, plane=%s, readonly=%s, memmap=%s, data=%s, datatype=%s, bmask=%s, bit=%s, args=%s, kwargs=%s' % (
            filename, extension, plane, readonly, memmap, data, datatype, bmask, bit, args, kwargs), 'debug')

        self.filename = filename
        self.extension = extension
        self.plane = plane
        self.readonly = readonly
        self.memmap = memmap
        self._data = data
        self._datatype = datatype
        self.bmask = bmask
        self.bit = bit

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError('Filename: %s not found!' % self.filename)

    def load(self):
        '''
           Proxy for load_image()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self.log('image load', 'verbose')
        return self.load_image()

    def load_image(self):
        '''
           Load the image from the given data Array or from filename.  If there
           is no data and no filename, the image data is set to None.
        '''

        log = self.log
        log('image load_image', 'verbose')
        filename = self.filename
        extension = self.extension
        plane = self.plane
        readonly = self.readonly
        memmap = self.memmap
        datatype = self._datatype
        bit = self.bit

        if self._data is None:
            if filename is not None:
                try:
                    log('image load_image from file: filename=%s, memmap=%s, extension=%s' %
                        (filename, memmap, extension), 'debug')
                    #self._data = fits.getdata(filename, extension)
                    self._data = fits_open(filename, memmap=memmap)[extension].data
                except Exception as e:
                    raise DARMAError('Error loading image from %s: %s' % (filename, e))
        else:
            log('image load_image from data array: data=%s, dtype=%s' % (self._data, datatype), 'debug')
            self._data = Array.asanyarray(self._data, dtype=datatype)
        if self._data is not None and not self._data.flags.contiguous:
            log('image load_image make contiguous', 'debug')
            self._data = Array.ascontiguousarray(self._data, dtype=datatype)
            if self.bmask is not None:
                log('image load_image make contiguous bmask', 'debug')
                self.bmask.data = Array.ascontiguousarray(self.bmask.data)

        if self._data is not None and len(self._data.shape) == 3:
            log('image load_image select plane %s' % plane, 'debug')
            self._data = self._data[plane]

        if self.bmask is None:
            log('image load_image initialize bmask', 'debug')
            self.bmask = bitmask(conserve=True, datatype='bool')

    def as_pixelmap(self):
        '''
           Return a pixelmap object constructed from this image object.
           Values are converted to a boolean array (i.e.,  0 ? 0 : 1)
        '''

        return pixelmap(data=self.data)

    def has_nonnumbers(self):
        '''
           Determine if non-numbers (NaN, Inf, etc.) exist in the data.
        '''

        self.log('image has_nonnumbers', 'verbose')
        bit = self.bit
        if not self.bmask.has_bit(bit=bit):
            self.log('image has_nonnumbers constructing bmask', 'debug')
            pmap = pixelmap(data=Array.isfinite(self.data))
            self.bmask.add_pixelmap(pmap=pmap, bit=bit)
        return self.bmask.has_bit(bit=bit)

    def count_nonnumbers(self):
        '''
           Return the number of nonnumbers in the image.
        '''

        self.log('image count_nonnumbers', 'verbose')
        bit = self.bit
        # if not self.bmask.has_bit(bit=bit):
        #    pmap = pixelmap(data=Array.isfinite(self.data))
        #    self.bmask.add_pixelmap(pmap=pmap, bit=bit)
        # if not self.bmask.has_bit(bit=bit):
        if not self.has_nonnumbers():
            return 0
        else:
            self.log('image count_nonnumbers found nonnumbers', 'debug')
            pdata = self.bmask.as_pixelmap(mask=2**bit).data
            return self.size - pdata.nonzero()[0].shape[0]

    def map_nonnumbers(self):
        '''
           Return a pixelmap with nonnumbers in the image marked as bad.
        '''

        self.log('image map_nonnumbers', 'verbose')
        bit = self.bit
        if not self.bmask.has_bit(bit=bit):
            self.log('image map_nonnumbers constructing bmask', 'debug')
            pmap = pixelmap(data=Array.isfinite(self.data))
            self.bmask.add_pixelmap(pmap=pmap, bit=bit)
        return self.bmask.as_pixelmap(mask=1 << bit)

    ################################################################
    #
    # Statistics
    #

    def stat(self, domedian=True, filter=False):
        '''
           Compute the statistics.

           domedian: compute median
             filter: filter out non-numbers (NaN, Inf, etc.)

           Returns a StatStruct object. Adds an attribute 'convergence' to the
           StatStruct object. The value of this attribute is 1 if the iteration
           converged, 0 otherwise.  The number of iterations is also added
           under the 'iterations' attribute.
        '''

        return self.iter_stat_opts(max_iter=None, threshold=None,
                                   domedian=domedian, filter=filter)

    def stat_opts(self, pixmap=None, pixrange=None, zone=None, domedian=True,
                  filter=False):
        '''
           Compute the statistics, using a pixmap and/or a pixrange and/or a
           zone to define included pixels.

             pixmap: boolean array of same shape as self.data (0=bad, 1=good)
           pixrange: a range of valid values (low, high)
               zone: a tuple defining the valid zone (x0, y0, x1, y1)
           domedian: compute median
             filter: filter out non-numbers (NaN, Inf, etc.)

           Returns a StatStruct object. Adds an attribute 'convergence' to the
           StatStruct object. The value of this attribute is 1 if the iteration
           converged, 0 otherwise.  The number of iterations is also added
           under the 'iterations' attribute.
        '''

        return self.iter_stat_opts(pixmap=pixmap, pixrange=pixrange, zone=zone,
                                   max_iter=None, threshold=None,
                                   domedian=domedian, filter=filter)

    def iter_stat(self, max_iter=5, threshold=5.0, domedian=True,
                  filter=False):
        '''
           Compute the statistics iteratively.

            max_iter: maximum number of iterations
           threshold: rejection threshold (relative to stdev)
            domedian: compute median
              filter: filter out non-numbers (NaN, Inf, etc.)

           Iteratively approximate the image statistics by rejecting outliers
           from the interval [median-threshold*stdev, median+thresold*stdev]

           NOTE: If either max_iter or threshold is set to None or if domedian
                 is set to False, the iterative behavior is disabled as all are
                 required for the iterations.

           Returns a StatStruct object. Adds an attribute 'convergence' to the
           StatStruct object. The value of this attribute is 1 if the iteration
           converged, 0 otherwise.  The number of iterations is also added
           under the 'iterations' attribute.

        '''

        return self.iter_stat_opts(max_iter=max_iter, threshold=threshold,
                                   domedian=domedian, filter=filter)

    def iter_stat_opts(self, pixmap=None, pixrange=None, zone=None, max_iter=5,
                       threshold=5.0, domedian=True, filter=False):
        '''
           Compute the statistics iteratively, using a pixmap and/or a pixrange
           and/or a zone to define included pixels.

              pixmap: pixelmap object of same shape as self (0=bad, 1=good)
            pixrange: a range of valid values (low, high)
                zone: a tuple defining the valid zone (x0, y0, x1, y1)
            max_iter: maximum number of iterations
           threshold: rejection threshold (relative to stdev)
            domedian: compute median
              filter: filter out non-numbers (NaN, Inf, etc.)

           Iteratively approximate the image statistics by rejecting outliers
           from the interval [median-threshold*stdev, median+thresold*stdev]

           NOTE: If either max_iter or threshold is set to None or if domedian
                 is set to False, the iterative behavior is disabled as all are
                 required for the iterations.

           Returns a StatStruct object. Adds an attribute 'convergence' to the
           StatStruct object. The value of this attribute is 1 if the iteration
           converged, 0 otherwise.  The number of iterations is also added
           under the 'iterations' attribute.

        '''

        # self/img and pixmap/pmap are image and pixelmap objects, respectively
        # _data, _mask, and _pmap are Arrays

        bit = self.bit
        # Determine the valid pixels.
        #
        # Get the data from the image (self->img) and put it in _data
        if zone is not None:
            img = self.extract_region(zone[0], zone[1], zone[2], zone[3])
        else:
            img = self
        _data = img.data.ravel()
        if filter and not img.bmask.has_bit(bit=bit):
            pmap = pixelmap(data=Array.isfinite(img.data))
            img.bmask.add_pixelmap(pmap=pmap, bit=bit)
            _mask = img.bmask.as_pixelmap(mask=2**bit).data
        elif filter and img.bmask.has_bit(bit=bit):
            _mask = img.bmask.as_pixelmap(mask=2**bit).data
        else:
            _mask = None
        if _mask is not None:
            _mask = _mask.ravel()
        # Get the data from the pixelmap (pmap) and put it into _pmap
        if pixmap is not None:
            if zone is not None:
                _pmap = pixmap.extract_region(zone[0], zone[1], zone[2],
                                              zone[3]).data
            else:
                _pmap = pixmap.data
            _pmap = _pmap.ravel()
            # Merge _pmap with any existing mask
            if _mask is not None:
                _mask &= _pmap
            else:
                _mask = _pmap
            del _pmap
        # Mask pixels out of range
        if pixrange is not None:
            _masklo = _data > pixrange[0]
            _maskhi = _data < pixrange[1]
            if _mask is not None:
                _mask &= _masklo
                _mask &= _maskhi
            else:
                _mask = _masklo & _maskhi
        # Remove the invalid pixels.
        if _mask is not None and not _mask.all():
            _data = _data.compress(_mask)
        # Start the main statistics loop.
        n = _data.size * 1.0
        if n:
            # Compute base statistics.
            sum_val = _data.sum(dtype='float64')
            mean_val = sum_val / n
            stdev_val = math.sqrt(((_data**2).sum(dtype='float64') - ((sum_val**2) / n)) / (n - 1.0))
            # Copy and sort only for the median.
            if domedian:
                _data = _data.copy()
                _data.sort()
                median_val = median(_data, sorted=True)
            else:
                median_val = 0.0
            # Iterate if necessary.
            if max_iter is not None and threshold is not None and domedian:
                max_iter = int(max_iter)
                convergence = 0
                iter = 0
                # Iteration loop
                while not convergence and max_iter:
                    _mask = Array.abs(_data - median_val) < threshold * stdev_val
                    # Don't apply mask or recalculate statistics if there is
                    # nothing to be masked.
                    if not _mask.all():
                        _data = _data.compress(_mask)
                        n = _data.size * 1.0
                        sum_val = _data.sum(dtype='float64')
                        new_mean = sum_val / n
                        new_stdev = math.sqrt(((_data**2).sum(dtype='float64') - ((sum_val**2) / n)) / (n - 1.0))
                        median_val = median(_data, sorted=True)
                        if ((abs(new_mean / mean_val - 1) < 0.01 and
                             abs(new_stdev / stdev_val - 1) < 0.01)):
                            convergence = 1
                        mean_val = new_mean
                        stdev_val = new_stdev
                    else:
                        convergence = 1
                    max_iter -= 1
                    iter += 1
            mean_val = float(mean_val)
            median_val = float(median_val)
            # Find the min/max statistics.
            min_val = float(_data.min())
            max_val = float(_data.max())
            min_y = int(Array.argmax(Array.maximum.reduce(Array.equal(self.data, min_val), axis=1)))
            min_x = int(Array.argmax(Array.equal(self.data[min_y], min_val)))
            max_y = int(Array.argmax(Array.maximum.reduce(Array.equal(self.data, max_val), axis=1)))
            max_x = int(Array.argmax(Array.equal(self.data[max_y], max_val)))
            # Add the 1 pixel offset for FITS convention
            min_y += 1
            min_x += 1
            max_y += 1
            max_x += 1
            # Compute the energies.
            energy_val = float((_data**2).sum(dtype='float64'))
            flux_val = float(sum_val)
            absflux_val = float(Array.absolute(_data).sum(dtype='float64'))
            # Create the StatStruct.
            stat_tuple = (min_val, max_val, mean_val, median_val, stdev_val, energy_val,
                          flux_val, absflux_val, min_x, min_y, max_x, max_y, int(n))
            stats = StatStruct(stat_tuple)
            if max_iter is not None and threshold is not None:
                stats.iterations = iter
                if max_iter:
                    stats.convergence = 1
                else:
                    stats.convergence = 0
            return stats
        else:
            raise DARMAError('Empty data array!')

    def get_mean(self, filter=False):
        '''
           Return the mean value of this image.
        '''

        return mean(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                    filter=filter)

    def get_median(self, sorted=False, filter=False):
        '''
           Return the median value of this image.

           sorted: is the data already sorted
        '''

        return median(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                      sorted=sorted, filter=filter)

    def get_stdev(self, filter=False):
        '''
           Return the sample standard deviation value of this image.
        '''

        return stdev(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                     filter=filter)

    def get_rms(self, filter=False):
        '''
           Return the rms (root mean square) value of this image.
        '''

        return rms(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                   filter=filter)

    def get_min(self, filter=False):
        '''
           Return the minumum value of this image.
        '''

        return min(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                   filter=filter)

    def get_max(self, filter=False):
        '''
           Return the maximum value of this image.
        '''

        return max(self.data, self.bmask.as_pixelmap(mask=2**self.bit).data,
                   filter=filter)

    def thresh_to_pixmap(self, lo_cut=None, hi_cut=None):
        '''
           Produce a pixelmap mapping pixels with values between low_cut and
           hi_cut.
        '''

        if lo_cut is not None:
            masklo = self.data > lo_cut
        else:
            masklo = self.as_pixelmap()
            masklo.set_val(1)
        if hi_cut is not None:
            maskhi = self.data < hi_cut
        else:
            maskhi = self.as_pixelmap()
            maskhi.set_val(1)
        bit = self.bit
        if not self.bmask.has_bit(bit=bit):
            pmap = pixelmap(data=Array.isfinite(self.data))
            self.bmask.add_pixelmap(pmap=pmap, bit=bit)
        if not self.bmask.has_bit(bit=bit):
            return pixelmap(data=masklo & maskhi)
        else:
            data = masklo & maskhi & self.bmask.as_pixelmap(mask=2**bit).data
            return pixelmap(data=data)

    #################################################################
    #
    # image producing operations
    #

    def clean_bad_pixels(self, pixmap, boxsize):
        '''
           Interpolate the bad pixels in an image.

            pixmap: A pixelmap (good=1, bad=0)
           boxsize: width of interpolation region

           NOTE: THIS METHOD CURRENTLY DOES NOT WORK!
        '''

        # XXX FIXME
        newdata = self.data.copy()
        badpixlist = (~pixmap).data.nonzero()

        data = Array.empty(shape=self.data.shape, dtype='complex64')
        data.real = self.data
        data.imag = pixmap.data

        def clean(pixels):
            data = pixels.real
            pmap = pixels.imag

        return image(data=newdata)

    def mirror_edges(self, xedge, yedge):
        '''
           Mirror the edges of the image to create a new image

           xedge: The size of the sides to be mirrored
           yedge: The size of the top/bottom to be mirrored
        '''

        xsize = self.xsize()
        ysize = self.ysize()

        wide = self.__class__(data=Array.zeros(shape=(self.ysize(),
                                                      self.xsize() + 2 * xedge), dtype=self.datatype))
        tall = self.__class__(data=Array.zeros(shape=(self.ysize() + 2 * yedge,
                                                      self.xsize() + 2 * xedge), dtype=self.datatype))

        wide[:xedge, :] = self[:xedge, :][::-1, :]
        wide[xedge + 1:-xedge - 1, :] = self[:, :]
        wide[-xedge:, :] = self[-xedge:, :][::-1, :]
        tall[:, :yedge] = wide[:, :yedge][:, ::-1]
        tall[:, yedge + 1:-yedge - 1] = wide[:, :]
        tall[:,          -yedge:] = wide[:, -yedge:][:, ::-1]

        del wide
        return tall

    def subtract_oscan_rows(self, x0, x1, zone=None, smooth=0):
        '''
           Subtract mean of overscan rows.

           x0, x1: start and end column of overscan region
           zone: a tuple defining the zone to subtract mean from in
                 (x0, y0, x1, y1) form
           smooth: size of rectangular box smoothing function
        '''

        # Take overscan region.
        if zone is not None:
            y0, y1 = zone[1], zone[3]
            oscan_image = self[x0:x1, y0:y1]
        else:
            oscan_image = self[x0:x1, :]
        # Average along the X-axis.
        oscan_data = Array.add.reduce(oscan_image.data, 1) / (x1 - x0 + 1)
        if smooth:
            oscan_data = uniform_filter1d(oscan_data, smooth)
        # Prepare 1-D overscan image for subtraction.
        oscan_image = image(data=oscan_data)
        oscan_image.reshape((1, oscan_image.size))
        if zone is not None:
            x0, y0, x1, y1 = zone
            sub_image = self[x0:x1, y0:y1] - oscan_image
            self[x0:x1, y0:y1] = sub_image
            return self
        self -= oscan_image
        return self

    def subtract_oscan_columns(self, y0, y1, zone, smooth=0):
        '''
           Subtract mean of overscan columns.

           y0, y1: start and end row of overscan region
           zone: a tuple defining the zone to subtract mean from in
                 (x0, y0, x1, y1) form
           smooth: size of rectangular box smoothing function
        '''

        # Take overscan region.
        if zone is not None:
            x0, x1 = zone[0], zone[2]
            oscan_image = self[x0:x1, y0:y1]
        else:
            oscan_image = self[:, y0:y1]
        # Average along the X-axis.
        oscan_data = Array.add.reduce(oscan_image.data, 0) / (y1 - y0 + 1)
        if smooth:
            oscan_data = uniform_filter1d(oscan_data, smooth)
        # Prepare 1-D overscan image for subtraction.
        oscan_image = image(data=oscan_data)
        oscan_image.reshape((oscan_image.size, 1))
        if zone is not None:
            x0, y0, x1, y1 = zone
            sub_image = self[x0:x1, y0:y1] - oscan_image
            self[x0:x1, y0:y1] = sub_image
            return self
        self -= oscan_image
        return self

#    filters = {'mean3':    [1.0]*9,
#               'mean5':    [1.0]*25,
#               'dx':       [-1.0, 0.0, 1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 1.0],
#               'dy':       [-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
#               'dx2':      [1.0, -2.0, 1.0, 1.0, -2.0, 1.0, 1.0, -2.0, 1.0],
#               'dy2':      [1.0, 1.0, 1.0, -2.0, -2.0, -2.0, 1.0, 1.0, 1.0],
#               'contour1': [1.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0],
#               'contour2': [-1.0, 0.0, 1.0, 2.0, 0.0, -2.0, -1.0, 0.0, 1.0],
#               'contour3': [-1.0, -2.0, -1.0, 0.0, 0.0, 0.0, 1.0, -2.0, 1.0],
#               'contrast1':[1.0]*4+[4.0]+[1.0]*4}

    def _apply_filter(self, filtername):
        '''
           Unimplemented
        '''

#        '''Return a new image produced by applying a named filter'''
#        result = image()
#        filter = self.filters[filtername]
#        if len(filter) == 9:
#            result.p_ima = c_eclipse.image_filter3x3(self.p_ima, filter)
#        else:
#            result.p_ima = c_eclipse.image_filter5x5(self.p_ima, filter)
#        result.pcheck('Error applying filter %s' % filtername)
#        return result

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_mean(self, xsize=3, ysize=3):
        '''
           Unimplemented
        '''

#        '''Return a mean filtered image over a rectangular kernel
#
#        Arguments:
#        xsize -- width of filter (default=3)
#        ysize -- height of filter (default=3)
#        '''
#        if xsize==3 and ysize==3:
#            return self._apply_filter('mean3')
#        if xsize==5 and ysize==5:
#            return self._apply_filter('mean5')
#
#        result = image()
#        result.p_ima = c_eclipse.image_rectangle_filter_flat(self.p_ima,
#                                                             xsize, ysize)
#        result.pcheck('Error applying filter')
#        return result

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_median(self, xsize=3, ysize=3):
        '''
           Unimplemented
        '''

#        '''Do a median filtering over a rectangular area
#
#        Arguments:
#        xsize -- width of filter (default=3)
#        ysize -- height of filter (default=3)
#        '''
#        result = image()
#        if xsize==3 and ysize==3:
#            result.p_ima = c_eclipse.image_filter_median(self.p_ima)
#        else:
#            result.p_ima = c_eclipse.image_filter_large_median(self.p_ima,
#                                                                xsize,
#                                                                ysize)
#        result.pcheck('Error applying median filter')
#        return result

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_dx(self):
        '''
           Unimplemented
        '''

#        '''First derivative in x, convolve with a kernel
#        -1 0 1
#        -1 0 1
#        -1 0 1
#        '''
#        return self._apply_filter('dx')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_dy(self):
        '''
           Unimplemented
        '''

#        '''First derivative in y, convolve with a kernel
#        -1 -1 -1
#         0  0  0
#         1  1  1
#        '''
#        return self._apply_filter('dy')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_dx2(self):
        '''
           Unimplemented
        '''

#        '''Second derivative in x, convolve with a kernel
#        1 -2 1
#        1 -2 1
#        1 -2 1
#        '''
#        return self._apply_filter('dx2')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_dy2(self):
        '''
           Unimplemented
        '''

#        '''Second derivative in y, convolve with a kernel
#         1  1  1
#        -2 -2 -2
#         1  1  1
#        '''
#        return self._apply_filter('dy2')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_contour1(self):
        '''
           Unimplemented
        '''

#        '''Convolve with a kernel
#         1  0 -1
#         0  0  0
#        -1  0  1
#        '''
#        return self._apply_filter('contour1')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_contour2(self):
        '''
           Unimplemented
        '''

#        '''Convolve with a kernel
#        -1  0  1
#         2  0 -2
#        -1  0  1
#        '''
#        return self._apply_filter('contour2')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_contour3(self):
        '''
           Unimplemented
        '''

#        '''Convolve with a kernel
#        -1  2 -1
#         0  0  0
#         1 -2  1
#        '''
#        return self._apply_filter('contour3')

        print('WARNING - This method is not yet implemented!')
        return None

    def filter_contrast1(self):
        '''
           Unimplemented
        '''

#        '''Convolve with a kernel
#         1  1  1
#         1  4  1
#         1  1  1
#        '''
#        return self._apply_filter('contrast1')

        print('WARNING - This method is not yet implemented!')
        return None

    def hough_transform(self, threshold):
        """
           Make a Hough transform of the image.
        """

        xsize = self.data.shape[0]
        ysize = self.data.shape[1]
        sdata = self.data
        floor = math.floor
        # Get output array sizes and scales.
        drho = 1.0 / math.sqrt(2.0)
        nrho = int(math.sqrt(xsize**2 + ysize**2) / drho) + 1
        ntheta = 1800
        dtheta = math.pi / ntheta
        # Initialize Hough image.
        hough = make_image(nrho, ntheta)
        hdata = hough.data
        # Precompute sin(angle), cos(angle).

        def sin(theta):
            return Array.sin((theta + 0.5) * dtheta)

        def cos(theta):
            return Array.cos((theta + 0.5) * dtheta)
        #sins = apply(sin, tuple(Array.indices([ntheta], dtype=self.datatype)))
        #coss = apply(cos, tuple(Array.indices([ntheta], dtype=self.datatype)))
        sins = Array.fromfunction(sin, [ntheta])
        coss = Array.fromfunction(cos, [ntheta])

        # Do the transform.
        for j in range(ysize):
            for i in range(xsize):
                if (sdata[i, j] > threshold):
                    # Eclipse axes are swapped?
                    x = Array.array(float(j), dtype=self.datatype)
                    y = Array.array(float(i), dtype=self.datatype)
                    for k in range(ntheta):
                        l = int(floor((x * coss[k] + y * sins[k]) / drho))
                        hdata[k, l] += 1.0

        #import itertools
        # def transform(x,y):
        #    if self.data[x, y] > threshold:
        #        x = Array.array(float(y), dtype=self.datatype)
        #        y = Array.array(float(x), dtype=self.datatype)
        #        for k in range(ntheta):
        #            l = int(math.floor((x * coss[k] + y * sins[k]) / drho))
        #            hough.data[k,l] += 1.0
        #itertools.imap(transform, range(xsize), range(ysize))

        return hough

        #pmap = self.thresh_to_pixmap(threshold)

        # def transform(nrho, ntheta):
        #    result = 0
        #    # PyFITS Array axes are reversed.
        #    for x in range(self.ysize()):
        #        for y in range(self.xsize()):
        #            if self.data[x, y] > threshold:
        #                if x * coss[ntheta] + y * sins[ntheta] == nrho:
        #                    result += 1
        #    return result
        # return Array.fromfunction(transform, [nrho, ntheta])

    def inverse_hough_transform(self, threshold, lx, ly):
        '''
           Make an Inverse Hough transform of the image.

           Unimplemented
        '''

        #result = pixelmap()
        # result.p_pmap = c_eclipse.hough_transform_to_pixelmap(self.p_ima,
        #                                                      threshold,
        #                                                      lx, ly)
        # if result.p_pmap is None:
        #    raise DARMAError, 'Error thresholding'
        # return result

        print('WARNING - This method is not yet implemented!')
        return None

    ##################################################################
    #
    # In-place operations

    def normalize_mean(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):
        '''
           Normalize the image to a mean of 1.0.

           The mean can be computed in a restricted area. This function
           modifies the image in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [xmin, ymin, xmax, ymax]
              scale: normalize to a different scale (default=1.0)
        '''

        if (pixmap is None) and (pixrange is None) and (zone is None):
            mean = self.get_mean(filter=False)
        else:
            stats = self.stat_opts(pixmap, pixrange, zone, domedian=0)
            mean = stats.avg_pix

        self *= scale / mean

    def normalize_median(self, pixmap=None, pixrange=None, zone=None,
                         scale=1.0):
        '''
           Normalize the image to a median of 1.0.

           The median can be computed in a restricted area. This function
           modifies the image in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [xmin, ymin, xmax, ymax]
              scale: normalize to a different scale (default=1.0)
        '''

        if (pixmap is None) and (pixrange is None) and (zone is None):
            median = self.get_median(filter=False)
        else:
            stats = self.stat_opts(pixmap, pixrange, zone, domedian=1)
            median = stats.median

        self *= scale / median

    def normalize_flux(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):
        '''
           Normalize the image to a flux of 1.0.

           The flux can be computed in a restricted area. This function
           modifies the image in-place

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [xmin, ymin, xmax, ymax]
              scale: normalize to a different scale (default=1.0)
        '''

        if (pixmap is None) and (pixrange is None) and (zone is None):
            stats = self.stat(domedian=0)
        else:
            stats = self.stat_opts(pixmap, pixrange, zone, domedian=0)

        self *= scale / stats.flux

    def normalize_range(self, pixmap=None, pixrange=None, zone=None,
                        scale=1.0):
        '''
           Normalize the image to a range of values between 0.0 and 1.0.

           The range can be computed in a restricted area. This function
           modifies the image in-place

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [xmin, ymin, xmax, ymax]
              scale: normalize to a different scale (default=1.0)
        '''

        if (pixmap is None) and (pixrange is None) and (zone is None):
            stats = self.stat(domedian=0)
        else:
            stats = self.stat_opts(pixmap, pixrange, zone, domedian=0)

        gain = stats.max_pix - stats.min_pix
        self -= stats.min_pix
        self *= scale / gain

    def normalize_absolute_flux(self, pixmap=None, pixrange=None,
                                zone=None, scale=1.0):
        '''
           Normalize the image to an absolute flux of 1.0.

           The absolute flux can be computed in a restricted area. This
           function modifies the image in-place

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [xmin, ymin, xmax, ymax]
              scale: normalize to a different scale (default=1.0)
        '''

        if (pixmap is None) and (pixrange is None) and (zone is None):
            stats = self.stat(domedian=0)
        else:
            stats = self.stat_opts(pixmap, pixrange, zone, domedian=0)

        self *= scale / stats.absflux

    # QC tools and utilities

    def run_signtest(self, nwx, nwy, Threshold=5):

        return None, None

        '''
           Quality control tool for Bias.

           The algorithm splits the input frame in a number of subwindows
           (parameter in input) and then counts, for each, the elements
           greaters of median frame value; if this number is not out of
           binomial distribution, then the subwindow is flagged. Finaly
           the number of bad windows is compared with the teorical number
           of windows expected; the quality index, then is defined as
           (N_BAD-N_EXPECTED)/sigma

           Arguments

           nwx - number of subwindows in x
           nwy - number of subwindows in y
           Threshold
           --

           Returns a quality index.

           Unimplemented
        '''

        #result   =  image()
        #result.p_ima = c_eclipse.image_new(nwx, nwy);
        # qualityIndex = c_eclipse.image_signtest(self.p_ima, result.p_ima,
        #                                        nwx, nwy, Threshold)
        # return result,qualityIndex

        print('WARNING - This method is not yet implemented!')
        return None, None

    def run_flattest(self, nwx, nwy):
        '''
           Quality control tool for Dome.

           This test works an flat-fielded images.

           The image is normalised by its median value.The medians of a
           number of sub-windows of the normalized image are determined.
           The minimum median is subtracted from the maximum median and
           the result is given as output.

           Arguments

           nwx - number of subwindows in x
           nwy - number of subwindows in y

           Returns a quality index.

           Unimplemented
        '''

        #result   =  image()
        #result.p_ima = c_eclipse.image_new(nwx,nwy);
        #qualityIndex = c_eclipse.image_flattest(self.p_ima,result.p_ima,nwx,nwy)
        # return result,qualityIndex

        print('WARNING - This method is not yet implemented!')
        return None, None

    def run_flatfittingtest(self, nwx, nwy, nfwx, nfwy):
        '''
           Quality control tool for Twilight.

           It can be used on flat images to see if there is a gradient,
           works in two steps, before use the bicubic spline
           interpolation to produce an image and after split this image
           in a number of subwindows; then for each subwindows compute
           the root means square and return the max rms value.

           Arguments

           nwx  - number of subwindows in x
           nwy  - number of subwindows in y
           nfwx - number of subwindows in x for fitting
           nfwy - number of subwindows in y for fitting

           Returns a quality index.

           Unimplemented
        '''

        #imsurfit = image()
        #imsurfit.p_ima = c_eclipse.image_surfit(self.p_ima,nfwx,nfwy)
        #result   = image()
        #result.p_ima = c_eclipse.image_new(nwx,nwy);
        # qualityIndex = c_eclipse.image_flattest(imsurfit.p_ima,
        #                                        result.p_ima,nwx,nwy)
        # return result,qualityIndex

        print('WARNING - This method is not yet implemented!')
        return None, None

    def run_counttest(self, Threshold):
        '''
           Unimplemented
        '''

#        '''Quality control tool
#
#        This test is useful the see the number of pixel out a fixed
#        threshold. It can produce two different output: the sum of all
#        pixel out the threshold or simple the number; morover produce
#        a flag image of pixel out the range.
#
#        Arguments
#
#        Threshold
#
#
#        Returns a quality index.'''
#
#        sum=0
#        result = self.copy()
#        qualityIndex = c_eclipse.image_count_threshold_withoutBPM(self.p_ima,result.p_ima,Threshold,sum)
#        return qualityIndex

        print('WARNING - This method is not yet implemented!')
        return None

    def run_imsurfit(self, nwx, nwy):
        '''
           Unimplemented
        '''

#        '''Tool for fitting surface
#
#        The common technique for obtaining smoothness in
#        two-dimensional interpolation is the bicubic spline.
#        Actually, this is equivalent to a special case of bicubic
#        interpolation: Bicubic splines are usually implemented in a
#        form that looks rather different from the above bicubic
#        interpolation routines: To interpolate one functional value,
#        one performs m one-dimensional splines across the rows of the
#        table, followed by one additional one-dimensional spline down
#        the newly created column. It is a matter of taste (and
#        trade-off between time and memory) as to how much of this
#        process one wants to precompute and store. Instead of
#        precomputing and storing all the derivative information (as in
#        bicubic interpolation), spline users typically precompute and
#        store only one auxiliary table, of second derivatives in one
#        direction only. Then one need only do spline evaluations (not
#        constructions) for the m row splines; one must still do a
#        construction and an evaluation for the final column spline
#
#        Arguments
#
#        nwx - number of subwindows in x for fitting
#        nwy - number of subwindows in y for fitting
#
#        Returns a surface fitting image.'''
#
#        imsurfit = image()
#        imsurfit.p_ima = c_eclipse.image_surfit(self.p_ima,nwx,nwy)
#        return imsurfit

        print('WARNING - This method is not yet implemented!')
        return None

    def threshold(self, lv, hv, sl, sh):
        '''
           Unimplemented
        '''

#        '''
#        This tool takes all pixels major than hl and assign them the value sh, then
#        it takes all pixels less than lv and assign them the value sl.
#
#        Arguments
#
#        lv - low  value
#        hv - high value
#        sl - low  new value
#        sh - high new value
#
#        '''
#        result = image()
#        result.p_ima = c_eclipse.image_threshold(self.p_ima,lv, hv, sl, sh)
#        return result

        print('WARNING - This method is not yet implemented!')
        return None


def convert(filename, bitpix=16):
    '''
       Convert data contained in filename to datatype bitpix.  The file
       can be a single- or multi-extension FITS image.

         filename: name of FITS file to convert
           bitpix: BITPIX to convert data to (one of 8, 16, 32, -32, -64)

       WARNING: This function is not completely robust for data whose
                range is greater than 2**|bitpix| ADU and is primarily
                intended to overcome PyFITS insistance to use a float
                representation for all data, even when saving.
    '''

    bpmap = {
        8:   'uint8',
        16:   'int16',
        32:   'int32',
        -32: 'float32',
        -64: 'float64',
    }
    # incorrect/unsupported bitpix value
    if bitpix not in bpmap:
        raise DARMAError('Unsupported bitpix value!  Must be one of %s' % list(bpmap.keys()))
    # open HDUList
    with fits_open(filename, mode='update', memmap=True) as hdus:
        if len(hdus) == 1:
            # SEF
            hdulist = hdus
        else:
            # MEF
            hdulist = hdus[1:]
        for hdu in hdulist:
            # nothing to do
            if hdu.header['BITPIX'] == bitpix:
                continue
            # integer data must be scaled if dynamic range too great
            if bitpix > 0:
                print('Converting data in %s' % hdu.name)
                # default values
                bzero = 2.**(bitpix - 1)
                bscale = 1.0
                # check the dynamic range (flat the shape temporarily to save memory)
                dims = hdu.data.shape
                hdu.data.shape = hdu.data.size
                min = Array.minimum.reduce(hdu.data)
                max = Array.maximum.reduce(hdu.data)
                hdu.data.shape = dims
                # adjust for negative values
                if min < 0:
                    bzero += min
                # scaling check
                if max - min > 2**bitpix - 1:
                    bscale = (max - min) / (2.**bitpix - 1)
                # shift and scale data and add values to header
                hdu.data += -bzero  # to avoid out of range error for BZERO = +32768a
                if bscale != 1.0:
                    hdu.data /= bscale
                update_header(hdu.header, 'BZERO', bzero, comment='physical=stored*BSCALE+BZERO', after='NAXIS2')
                update_header(hdu.header, 'BSCALE', bscale, comment='physical=stored*BSCALE+BZERO', after='NAXIS2')
                # convert to new datatype
                hdu.data = Array.array(Array.around(hdu.data), dtype=bpmap[bitpix])
                hdu.header['BITPIX'] = bitpix
            # don't scale data for floats (ever?)
            if bitpix < 0:
                pass
    # XXX PyFITS/Astropy have a bug in Python 3 that corrupts larger FITS
    # XXX files upon writing when opened in 'update' mode and the file
    # XXX size changes.  Write a new file to work around this bug.
    hdus.writeto(filename+'.new', output_verify='fix')
    os.remove(filename)
    os.rename(filename+'.new', filename)

##########################################################################
#
# Functions generating images
#


def make_image(xsize, ysize, datatype=FLOAT, value=None):
    """
       Generate a new image.

       xsize   : the X dimension of the image
       ysize   : the Y dimension of the image
       value   : optional value to initialize pixel values to
       datatype: type of the image pixel data

       NOTE: Associated data array is zero initialized.
    """

    # Allow DARMA to be imported even if NumPy is not available.
    if not _HAS_NUMPY:
        raise DARMAError('DARMA pixel functionality not possible: cannot import module numpy')

    if not(xsize > 0 and ysize > 0):
        raise DARMAError('Invalid image dimesions')

    # PyFITS Array axes are reversed.
    ima = image(data=Array.zeros((ysize, xsize), dtype=datatype), datatype=datatype)
    if value is not None:
        ima.data.fill(value)
    return ima


def fft(real, imaginary=None, direction=-1):
    '''
       Do a Fast Fourier Transorm (not currently using FFTW)

            real: An image containing the real values
       imaginary: An image containing the imaginary values (default=None)
       direction: -1 (forward) or 1 (inverse)

       Returns a tuple of images representing the real and imaginary part
       of the fourier transformed data.
    '''

    # XXX optimize for precision

    if imaginary is None:
        data = real.data
    else:
        data = Array.empty(shape=(real.data.shape), dtype='complex64')
        data.real = real.data
        data.imag = imaginary.data

    if direction == -1:
        new = Arrayfft.fft2(data)
    if direction == 1:
        new = Arrayfft.ifft2(data)
    data = None

    return image(data=new.real), image(data=new.imag)


def mean(data, nanmask=None, filter=False):
    '''
       Return the mean of a sequence of the dataset data.  All members of the
       input array are considered regardless of array rank (number of
       dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # Return a ravel()ed array.
    _data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    if _data.size:
        return _data.mean(dtype='float64')
    else:
        raise DARMAError('Empty data array!')


def median(data, nanmask=None, sorted=False, filter=False):
    '''
       Return the median of the dataset data.  All members of the input array
       are considered regardless of array rank (number of dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        sorted: the input data array is already sorted
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # XXX use buitlin function?

    # Return a ravel()ed array.
    _data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    n = _data.size
    if n:
        if not sorted:
            _data = _data.copy()
            _data.sort()
        if n % 2:
            return _data[n / 2]
        else:
            return (_data[n / 2] + _data[n / 2 - 1]) / 2.0
    else:
        raise DARMAError('Empty data array!')


def stdev(data, nanmask=None, filter=False):
    '''
       Return the sample standard deviation of a the dataset data.  All members
       of the input array are considered regardless of array rank (number of
       dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # Return a ravel()ed array.
    _data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    n = _data.size * 1.0
    if n:
        sum_val = _data.sum(dtype='float64')
        return math.sqrt(((_data**2).sum(dtype='float64') - ((sum_val**2) / n)) / (n - 1.0))
    else:
        raise DARMAError('Empty data array!')


def rms(data, nanmask=None, filter=False):
    '''
       Return the root-mean-square (RMS) of the values of the dataset data.
       All members of the input array are considered regardless of array rank
       (number of dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # Return a ravel()ed array.
    _data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    n = _data.size * 1.0
    if n:
        return math.sqrt((_data**2).sum(dtype='float64') / n)
    else:
        raise DARMAError('Empty data array!')


def min(data, nanmask=None, filter=False):
    '''
       Return the minimum value of teh dataset data.  All members of the input
       array are considered regardless of array rank (number of dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # Return a ravel()ed array.
    data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    n = data.size
    if n:
        return data.min()
    else:
        raise DARMAError('Empty data array!')


def max(data, nanmask=None, filter=False):
    '''
       Return the maximum value of the dataset data.  All members of the input
       array are considered regardless of array rank (number of dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    # Return a ravel()ed array.
    data = filter_nonnumbers(data=data, nanmask=nanmask, filter=filter)
    n = data.size
    if n:
        return data.max()
    else:
        raise DARMAError('Empty data array!')


def filter_nonnumbers(data, nanmask=None, filter=False):
    '''Returns a 1-dimensional array with non-numbers (NaN, Inf, etc.)
       filtered out.  All members of the input array are considered
       regardless of array rank (number of dimensions).

          data: input data array of arbitrary rank
       nanmask: a pixel mask where finite pixel values in data are 1
        filter: filter out non-numbers (NaN, Inf, etc.)
    '''

    _data = data.ravel()
    if filter and nanmask is None:
        mask = Array.isfinite(_data)
    elif nanmask is not None:
        mask = nanmask
    else:
        return _data
    mask = mask.ravel()
    if mask.all():
        return _data
    else:
        return _data.compress(mask)


def uniform_filter1d(array, filter_size, mode=None, copy=False):
    '''
       Filter data in a one dimmensional array, in place, averaging over
       2*filtersize+1.

               array: input Array object
         filter_size: filter box = 2*filter_size+1
                mode: mode of the endpoints treatment
                copy: modify and return a copy of array

       The only current endpoint treatment modes are "reflect" and None.
       Only one dimensional arrays are supported at this time.
    '''

    #modes = ['nearest', 'wrap', 'reflect', 'constant']
    modes = ['reflect']

    if len(array.shape) != 1:
        raise DARMAError('uniform_filter1d only supports arrays of one dimension!')

    if copy:
        copy = array.copy()
    else:
        copy = array

    if mode in modes:

        buffer = Array.empty(shape=(copy.size + 2 * filter_size,), dtype=copy.dtype)

        # Treat boundries by reflecting the endpoints.
        if mode == 'reflect':
            buffer[:filter_size] = copy[filter_size:0:-1]
            buffer[filter_size:-filter_size] = copy
            buffer[-filter_size:] = copy[-2:-(filter_size + 2):-1]

        for i in range(copy.size):
            # buffer.size = copy.size+2*filter_size
            copy[i] = buffer[i:i + 2 * filter_size + 1].mean(dtype='float64')

    else:

        buffer = Array.empty(shape=copy.shape, dtype=copy.dtype)

        # Don't treat boundries at all.  Shrink smoothing box at ends.
        for i in range(copy.size):
            minj = Array.max([0, i - filter_size])
            maxj = Array.min([copy.size - 1, i + filter_size]) + 1
            buffer[i] = copy[[j for j in range(minj, maxj)]].mean(dtype='float64')
        copy = buffer

    return copy
