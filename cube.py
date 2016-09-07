'''
   A list of images or pixelmaps with methods that process stacks of them.
'''

__version__ = '@(#)$Revision$'

import os

from .common import fits, DataStruct, Array, FLOAT, INT, fits_open
from .common import DARMAError, _HAS_NUMPY, _datamd5, _update_datamd5
from .image import image
from .pixelmap import pixelmap


class cube(DataStruct):

    '''
       cubes are stacks of images or pixelmaps (3-dimensional arrays) that can
       be manipulated in similar fashions to images or pixelmaps.  Normal
       arithmetic (addition, subtraction, multiplication, division, etc.) is
       performed on all members of the stack in turn (i1*constant, i2*constant,
       etc.), but other operations, such as statistics, are performed on sets
       of pixels in the `z' direction of the stack.

       It is assumed that all members of a cube are the same shape, type, and
       datatype.

       The functionality of a cube is very similar to that of an image or a
       pixelmap, except that the operations are typically broadcasted over all
       planes of the cube, while others condense the members of the cube to an
       image or a pixelmap.
    '''

    def __init__(self, filename=None, extension=0, data=None, image_list=None,
                 index=0, readonly=0, memmap=1, datatype=FLOAT, *args,
                 **kwargs):
        '''
             filename: The name of a FITS file the cube can be loaded from
            extension: A FITS extension number
                 data: A 3-dim numeric Python array (i.e., NumPy array)
           image_list: A list of images or pixelmaps
                index: Which cube to take if data is 4-dimensional (e.g., a
                       radio cube with polarization)
             readonly: Indicate that the FITS file is readonly
               memmap: Use memory mapping
        '''

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError('DARMA pixel functionality not possible: cannot import module numpy')

        self.filename = filename or None
        self.extension = extension
        self._data = data
        self.image_list = image_list
        self.index = index
        self.readonly = readonly
        self.memmap = memmap
        self._datatype = datatype

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError('Filename: %s not found!' % self.filename)

    def load(self):
        '''
           Proxy for load_cube()
        '''

        self.load_cube()

    def load_cube(self):
        '''
           Load the images from a file, data or from the given image_list.
        '''

        # FIXME Add datatype conversion here.

        if self._data is None:

            filename = self.filename
            extension = self.extension
            data = self._data
            image_list = self.image_list
            index = self.index
            readonly = self.readonly
            memmap = self.memmap
            if filename is not None:
                try:
                    #_data = fits.getdata(filename, extension)
                    _data = fits_open(filename, memmap=memmap)[extension].data
                except Exception as e:
                    raise DARMAError('Unable to load data from %s : %s' % (filename, e))
            elif data:
                _data = data
                del data
            elif image_list:
                _data = Array.concatenate([ima.data for ima in image_list]).reshape(
                    len(image_list), ima.data.shape[0], ima.data.shape[1])
            else:
                _data = None
            if _data is not None:
                shape = _data.shape
                if len(shape) == 1:
                    _data = _data.reshape(1, 1, shape[0])
                elif len(shape) == 2:
                    _data = _data.reshape(1, shape[0], shape[1])
                elif len(shape) == 3:
                    pass
                elif len(shape) == 4:
                    _data = _data[index]
                else:
                    raise DARMAError('Cubes with %d dimensions are not supported!' % len(shape))
            self._data = _data

    def as_image_list(self):
        '''
           Return a list of individual image objects, each corresponding to
           planes in the data cube.  This replicates the way Eclipse stored
           cube data.
        '''

        return [image(data=plane) for plane in self.data]

    def as_pixelmap_list(self):
        '''
           Return a list of individual pixelmap objects, each corresponding
           to planes in the data cube.  This replicates the way Eclipse
           stored cube data.
        '''

        return [pixelmap(data=plane.data) for plane in self.data]

    def copy(self):
        '''
           Copy the data to a new object.
        '''

        return cube(data=self.data)

    def save(self, filename=None, hdr=None, extension=None,
             datatype='float32', clobber=True, update_datamd5=True):
        '''
           Save the data to a file.

                 filename: name of the file
                      hdr: image header (header object)
                extension: A FITS extension number
                 datatype: type of data output to the FITS file
                  clobber: overwrite an existing file
           update_datamd5: update (or add) the DATAMD5 header keyword

        '''

        if self.readonly and (filename is None or filename == self.filename):
            raise DARMAError('Saving read-only data')

        if not filename:
            if not self.filename:
                raise DARMAError('Neither filename (%s) nor self.filename (%s) contain a valid file name!' %
                                 (filename, self.filename))
            else:
                filename = self.filename
        else:
            if not self.filename:
                self.filename = filename

        if hasattr(hdr, 'hdr'):
            hdr = hdr.hdr

        if extension is None:
            extension = self.extension

        # Can't save a Bool array to a FITS image.
        if datatype is None and self.datatype == 'bool':
            datatype = 'uint8'

        if not self.data.flags.contiguous:
            self.data = Array.ascontiguousarray(self.data)

        fits.writeto(filename=filename, data=self.data, header=hdr,
                     ext=extension, clobber=clobber)

        if update_datamd5:
            _update_datamd5(filename, _datamd5(filename))

    def __del__(self):
        '''
        '''

        del self

    ########################################################################
    #
    # Introspection
    #

    def xsize(self):
        '''
           The length of the x-axis data of the cube members.
        '''

        return self.data.shape[2]  # PyFITS Array axes are reversed

    def ysize(self):
        '''
           The length of the y-axis data of the cube members.
        '''

        return self.data.shape[1]  # PyFITS Array axes are reversed

    def zsize(self):
        '''
           The length of the z-axis data of the cube members.
        '''

        return self.data.shape[0]  # PyFITS Array axes are reversed

    ##################################################################
    #
    # In-place operations
    #

    def normalize_mean(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):
        '''
           Normalize each plane to a mean of 1.0.

           The mean can be computed in a restricted area.  This function
           modifies each plane in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        images = self.as_image_list()
        for ima in images:
            ima.normalize_mean(pixmap=pixmap, pixrange=pixrange, zone=zone,
                               scale=scale)
        self.data = cube(image_list=images).data

    def normalize_median(self, pixmap=None, pixrange=None, zone=None,
                         scale=1.0):
        '''
           Normalize each plane to a median of 1.0.

           The median can be computed in a restricted area.  This function
           modifies each plane in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        images = self.as_image_list()
        for ima in images:
            ima.normalize_median(pixmap=pixmap, pixrange=pixrange, zone=zone,
                                 scale=scale)
        self.data = cube(image_list=images).data

    def normalize_flux(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):
        '''
           Normalize each plane to a flux of 1.0.

           The flux can be computed in a restricted area.  This function
           modifies each plane in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        images = self.as_image_list()
        for ima in images:
            ima.normalize_flux(pixmap=pixmap, pixrange=pixrange, zone=zone,
                               scale=scale)
        self.data = cube(image_list=images).data

    def normalize_range(self, pixmap=None, pixrange=None, zone=None,
                        scale=1.0):
        '''
           Normalize the images to a range of values between 0.0 and 1.0.

           The range can be computed in a restricted area.  This function
           modifies the image in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different maximum (default=1.0)
        '''

        images = self.as_image_list()
        for ima in images:
            ima.normalize_range(pixmap=pixmap, pixrange=pixrange, zone=zone,
                                scale=scale)
        self.data = cube(image_list=images).data

    def normalize_absolute_flux(self, pixmap=None, pixrange=None,
                                zone=None, scale=1.0):
        '''
           Normalize the images to an absolute flux of 1.0.

           The absolute flux can be computed in a restricted area.  This
           function modifies the image in-place.

             pixmap: map of valid pixelsd (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        images = self.as_image_list()
        for ima in images:
            ima.normalize_absolute_flux(pixmap=pixmap, pixrange=pixrange,
                                        zone=zone, scale=scale)
        self.data = cube(image_list=images).data

    ########################################################################
    #
    # image producing operations
    #

    def sum(self):
        '''
           Sum all images in the cube to a single image.
        '''

        return image(data=self.data.sum(axis=0))

    def average(self):
        '''
           Do a straight average of all images in the cube.
        '''

        return image(data=self.data.mean(axis=0))

    def stdev(self, mean=None):
        '''
           Compute the standard deviation of each pixel in the z direction.

           Arguments:
              mean -- An image to be used for the average (default=None)

           This procedure computes the mean deviation from a mean image.  The
           mean image can be passed as an optional parameter.  If no parameter
           is passed, the mean is computed first.

           Try buffering to improve performance.
        '''

        return image(data=self.data.std(axis=0))

        # XXX retain until performance is checked.
        # if len(self) < 2:
        #    raise DARMAError, 'stdev requires at least two images!'

        # if mean is None:
        #    mean = self.average()

        #stdev = (self[0]-mean)
        #stdev *= stdev
        # for ima in self[1:]:
        #    devima = ima-mean
        #    devima *= devima
        #    stdev += devima
        #    devima = None # force unload

        #stdev /= len(self)
        # return stdev ** 0.5

    # def median(self, buffer_size=256):
    def median(self):
        '''
           Do a median average of all images in the cube.

           buffer_size: number of rows to median at a time (no buffering if
                        buffer_size is 0)

           This method is buffered to reduce memory usage and increase
           performance.
        '''

        # XXX check performance/memory usage

        num = self.data.shape[0]
        if num < 3:
            raise DARMAError('median requires at least three images!')

        return image(data=Array.median(self.data))

        #bsize = int(buffer_size)

        # if bsize == 0:
        #    return image(data=Array.median(self.data))
        # else:
        #    pcube = self.data
        #    result = Array.empty(shape=pcube[0].shape, dtype=pcube[0].dtype)

        #    remain = len(pcube[0])%bsize
        #    length = len(pcube[0])-remain

        #    for i in range(bsize, length+bsize, bsize):
        #        #bcube = Array.concatenate([image[i-bsize:i] for image in pcube])
        #        #bcube = bcube.reshape((num,)+pcube[0][i-bsize:i].shape)
        #        bcube = pcube[:i-bsize:i]
        #        result[i-bsize:i] = Array.median(bcube)
        #    if remain:
        #        #bcube = Array.concatenate([image[i:i+remain] for image in pcube])
        #        #bcube = bcube.reshape((num,)+pcube[0][i:i+remain].shape)
        #        bcube = pcube[:i:i+remain]
        #        result[i:i+remain] = Array.median(bcube)

        #    return self[0].__class__(data=result)

    def average_with_rejection(self, low_reject, high_reject):
        '''
           Unimplemented
        '''

        pass

#        '''
#           Average the planes in the cube.
#
#           low_reject  -- reject pixels lower than this value
#           high_reject -- reject pixels higher than this value
#        '''
#
#        result = image()
#        pcube = self.data
#        result.p_ima = c_eclipse.cube_avg_reject(pcube,
#                                                 low_reject, high_reject)
#        c_eclipse.cube_del_shallow(pcube)
#        result.pcheck('Error in average')
#        return result

    def average_with_sigma_clip(self, n_cycle, nmin, bias, scaling, thresh, badval, rn, gain):
        '''
           Unimplemented
        '''

        pass

#        '''
#           Average with sigma-clipping rejection:
#           Procedure takes in input a cube and run n_cycle times a rejection
#           excluding pixels value large than (thresh*sigma).  Sigma is given
#           by sigma=sqrt((rn/gain)^2 + median/gain).
#
#           Arguments
#             n_cycle  -- number of iterations
#             nmin     -- minimum number of pixels used for final average
#             bias     -- if in input are bias frames then is setted at 1
#             scaling  -- compute the scaling factors internally
#             thresh   -- threshold
#             badval   -- badvalue (not considered)
#             rn       -- Read out noise
#             Gain     -- gain
#
#           Returns an image that contains the sigma-clipped average.
#        '''
#
#
#        flagoutput=0
#
#        #  if sigma is setted at 1 then sigma is the rms
#        sigma=0
#
#        pcube_in = self.data
#        pcube_out = c_eclipse.cube_sigmaclip_withoutBPM(pcube_in,n_cycle,nmin,flagoutput,bias,scaling,sigma,thresh,badval,rn,gain)
#        average = image()
#        average.p_ima = c_eclipse.cube_getplane(pcube_out, 0)
#        c_eclipse.cube_del_shallow(pcube_in)
#        c_eclipse.cube_del_shallow(pcube_out)
#        return average


def average_with_sigma_clip(data_cube, errors, threshold, niter=1):
    '''
       Unimplemented
    '''

    pass

#    """
#       Iteratively compute the mean of images with given errors, rejecting
#       outliers.
#
#       Arguments
#          data_cube -- A cube of images
#          errors    -- A cube of error images, or an array of errors
#          threshold -- The sigma-clipping threshold (default = 5.0)
#          niter     -- The number of iterations (default = 1)
#
#       This algorithm assumes that the errors are given a-priori.
#
#       The algorithm first uses the median of data_cube to estimate the mean,
#       and then computes the mean of the pixels for each data-plane in
#       data_cube for which:
#
#            (data-mean)/error > threshold
#
#       This gives a new estimate of the mean, which can be used to reject
#       additional pixels. This would however normally not be necessary.
#    """
#
#    # Use the median as a first approach. Using the mean would, in the
#    # case of an extreme outlier, result in all pixels deviating from
#    # the 'mean'
#    mean = data_cube.median()
#
#    # The mean can be improved iteratively, although, if the errors
#    # are correct, and outliers have (data-mean)/error >> threshold,
#    # then it is expected that the first pass already rejects all bad
#    # pixels
#    for i in range(niter):
#        deviation = (mean-data_cube[0])/errors[0]
#        sum_good = deviation.thresh_to_pixmap(-threshold, threshold).as_image()
#        sum_data = data_cube[0]*sum_good
#
#        for data, errors in zip(data_cube[1:], errors[1:]):
#            deviation = (mean-data)/error
#            good = deviation.thresh_to_pixmap(-threshold, threshold).as_image()
#            sum_data += data*good
#            sum_good += good
#
#        mean = sum_data/sum_good
#
#    return mean

##########################################################################
#
# Functions generating cubes
#


def make_cube(xsize, ysize, zsize, datatype=FLOAT, value=None):
    """
       Generate a new cube.

       xsize   : the X dimension of the cube
       ysize   : the Y dimension of the cube
       zsize   : the Z dimension of the cube
       value   : optional value to initialize pixel values to
       datatype: type of the image pixel data

       NOTE: Associated data array is zero initialized.
    """

    # Allow DARMA to be imported even if NumPy is not available.
    if not _HAS_NUMPY:
        raise DARMAError('DARMA pixel functionality not possible: cannot import module numpy')

    if not(xsize > 0 and ysize > 0 and zsize > 0):
        raise DARMAError('Invalid image dimensions')

    # PyFITS Array axes are reversed.
    c = cube(data=Array.zeros((zsize, ysize, xsize), dtype=datatype))
    if value is not None:
        c.data.fill(value)
    return c
