'''
   Auxiliary data structures and constants.
'''

__version__ = '@(#)$Revision$'

import math, os, sys
# Python 2 and 3 compatibility
try:
    from __builtin__ import xrange as range
except:
    from builtins import range
if sys.version_info.major < 3:
    # Refer to existing types in Python 2.
    long = long
    unicode = unicode
else:
    class long(int):
        pass

    class unicode(str):
        pass

# Allow DARMA to be imported even if NumPy is not available.
_HAS_NUMPY = True
try:
    import numpy as Array
    import numpy.random as Arrayrandom
    import numpy.fft as Arrayfft
    # FIXME
    #import numpy.nd_image.filters as Arrayfilter
except:
    Arrayrandom = Arrayfft = None
    class ArrayClass():
        __version__ = ''
    Array = ArrayClass()
    _HAS_NUMPY = False

# AstroPy/PyFITS compatibility
_HAS_ASTROPY = False
_HAS_PYFITS33 = False
_HAS_PYFITS = False
try:
    if 'DARMA_PYFITS' in os.environ:
        raise Exception()
    from astropy.io import fits
    from astropy import __version__
    fits.__version__ = __version__
    if __version__ >= u'0.4':
        _HAS_ASTROPY = True
    else:
        raise Exception()
    print('DARMA using Astropy version %s and NumPy version %s' % (fits.__version__, Array.__version__))
except:
    try:
        import pyfits as fits
        if fits.__version__ >= '3.3':
            _HAS_PYFITS33 = True
            _HAS_PYFITS = True
        else:
            _HAS_PYFITS = True
        print('DARMA using PyFITS version %s and NumPy version %s' % (fits.__version__, Array.__version__))
    except:
        pass
if not _HAS_ASTROPY and not _HAS_PYFITS:
    raise ImportError('Cannot import either AstroPy or PyFITS!')

# default data types
FLOAT = 'float32'
INT   = 'int64'

# log levels
NONE    = 0
NORMAL  = 1 << 0
VERBOSE = 1 << 1
DEBUG   = 1 << 2

loglevel = {
            'none'    : NONE,
            'normal'  : NORMAL,
            'verbose' : NORMAL+VERBOSE,
            'debug'   : NORMAL+VERBOSE+DEBUG
           }

class DARMAError(Exception):

    pass

class StatStruct:

    '''
       A class to hold image statistics.

       Each instance has the following attributes
       min_pix: The minimum value
       max_pix: The maximum value
       avg_pix: The average value
        median: The median value
         stdev: The standard deviation
        energy: The total energy
          flux: The total flux
       absflux: The total absolute flux
         min_x: The x-coordinate of the minimum value
         min_y: The y-coordinate of the minimum value
         max_x: The x-coordinate of the maximum value
         max_y: The y-coordinate of the maximum value
          npix: The total number of pixels
    '''

    def __init__(self, stat_tuple):

        '''
           Just assign the values.
        '''

        self.min_pix = stat_tuple[ 0]
        self.max_pix = stat_tuple[ 1]
        self.avg_pix = stat_tuple[ 2]
        self.median  = stat_tuple[ 3]
        self.stdev   = stat_tuple[ 4]
        self.energy  = stat_tuple[ 5]
        self.flux    = stat_tuple[ 6]
        self.absflux = stat_tuple[ 7]
        self.min_x   = stat_tuple[ 8]
        self.min_y   = stat_tuple[ 9]
        self.max_x   = stat_tuple[10]
        self.max_y   = stat_tuple[11]
        self.npix    = stat_tuple[12]

    def show(self):

        '''
           Print out all statistics values.
        '''

        print('min_pix: %s' % self.min_pix)
        print('max_pix: %s' % self.max_pix)
        print('avg_pix: %s' % self.avg_pix)
        print('median : %s' % self.median)
        print('stdev  : %s' % self.stdev)
        print('energy : %s' % self.energy)
        print('flux   : %s' % self.flux)
        print('absflux: %s' % self.absflux)
        print('min_x  : %s' % self.min_x)
        print('min_y  : %s' % self.min_y)
        print('max_x  : %s' % self.max_x)
        print('max_y  : %s' % self.max_y)
        print('npix   : %s' % self.npix)

    def dump(self):

        '''
           Synonym for show().
        '''

        self.show()

class DataStruct(object):

    '''
       Abstract base class for image and pixelmap classes containing common
       methods (mainly arithmetic).
    '''

    verbose = NONE

    def __init__(self, *args, **kwargs):

        '''
           Abstract constructor.

           self.data MUST be defined as an Array instance by constructors
           of inherited classes.
        '''

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError('DARMA pixel functionality not possible: cannot import module numpy')
        if 'verbose' in kwargs:
            self.verbose = kwargs['verbose']
        self.log('DataStruct constructor', 'debug')

    def log(self, msg, level='normal'):

        '''
           Print a log statement

               msg: message to print
             level: level of log entry ('normal', 'verbose', 'debug')
        '''

        verbose = self.verbose
        if verbose in loglevel and level in loglevel:
            if loglevel[verbose] & loglevel[level]:
                print(msg)

    def load(self):

        '''
           Abstract load method.  All sub-classes should call their load_...()
           method from this method.

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self.log('DataStruct data loader', 'debug')
        self._data = None

    def _get_data(self):

        '''
           data 'getter' method
        '''

        self.log('DataStruct data getter', 'debug')
        self.load()
        return self._data

    def _set_data(self, data):

        '''
           data 'setter' method
        '''

        self.log('DataStruct data setter', 'debug')
        #FIXME this does not appear to work as expected
        self._data = data

    def _del_data(self):

        '''
           data 'deleter' method
        '''

        self.log('DataStruct data deleter', 'debug')
        del(self._data)
        self._data = None

    data = property(_get_data, _set_data, _del_data,
                    'Attribute to store the data')

    def _get_shape(self):

        '''
        '''

        self.log('DataStruct shape getter', 'debug')
        if self.data is not None:
            return self.data.shape[::-1]
        return(0,)

    shape = property(_get_shape)

    def _get_size(self):

        '''
           The total number of elements in the data array.
        '''

        self.log('DataStruct size getter', 'debug')
        if self.data is not None:
            return self.data.size
        return 0

    size = property(_get_size)

    def _get_itemsize(self):

        '''
           Return the item size (in bytes) of self.data.
        '''

        self.log('DataStruct itemsize getter', 'debug')
        if self.data is not None:
            return self.data.itemsize
        return 0

    itemsize = property(_get_itemsize)

    def _get_datatype(self):

        '''
        '''

        self.log('DataStruct datatype getter', 'debug')
        if self.data is not None:
            self._datatype = self.data.dtype.name
        return self._datatype

    def _set_datatype(self, datatype):

        '''
        '''

        self.log('DataStruct datatype setter', 'debug')
        self._datatype = datatype

    def _del_datatype(self):

        '''
        '''

        self.log('DataStruct datatype deleter', 'debug')
        self._datatype = None

    datatype = property(_get_datatype, _set_datatype, _del_datatype)

    def __del__(self):

        '''
           Cleanup data array before destruction
        '''

        self.log('DataStruct data __del__', 'debug')
        del(self.data)

    def copy(self, datatype=None):

        '''
           Copy the data to a new object.

           datatype: return a copy of the specified datatype
        '''

        self.log('DataStruct copy', 'verbose')
        if self.data is None:
            return None
        else:
            bmask = self.get_bitmask()
            if bmask is not None:
                self.log('DataStruct copy bmask', 'debug')
                bmask = bmask.copy()
            if datatype:
                if Array.dtype(datatype) != Array.dtype(self.datatype):
                    return self.__class__(data=self.data.copy(), bmask=bmask, datatype=datatype)
            return self.__class__(data=self.data.copy(), bmask=bmask)

    # FIXME
    # FIXME Rename save() to save_as() and create new save() method without
    # FIXME any arguments.  This is the proper OO way to implement saving.
    # FIXME

    def save(self, filename=None, hdr=None, datatype='float32', clobber=True,
             update_datamd5=True, option='silentfix'):

        '''
           Save the data to a file.

                 filename: name of the file (str)
                      hdr: image header (header object)
                 datatype: type of data output to the FITS file
           update_datamd5: update (or add) the DATAMD5 header keyword
                   option: option used to verify the output (from PyFITS)
                           should be one of fix, silentfix, ignore, warn, or
                           exception

        '''

        self.log('DataStruct save', 'verbose')
        if self.data is None:
            raise DARMAError('No data to save!')

        if self.readonly and (filename is None or filename == self.filename):
            raise DARMAError('Saving read-only data')

        if not filename:
            if not self.filename:
                raise DARMAError('Neither filename (%s) nor self.filename (%s) contain a valid file name!' % (filename, self.filename))
            else:
                filename = self.filename
        else:
            if not self.filename:
                self.filename = filename

        if hasattr(hdr, 'hdr'):
            hdr = hdr.hdr
        else:
            hdr = None

        if not self.data.flags.contiguous:
            self.log('DataStruct save: make contiguous', 'debug')
            self.data = Array.ascontiguousarray(self.data)

        try:
            if self.datatype is datatype:
                self.log('DataStruct save: fits.writeto', 'debug')
                fits.writeto(filename, data=self.data, header=hdr,
                               clobber=clobber, output_verify=option)
            else:
                self.log('DataStruct save: fits.writeto astype(%s)' % datatype, 'debug')
                fits.writeto(filename, data=self.data.astype(datatype),
                               header=hdr, clobber=clobber,
                               output_verify=option)
        except Exception as e:
            raise DARMAError(e)

        if update_datamd5:
            self.log('DataStruct save: update datamd5', 'debug')
            _update_datamd5(filename, _datamd5(filename))

    def display(self, viewer='skycat', filename=None):

        '''
           Display this image in an external viewer, saved to filename if
           filename is not None.

           NOTE: The image being saved here is saved to a temporary file in a
                 temporary directory without a proper header and will be
                 deleted once viewed.  To save the file properly, use the save
                 method.
        '''

        self.log('DataStruct display', 'verbose')
        if filename is None:
            self.log('DataStruct display: saving to temp file', 'debug')
            import tempfile
            if self.filename is None:
                base_name = 'None'
            else:
                base_name = self.filename.split('/')[-1]
            filename = tempfile.gettempdir() + '/' + '%s' % base_name
            del(tempfile)
        elif os.path.exists(filename):
            raise DARMAError('Cowardly refusing to overwrite existing file.  Use a differnt filename.')

        self.log('DataStruct display: saving file', 'debug')
        self.save(filename, update_datamd5=False)

        if not os.path.exists(filename):
            raise DARMAError('Could not find file %s' % self.filename)

        self.log('DataStruct display: launching viewer', 'verbose')
        os.system('%s %s' % (viewer, filename))
        self.log('DataStruct display: removing file', 'debug')
        os.remove(filename)

    def bin(self, xbin=2, ybin=2, datatype=None, old=False):

        '''
           Return with a binned version of the data.  Negative binning factors
           are allowed.  If a negative binning factor is used, this has the
           effect of reversing the axis.

               xbin: X-axis binning factor (int)
               ybin: Y-axis binning factor (int)
           datatype: use an alternate datatype for the binning (e.g., to
                     reduce rounding error)
                old: use older, much slower binning algorithm

           Note: If the binning factor is not a factor of the length of the
                 axis, the last axis_len % Nbin elements of the data will be
                 truncated (e.g., a 49x49 pixel image binned 2x2 will be a
                 24x24 pixel image where where the last column and row of data
                 are eliminated).

                 Also, if the datatype is not sufficient to handle the binned
                 data dynamic range, it will be truncated.
        '''

        self.log('DataStruct bin', 'verbose')
        x_bin = abs(int(xbin))
        y_bin = abs(int(ybin))

        if x_bin == 0 or y_bin == 0:
            raise DARMAError('Unsupported binning factor(s): (%s, %s)' % (str(xbin), str(ybin)))

        if x_bin != 1 or y_bin != 1:
            if old:
                xindex  = 1
                yindex  = 1
                # PyFITS Array axes are reversed.
                # XXX bitmask support should probably be included here for
                #     completeness
                if datatype:
                    dtype = datatype
                    data = self.copy(datatype=dtype)
                else:
                    dtype = self.datatype
                    data = self
                halfbin = data.__class__(data=Array.zeros(shape=(data.ysize(),
                                         data.xsize()/x_bin), dtype=dtype))
                fullbin = data.__class__(data=Array.zeros(shape=(data.ysize()/y_bin,
                                         data.xsize()/x_bin), dtype=dtype))

                self.log('DataStruct bin: starting halfbin', 'debug')
                for i in range(1, fullbin.xsize()+1):
                    for j in range(x_bin):
                        halfbin[i, :] += data[xindex, :]
                        xindex += 1
                self.log('DataStruct bin: starting fullbin', 'debug')
                for i in range(1, fullbin.ysize()+1):
                    for j in range(y_bin):
                        fullbin[:, i] += halfbin[:, yindex]
                        yindex += 1
                fullbin = data.__class__(data=fullbin.data, datatype=self.datatype)
                del(halfbin)
            else:
                # PyFITS Array axes are reversed.
                # XXX bitmask support should probably be included here for
                #     completeness
                shape = (self.ysize()/y_bin, self.xsize()/x_bin)
                if datatype:
                    data = self.data.astype(datatype)
                else:
                    data = self.data
                self.log('DataStruct bin: starting halfbin', 'debug')
                half = Array.add.reduceat(data, Array.arange(data.shape[0])[::y_bin], axis=0)
                self.log('DataStruct bin: starting fullbin', 'debug')
                full = Array.add.reduceat(half, Array.arange(data.shape[1])[::x_bin], axis=1)
                if full.shape != shape:
                    full = full[:shape[0], :shape[1]]
                fullbin = self.__class__(data=full, datatype=self.datatype)
        else:
            self.log('DataStruct bin: no binning requested', 'debug')
            fullbin = self.copy()

        if xbin < 0:
            self.log('DataStruct bin: reversing X', 'debug')
            fullbin = fullbin[::-1, ::]
        if ybin < 0:
            self.log('DataStruct bin: reversing Y', 'debug')
            fullbin = fullbin[::, ::-1]

        return fullbin

    def flip(self):

        '''
           Return a copy with the Y-axis flipped (top to bottom).
        '''

        self.log('DataStruct flip', 'verbose')
        return self.bin(1,-1)

    def flop(self):

        '''
           Return a copy with the X-axis flipped (left to right).
        '''

        self.log('DataStruct flop', 'verbose')
        return self.bin(-1,1)

    def reshape(self, shape):

        '''
           Set the shape of the image's data array to shape.

           shape: a tuple giving the shape

           The shape will generally be a tuple of the form (x,y) or (n,).
        '''

        self.log('DataStruct reshape', 'verbose')
        if self.data is not None:
            if self.has_bitmask():
                self.log('DataStruct reshape bmask', 'debug')
                self.bmask.reshape(shape)
            self.data = self.data.reshape(shape[::-1])

    def swapaxes(self):

        '''
           Swap NAXIS1 and NAXIS2 inplace.
        '''

        self.log('DataStruct swapaxes', 'verbose')
        if self.data is not None:
            if self.has_bitmask():
                self.log('DataStruct swapaxes bmask', 'debug')
                self.bmask.swapaxes(0,1)
            self.data = self.data.swapaxes(0,1)

    def extract_region(self, x0, y0, x1, y1):

        '''
           Extract a sub-region from this image/pixelmap

           x0, y0: lower lefthand corner
           x1, y1: upper righthand corner

           These coordinates follow FITS coordinates. Hence the
           x0, y0 = 1,1 is equivalent to the lower left corner of the
           input image, and the dimension of the resulting image will be
           (x1-x0)+1 x (y1-y0)+1
        '''

        self.log('DataStruct extract_region', 'verbose')
        if x0 < 1 or y0 < 1 or x1 > self.xsize() or y1 > self.ysize():
            raise DARMAError('Cannot extract region %s: region not contained completely within the %s!' % (repr((x0, y0, x1, y1)), self.__class__.__name__))

        return self[x0:x1, y0:y1]

    ########################################################################
    #
    # Introspection
    #

    def info(self):

        '''
           Show general information on this image/pixelmap.
        '''

        # Acquire attributes.
        size             = self.size
        item_size        = self.itemsize
        data_size        = size * item_size
        if hasattr(self, 'bmask'):
            has_nonnumbers = self.has_nonnumbers()
        else:
            has_nonnumbers = 'N/A'
        if self.has_bitmask():
            bitmask_size = self.bmask.size * self.bmask.itemsize
        else:
            bitmask_size = 0
        total_size       = data_size + bitmask_size
        # Print them out.
        print('   image class: %s'       %  self.__class__)
        print('         shape: %s'       % repr(self.shape))
        print('       npixels: %s'       %  size)
        print('      datatype: %s'       %  self.datatype)
        print('      itemsize: %s bytes' %  item_size)
        print('      datasize: %s bytes' %  data_size)
        print('has nonnumbers: %s'       %  has_nonnumbers)
        print('  bitmask size: %s bytes' %  bitmask_size)
        print('    total size: %s bytes' %  total_size)

    def xsize(self):

        '''
           The length of the x-axis data.
        '''

        if self.data is not None:
            return self.data.shape[1] # PyFITS Array axes are reversed.

    def ysize(self):

        '''
           The length of the y-axis data.
        '''

        if self.data is not None:
            return self.data.shape[0] # PyFITS Array axes are reversed.

    def has_bitmask(self):

        '''
           Determine if a bitmask exists for this object and is set.
        '''

        if hasattr(self, 'bmask') and self.bmask.data is not None:
            return True
        else:
            return False

    def get_bitmask(self):

        '''
           Return the bitmask for this object if it exists
        '''

        if hasattr(self, 'bmask'):
            return self.bmask
        else:
            return None

    def __len__(self):

        '''
           Total number of elements in the data array.
           x.__len__() <==> len(self)
        '''

        return self.size

    def __getitem__(self, key):

        '''
           Get an item from the data array using FITS convention indexes.
           x.__getitem__(i) <==> x[i]
        '''

        self.log('DataStruct __getitem__', 'verbose')
        if self.data is not None:
            if self.has_bitmask():
                self.log('DataStruct __getitem__ bmask', 'debug')
                bmask = self.bmask.__getitem__(key)
            else:
                bmask = None
            self.log('DataStruct __getitem__ adjust index: %s' % repr(key), 'debug')
            key = _adjust_index(key)
            return self.__class__(data=self.data.__getitem__(key),
                                  bmask=bmask)
        else:
            return self.__class__()

    def __setitem__(self, key, value):

        '''
           Set an item to the data array using FITS convention indexes.
           x.__setitem__(i, y) <==> x[i] = y
        '''

        self.log('DataStruct __setitem__', 'verbose')
        if self.data is not None:
            self.log('DataStruct __setitem__ adjust index: %s' % repr(key), 'debug')
            key = _adjust_index(key)
            self.log('DataStruct __setitem__ value: %s' % value.data, 'debug')
            self.data.__setitem__(key, value.data)
        else:
            raise DARMAError('Cannot set item.  Data array does not exist!')

    def __contains__(self, value):

        '''
           Return existence of value in self.
           x.__contains__(y) <==> y in x
        '''

        self.log('DataStruct __contains__: %s' % value, 'debug')
        return value in self.data

    #def __repr__(self):

    #    '''
    #       Show representation.
    #    '''

    #    if self.data is not None:
    #        data_array = self.data.__repr__()
    #    else:
    #        data_array = 'No data array loaded...'
    #    print 'image class: %s' %  self.__class__.__name__
    #    print '      shape: %s' % `self.shape`
    #    print '   datatype: %s' %  self.datatype
    #    print ' data array: %s' %  '(axes are swapped!)'
    #    print '             %s' %  data_array

    ########################################################################
    #
    # Abstract operations methods
    #

    def _arith_op_(self, op, other, *args, **kwargs):

        '''
           Provide a common interface for operations on images by other images
           and non-images.
        '''

        self.log('DataStruct _arith_op_', 'verbose')
        if isinstance(other, DataStruct):
            if other.data is not None:
                self.log('DataStruct _arith_op_ DataStruct: op=%s, data=%s, args=%s, kwargs=%s' % (op, other.data, args, kwargs), 'debug')
                return self.__class__(data=op(other.data, *args, **kwargs),
                                      bmask=self.get_bitmask())
            else:
                self.log('DataStruct _arith_op_ DataStruct no data: op=%s, args=%s, kwargs=%s' % (op, args, kwargs), 'debug')
                return self.copy()
        else:
            self.log('DataStruct _arith_op_ non-DataStruct: op=%s, data=%s, args=%s, kwargs=%s' % (op, other, args, kwargs), 'debug')
            return self.__class__(data=op(other, *args, **kwargs),
                                  bmask=self.get_bitmask())

    def _inplace_op_(self, op, other, *args, **kwargs):

        '''
           Provide a common interface for in-place operations on images by
           other images and non-images.
        '''

        self.log('DataStruct _inplace_op_', 'verbose')
        if isinstance(other, DataStruct):
            if other.data is not None:
                self.log('DataStruct _inplace_op_ DataStruct: op=%s, data=%s, args=%s, kwargs=%s' % (op, other.data, args, kwargs), 'debug')
                self.data = op(other.data, *args, **kwargs)
            else:
                self.log('DataStruct _inplace_op_ DataStruct no data: op=%s, args=%s, kwargs=%s' % (op, args, kwargs), 'debug')
        else:
            self.log('DataStruct _inplace_op_ non-DataStruct: op=%s, data=%s, args=%s, kwargs=%s' % (op, other, args, kwargs), 'debug')
            self.data = op(other, *args, **kwargs)
        return self

    ########################################################################
    #
    # Rich comparison operations
    #

    def __lt__(self, other):

        '''
           Less than comparison.
           x.__lt__(y) <==> x < y
        '''

        return self._arith_op_(self.data.__lt__, other)

    def __le__(self, other):

        '''
           Less than equal to comparison.
           x.__le__(y) <==> x <= y
        '''

        return self._arith_op_(self.data.__le__, other)

    def __eq__(self, other):

        '''
           Equal to comparison.
           x.__eq__(y) <==> x == y
        '''

        return self._arith_op_(self.data.__eq__, other)

    def __ne__(self, other):

        '''
           Not equal to comparison.
           x.__ne__(y) <==> x != y
        '''

        return self._arith_op_(self.data.__ne__, other)

    def __gt__(self, other):

        '''
           Greater than comparison.
           x.__gt__(y) <==> x > y
        '''

        return self._arith_op_(self.data.__gt__, other)

    def __ge__(self, other):

        '''
           Greater than equal to comparison.
           x.__ge__(y) <==> x >= y
        '''

        return self._arith_op_(self.data.__ge__, other)

    ########################################################################
    #
    # Arithmetic operations (binary)
    #

    def __add__(self, other):

        '''
           Add binary operation.
           x.__add__(y) <==> x + y
        '''

        return self._arith_op_(self.data.__add__, other)

    def __sub__(self, other):

        '''
           Subtract binary operation.
           x.__sub__(y) <==> x - y
        '''

        return self._arith_op_(self.data.__sub__, other)

    def __mul__(self, other):

        '''
           Multiply binary operation.
           x.__mul__(y) <==> x * y
        '''

        return self._arith_op_(self.data.__mul__, other)

    def __floordiv__(self, other):

        '''
           Floor divide binary operation.
           x.__floordiv__(y) <==> x // y
        '''

        return self._arith_op_(self.data.__div__, other)

    def __mod__(self, other):

        '''
           Modulus binary operation.
           x.__mod__(y) <==> x % y
        '''

        return self._arith_op_(self.data.__mod__, other)

    def __divmod__(self, other):

        '''
           Divide modulus binary operation.
           x.__divmod__(y) <==> divmod(x, y)
        '''

        return self._arith_op_(self.data.__divmod__, other)

    def __pow__(self, other):

        '''
           Power binary operation.
           x.__pow__(y) <==> pow(x, y) or x ** y
        '''

        return self._arith_op_(self.data.__pow__, other)

    def __lshift__(self, other):

        '''
           Left shift binary operation.
           x.__lshift__(y) <==> x << y
        '''

        return self._arith_op_(self.data.__lshift__, other)

    def __rshift__(self, other):

        '''
           Right shift binary operation.
           x.__rshift__(y) <==> x >> y
        '''

        return self._arith_op_(self.data.__rshift__, other)

    def __and__(self, other):

        '''
           AND binary operation.
           x.__and__(y) <==> x & y
        '''

        return self._arith_op_(self.data.__and__, other)

    def __xor__(self, other):

        '''
           XOR binary operation.
           x.__xor__(y) <==> x ^ y
        '''

        return self._arith_op_(self.data.__xor__, other)

    def __or__(self, other):

        '''
           OR binary operation.
           x.__or__(y) <==> x | y
        '''

        return self._arith_op_(self.data.__or__, other)

    def __div__(self, other):

        '''
           Divide binary operation.
           x.__div__(y) <==> x / y
        '''

        return self._arith_op_(self.data.__div__, other)


    def __truediv__(self, other):

        '''
           True divide binary operation.  Replaces __div__() when
           __future__.division is in effect.
           x.__truediv__(y) <==> x / y
        '''

        return self._arith_op_(self.data.__truediv__, other)

    ########################################################################
    #
    # Arithmetic operations (binary/in-place)
    #

    def __iadd__(self, other):

        '''
           Add in place binary operation.
           x = x.__iadd__(y) <==> x += y
        '''

        return self._inplace_op_(self.data.__iadd__, other)

    def __isub__(self, other):

        '''
           Subtract in place binary operation.
           x = x.__isub__(y) <==> x -= y
        '''

        return self._inplace_op_(self.data.__isub__, other)

    def __imul__(self, other):

        '''
           Multiply in place binary operation.
           x = x.__imul__(y) <==> x *= y
        '''

        return self._inplace_op_(self.data.__imul__, other)

    def __idiv__(self, other):

        '''
           Divide in place binary operation.
           x = x.__idiv__(y) <==> x /= y
        '''

        return self._inplace_op_(self.data.__idiv__, other)

    def __itruediv__(self, other):

        '''
           True divide in place binary operation.  Replaces __idiv__() when
           __future__.division is in effect.
           x = x.__idiv__(y) <==> x /= y
        '''

        return self._inplace_op_(self.data.__itruediv__, other)

    def __ifloordiv__(self, other):

        '''
           Floor divide in place binary operation.
           x = x.__ifloordiv__(y) <==> x //= y
        '''

        return self._inplace_op_(self.data.__ifloordiv__, other)

    def __imod__(self, other):

        '''
           Modulus in place binary operation.
           x = x.__imod__(y) <==> x %= y
        '''

        return self._inplace_op_(self.data.__imod__, other)

    def __ipow__(self, other):

        '''
           Power in place binary operation.
           x = x.__ipow__(y) <==> x **= y
        '''

        return self._inplace_op_(self.data.__ipow__, other)

    def __ilshift__(self, other):

        '''
           Left shift in place binary operation.
           x = x.__ilshift__(y) <==> x <<= y
        '''

        return self._inplace_op_(self.data.__ilshift__, other)

    def __irshift__(self, other):

        '''
           Right shift in place binary operation.
           x = x.__irshift__(y) <==> x >>= y
        '''

        return self._inplace_op_(self.data.__irshift__, other)

    def __iand__(self, other):

        '''
           AND in place binary operation.
           x = x.__iand__(y) <==> x &= y
        '''

        return self._inplace_op_(self.data.__iand__, other)

    def __ixor__(self, other):

        '''
           XOR in place binary operation.
           x = x.__ixor__(y) <==> x ^= y
        '''

        return self._inplace_op_(self.data.__ixor__, other)

    def __ior__(self, other):

        '''
           OR in place binary operation.
           x = x.__ior__(y) <==> x |= y
        '''

        return self._inplace_op_(self.data.__ior__, other)

    ########################################################################
    #
    # Arithmetic operations (binary/reflected)
    #

    def __radd__(self, other):

        '''
           Add reflected (swapped operands) binary operation.
           x.__radd__(y) <==> y + x
        '''

        return self._arith_op_(self.data.__radd__, other)

    def __rsub__(self, other):

        '''
           Subtract reflected (swapped operands) binary operation.
           x.__rsub__(y) <==> y - x
        '''

        return self._arith_op_(self.data.__rsub__, other)

    def __rmul__(self, other):

        '''
           Multiply reflected (swapped operands) binary operation.
           x.__rmul__(y) <==> y * x
        '''

        return self._arith_op_(self.data.__rmul__, other)

    def __rdiv__(self, other):

        '''
           Divide reflected (swapped operands) binary operation.
           x.__rdiv__(y) <==> y / x
        '''

        return self._arith_op_(self.data.__rdiv__, other)

    def __rtruediv__(self, other):

        '''
           True divide reflected (swapped operands) binary operation.  Replaces
           __rdiv__() when __future__.division is in effect.
           x.__rtruediv__(y) <==> y / x
        '''

        return self._arith_op_(self.data.__rtruediv__, other)

    def __rfloordiv__(self, other):

        '''
           Floor divide reflected (swapped operands) binary operation.
           x.__r__(y) <==> y // x
        '''

        return self._arith_op_(self.data.__rfloordiv__, other)

    def __rmod__(self, other):

        '''
           Modulus reflected (swapped operands) binary operation.
           x.__rmod__(y) <==> y % x
        '''

        return self._arith_op_(self.data.__rmod__, other)

    def __rdivmod__(self, other):

        '''
           Divide modulus reflected (swapped operands) binary operation.
           x.__rdivmod__(y) <==> divmod(y, x)
        '''

        return self._arith_op_(self.data.__rdivmod__, other)

    def __rpow__(self, other):

        '''
           Power reflected (swapped operands) binary operation.
           x.__rpow__(y) <==> pow(y, x) or y ** x
        '''

        return self._arith_op_(self.data.__rpow__, other)

    def __rlshift__(self, other):

        '''
           Left shift reflected (swapped operands) binary operation.
           x.__rlshift__(y) <==> y << x
        '''

        return self._arith_op_(self.data.__rlshift__, other)

    def __rrshift__(self, other):

        '''
           Right shift reflected (swapped operands) binary operation.
           x.__rrshift__(y) <==> y >> x
        '''

        return self._arith_op_(self.data.__rrshift__, other)

    def __rand__(self, other):

        '''
           AND reflected (swapped operands) binary operation.
           x.__rand__(y) <==> y & x
        '''

        return self._arith_op_(self.data.__rand__, other)

    def __rxor__(self, other):

        '''
           XOR reflected (swapped operands) binary operation.
           x.__rxor__(y) <==> y ^ x
        '''

        return self._arith_op_(self.data.__rxor__, other)

    def __ror__(self, other):

        '''
           OR reflected (swapped operands) binary operation.
           x.__ror__(y) <==> y | x
        '''

        return self._arith_op_(self.data.__ror__, other)

    ########################################################################
    #
    # Arithmetic operations (unary)
    #

    def __neg__(self):

        '''
           Negative unary operation.
           x.__neg__() <==> -x
        '''

        self.log('DataStruct __neg__', 'verbose')
        if self.data is not None:
            return self.__class__(data=self.data.__neg__(),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __pos__(self):

        '''
           Positive unary operation.
           x.__pos__() <==> +x
        '''

        self.log('DataStruct __pos__', 'verbose')
        if self.data is not None:
            return self.__class__(data=self.data.__pos__(),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __abs__(self):

        '''
           Absolute value unary operation.
           x.__abs__() <==> abs(x)
        '''

        self.log('DataStruct __abs__', 'verbose')
        if self.data is not None:
            return self.__class__(data=self.data.__abs__(),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __invert__(self):

        '''
           Invert unary operation.
           x.__invert__() <==> ~x

           NOTE: only works on integer datatypes
        '''

        self.log('DataStruct __invert__', 'verbose')
        if self.data is not None:
            return self.__class__(data=self.data.__invert__(),
                                  bmask=self.get_bitmask())
        else:
            return self

    ########################################################################
    #
    # Datatype conversion
    #

    def __int__(self):

        '''
           Integer datatype conversion.  Return with the data converted to an
           integer representation (%s).
        ''' % INT

        self.log('DataStruct __int__', 'verbose')
        if self.data is not None:
            self.log('DataStruct __int__: astype=%s' % INT, 'debug')
            return self.__class__(data=self.data.astype(INT),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __float__(self):

        '''
           Float datatype conversion.  Return with the data converted to a
           float64 representation (PyFITS converts 16 and -32 BITPIX data into
           float32 by default).
        '''

        self.log('DataStruct __float__', 'verbose')
        if self.data is not None:
            return self.__class__(data=self.data.astype('float64'),
                                  bmask=self.get_bitmask())
        else:
            return self

    def astype(self, datatype=FLOAT):

        '''
           Return with the data converted to an arbitrary Array datatype
           (uint8, float32, etc.).

           datatype: Array data type
        '''

        self.log('DataStruct astype', 'verbose')
        if self.data is not None:
            self.log('DataStruct astype: astype=%s' % datatype, 'debug')
            return self.__class__(data=self.data.astype(datatype),
                                  bmask=self.get_bitmask())
        else:
            return self

    ########################################################################
    #
    # Initialization conversion
    #

    def set_val(self, value=0):

        '''
           Set all elements of the data in this image to an arbitrary value.

              value: any number construct (int, float, imag, nan, etc.)
        '''

        self.log('DataStruct set_val', 'verbose')
        self.log('DataStruct set_val: val=%s' % value, 'debug')
        self.data.fill(value)

    def set_zero(self):

        '''
           Set all elements of the data in this image to zero.
        '''

        # Same as Array.zeros()
        self.log('DataStruct set_zero', 'verbose')
        self.set_val()

    ########################################################################
    #
    # Utility functions
    #

def _datamd5(filename, regions=None, buffer_blocks=32):

    '''
       Calculate the MD5SUM of all data regions of a FITS file.

            filename: name of the FITS file containg the data regions
             regions: regions of data (e.g., list of extension indexes) to be
                      hashed (if None, do all regions)
       buffer_blocks: read only this many FITS blocks at a time
    '''

    import os, md5

    if not os.path.exists(filename):
        raise DARMAError('No FITS file (%s) to calcualte MD5SUM from!' % filename)

    fitsfile = fits_open(filename, mode='readonly', memmap=True)
    md5sum   = md5.md5()

    block  = 2880
    number = buffer_blocks
    if regions is None:
        regions = list(range(len(fitsfile)))
    for index in regions:
        hdu = fitsfile[index]
        start  = hdu._datLoc
        length = hdu._datSpan
        hdu._file.seek(start)
        while length > 0:
            if length < number*block:
                buffer_size = length
            else:
                buffer_size = number*block
            md5sum.update(hdu._file.read(buffer_size))
            length -= number*block

    fitsfile.close()

    return md5sum.hexdigest()

def _update_datamd5(filename, datamd5):

    '''
       Update (or add) the DATAMD5 keyword in the header with datamd5.

       datamd5: the md5sum of the data (32 character string)
    '''

    import os

    if not os.path.exists(filename):
        raise DARMAError('No FITS file (%s) to update DATAMD5 for!' % filename)
    if len(datamd5) != 32:
        raise DARMAError('%s does not appear to be a valid MD5SUM.' % datamd5)

    fitsfile = fits_open(filename, mode='update', memmap=True)
    fitsfile[0].header.update('DATAMD5', datamd5, comment='MD5 checksum of all data regions')
    fitsfile.close()
    # XXX TODO EMH PyFits in the module NA_pyfits.py does something nasty.
    # Under certain circumstances the signal handler is redefined to
    # ignore Ctrl-C keystrokes, the next two lines mean to reset the signal
    # handler to its original state, which is omitted in PyFits.
    import signal
    signal.signal(signal.SIGINT,signal.default_int_handler)

def _adjust_index(key):

    '''
       Function to take array index keys (integers or slices) and adjust them
       from FITS convention to PyFITS/Array convention (i.e., unity-indexed
       [NAXIS1, NAXIS2] to zero-indexed [NAXIS2, NAXIS1]).

       Indexes
       -------
       Positive indexes go from 1...n, negative indexes are supported and mimic
       the standard Python conventions (e.g., -1 is the last element).

       Slices
       ------
       Slices work a little differently from Python standard.  A little thought
       on the index behavior will reveal that a blank initial index means start
       at index 1, blank terminal index means stop at index n, and the range of
       the slice is terminal_index - initial_index + 1.  Normal Python behavior
       says stop at n-1.  For example:

       > import image
       > img = image.make_image(20, 20)
       > img.shape
       (20, 20)
       > img[1:10, :].data.shape
       (20, 10)
       > img.data[:, 1:10].shape
       (20, 9)

       Note the data array is stored with the axes in reversed order as is the
       PyFITS standard.
    '''

    # If two indexes.
    if isinstance(key, tuple):
        # Make sure no more than 2 indexes exist.
        if len(key) > 2:
            raise IndexError('Maximum 2 indexes/slices allowed!')
        key0 = key[0]
        key1 = key[1]
        # Slice modification for first index.
        if isinstance(key0, slice):
            start = key0.start
            stop  = key0.stop
            step  = key0.step
            if start == 0 or stop == 0:
                raise DARMAError('Slice [%d:%d, _] not in FITS convention!' % (start, stop))
            # Rectify negative indexes.
            if start is not None and start < 0: start += 1
            if stop  is not None and stop  < 0: stop  += 1
            # Shift indexes for zero-indexed array.
            if step is None or step >= 0:
                if start is not None:
                    start -= 1
            else:
                if stop is not None:
                    stop -= 1
            key0 = slice(start, stop, step)
        # Non-slice modification for first index.
        else:
            if key0 == 0:
                raise DARMAError('Index [%d, _] not in FITS convention!' % key0)
            # Rectify negative indexes.
            if key0 is not None and key0 < 0: key0 += 1
            # Shift indexes for zero-indexed array.
            key0 -= 1
        # Slice modification for second index.
        if isinstance(key1, slice):
            start = key1.start
            stop  = key1.stop
            step  = key1.step
            if start == 0 or stop == 0:
                raise DARMAError('Slice [_, %d:%d] not in FITS convention!' % (start, stop))
            # Rectify negative indexes.
            if start is not None and start < 0: start += 1
            if stop  is not None and stop  < 0: stop  += 1
            # Shift indexes for zero-indexed array.
            if step is None or step >= 0:
                if start is not None:
                    start -= 1
            else:
                if stop is not None:
                    stop -= 1
            key1 = slice(start, stop, step)
        # Non-slice modification for second index.
        else:
            if key1 == 0:
                raise DARMAError('Index [_, %d] not in FITS convention!' % key1)
            # Rectify negative indexes.
            if key1 is not None and key1 < 0: key1 += 1
            # Shift indexes for zero-indexed array.
            key1 -= 1
        return (key1, key0) # PyFITS Array axes are reversed.
    # If one index.
    else:
        key0 = key
        # Slice modification.
        if isinstance(key0, slice):
            start = key0.start
            stop  = key0.stop
            step  = key0.step
            if start == 0 or stop == 0:
                raise DARMAError('Slice [%d:%d] not in FITS convention!' % (start, stop))
            # Rectify negative indexes.
            if start is not None and start < 0: start += 1
            if stop  is not None and stop  < 0: stop  += 1
            # Shift indexes for zero-indexed array.
            if step is None or step >= 0:
                if start is not None:
                    start -= 1
            else:
                if stop is not None:
                    stop -= 1
            key0 = slice(start, stop, step)
        # Non-slice modification
        else:
            if key0 == 0:
                raise DARMAError('Index [%d] not in FITS convention!' % key0)
            # Rectify negative indexes.
            if key0 is not None and key0 < 0: key0 += 1
            # Shift indexes for zero-indexed array.
            key0 -= 1
        return key0

def fold_string(string, num=80, char='', newline='\n'):

    '''
       Fold the given string string at num characters if len(string) > num.
       If char is specified, prefer splitting after nearest previous
       occurrance of char.  The newline character can also be specified.

          string: any string to be split
             num: number of characters to split at
            char: prefer to split after specific character in string
         newline: newline character
    '''

    output = ''
    buffer = ''
    for c in string:
        if len(buffer)+1 < num:
            buffer += c
        else:
            buffer += c
            if char and char in buffer:
                index = buffer.rfind(char)
                output += '%s%s' % (buffer[:index+1], newline)
                buffer = buffer[index+1:]
            else:
                output += '%s%s' % (buffer, newline)
                buffer = ''
    if len(buffer):
        output += buffer
    if output.endswith(newline):
        output = output[:-len(newline)]
    return output

def get_tmpbase(suffix='', prefix='tmp', dir=None):

    '''
       Return a basename for a temporary filename.

       Loosely follows tempfile.mktemp syntax, but constructs a name based on
       the current time (seconds since 00:00:00 1970-01-01 UTC) with
       microsecond precision followed by a 6 character random string.  This
       should virtually guarantee temp-name uniqueness.  The returned string
       has the following form:

       '<dir>/<prefix><seconds.microseconds>.<random_string>.<suffix>'

       If dir is not None, it will be supplied with a trailing '/' if one is
       not given.  If suffix is not '', it will be preceeded by a '.' if one
       is not given.

       suffix: suffix to add
       prefix: prefix to add
          dir: pathname to prepend to file (None means the same as '')

       NOTE: If dir is given, it will be checked for, and an Exception raised
             if it does not exist.
    '''

    from os import path
    from datetime import datetime
    from tempfile import mktemp

    if dir is not None:
        if not path.exists(dir):
            raise Exception('Path: %s does not exist!')
        if not dir.endswith('/'):
            dir = '%s/' % dir
    else:
        dir = ''
    dt = datetime.now()
    date_str = '%s.%06d' % (dt.strftime('%s'), dt.microsecond)
    rand_str = '.%s' % mktemp(suffix='', prefix='', dir='')
    if suffix != '':
        if suffix.startswith('.'):
            suffix = suffix[1:]
        suffix = '.%s' % suffix

    return '%s%s%s%s%s' % (dir, prefix, date_str, rand_str, suffix)

#####################################
# Astropy/PyFITS compatibility code #
#####################################

def fits_open(*args, **kwargs):

    '''
       Wrapper around fits.open() method to allow arbitrary extra
       arguments common to all open commands, e.g., ignore_missing_end.
    '''

    return fits.open(ignore_missing_end=True, *args, **kwargs)


def new_table(columns=[], hdr=None, nrows=0, fill=False, tbtype='BinTableHDU'):

    '''
       In PyFITS >= 3.3 pyfits.new_table() is deprecated.  Use
       pyfits.BinTableHDU.from_columns() for new BINARY tables or
       pyfits.TableHDU.from_columns() for new ASCII tables instead.
       Similarly, in AstroPy >=0.4 astropy.io.fits.new_table() is
       deprecated.  Use from_columns() methods from
       astropy.io.fits.BinTableHDU and astropy.io.fits.TableHDU.

       Create a new table from the input column definitions.

         columns: sequence of Column or ColDefs objects to create a
                  table from
             hdr: a fits.Header instance to be used to populate the non-
                  required keywords
           nrows: umber of rows in the new table
            fill: fill all cells with zeros or blanks
          tbtype: table type to be created ("BinTableHDU" or "TableHDU")
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        if tbtype == 'BinTableHDU':
            return fits.BinTableHDU.from_columns(columns=columns, header=hdr, nrows=nrows, fill=fill)
        if tbtype == 'TableHDU':
            return fits.TableHDU.from_columns(columns=columns, header=hdr, nrows=nrows, fill=fill)
    else:
        return fits.new_table(input=columns, header=hdr, nrows=nrows, fill=fill, tbtype='BinTableHDU')

def _strip_keyword(keyword, fill=False):

    '''
       Return a keyword stripped of 'HIERARCH ' if a string.

         keyword: any keyword string or index
            fill: additionally, replace ' ' with '_'
    '''

    if isinstance(keyword, (str, unicode)):
        if keyword.startswith('HIERARCH '):
            keyword = keyword[9:]
        if fill:
            keyword = keyword.replace(' ', '_')
        return keyword
    elif isinstance(keyword, int):
        return keyword
    else:
        raise DARMAError('keyword is not of type str or int: %s' % type(keyword))

def is_hierarch(card):

    '''
       Return if a fits.Card instance is a HIERARCH card.

         card: a fits.Card instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        return card._hierarch
    else:
        return isinstance(card, fits.core._Hierarch)

def get_cards(hdr):

    '''
       Return the card list (dictionary-like object, actually) of a
       fits.Header instance.

         hdr: a fits.Header instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        return hdr.cards
    else:
        return hdr.ascardlist()

def get_keyword(card):

    '''
       Return the keyword of a fits.Card instance.

         card: a fits.Card instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        return card.keyword
    else:
        return card.key

def _remove_cards(hdr, keywords):

    '''
       Astropy/new PyFITS cannot remove a HIERARCH keyword card properly.
       Remove it by making a shadow copy, clearing the original header,
       then copying all but the removed cards back.

              hdr: a fits.Header instance (Astropy.new PyFITS only)
         keywords: list of keys of cards to be removed
    '''

    shadow = hdr.copy()
    hdr.clear()
    hdr.update([card for card in shadow.cards if card.keyword not in keywords])

def clear_header(hdr):

    '''
       Remove all card from the header.

         hdr: a fits.Header instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        hdr.clear()
    else:
        for key in hdr:
            del hdr[key]

def rename_keyword(hdr, oldkeyword, newkeyword):

    '''
       Rename a card's keyword in the header.

                hdr: a fits.Header instance
         oldkeyword: old keyword or card index
         newkeyword: new keyword
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        old = _strip_keyword(oldkeyword)
        new = _strip_keyword(newkeyword)
        if new in hdr:
            raise DARMAError('Cannot rename %s to %s: %s exists!' % (oldkeyword, newkeyword, newkeyword))
        #FIXME rename_keyword() does not work properly for HIERARCH
        #FIXME keywords in Astropy/new PyFITS.  Manually rename.
        #hdr.rename_keyword(oldkeyword=old, newkeyword=new)
        oldcard = hdr.cards[old]
        newcard = fits.Card(keyword=newkeyword, value=oldcard.value, comment=oldcard.comment)
        hdr.insert(old, newcard, useblanks=False)
        #FIXME The main problem with rename_keyword() method for HIERARCH
        #FIXME cards is the remove() method.
        _remove_cards(hdr, [old])
    else:
        hdr.rename_key(oldkey=oldkeyword, newkey=newkeyword)

def update_header(hdr, keyword, value, comment=None, before=None, after=None, savecomment=False):

    '''
       Update one header card.

       If the keyword already exists, it's value and/or comment will
       be updated.  If it does not exist, a new card will be created
       and it will be placed before or after the specified location.
       If no `before` or `after` is specified, it will be appended at
       the end.

             hdr: a fits.Header instance
         keyword: keyword of the card to be updated
           value: value to be used for updating
         comment: comment to be used for updating
          before: keyword name/index of the card before which the new
                  card will be placed (the argument before takes
                  precedence over after if both specified)
           after: keyword name/index of the card after which the new
                  card will be placed
         savecomment: preserve the current comment for an existing
                      keyword (takes precedence over comment if both
                      specified)
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        key = _strip_keyword(keyword)
        key_in_hdr = key in hdr
        reference_keyword = ''
        if before:
            before = _strip_keyword(before)
            reference_keyword = before
            _after = False
        if after:
            after = _strip_keyword(after)
            reference_keyword = after
            _after = True
        if savecomment:
            comment = None
        else:
            if not comment and key_in_hdr:
                comment = hdr.cards[key].comment
        card = (keyword, value, comment)
        if reference_keyword:
            if key_in_hdr:
                _remove_cards(hdr, [key])
            hdr.insert(reference_keyword, card, after=_after)
        else:
            if key_in_hdr:
                card = (key, value, comment)
            hdr.update([card])
    else:
        hdr.update(key=keyword, value=value, comment=comment, before=before, after=after, savecomment=savecomment)

def get_cardimage(card):

    '''
       Return a fits.Card instance image

         card: a fits.Card instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        return card.image
    else:
        # overcome a HIERARCH keyword image bug in older PyFITS versions
        if is_hierarch(card):
            value = card.value
            if isinstance(value, (str, unicode)):
                if len(value) < 8:
                    value = '%- 8s' % value
                cardstr = 'HIERARCH %s = \'%s\'' % (card.key, value)
            else:
                cardstr = 'HIERARCH %s = %s' % (card.key, card.value)
            return '%- 80s' % cardstr[:80]
        return card.ascardimage()

def get_comment(hdr):

    '''
       Return a list of all COMMENT card contents

         hdr: a fits.Header instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        if 'COMMENT' in hdr:
            return hdr['COMMENT']
        return []
    else:
        return hdr.get_comment()

def get_history(hdr):

    '''
       Return a list of all HISTORY card contents

         hdr: a fits.Header instance
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        if 'HISTORY' in hdr:
            return hdr['HISTORY']
        return []
    else:
        return hdr.get_history()

def _get_index(hdr, keyword):

    '''
       Return index of a keyword in a fits.Header instance

             hdr: a fits.Header instance
         keyword: the keyword to find the index of
    '''

    if not isinstance(keyword, (str, unicode)):
        raise DARMAError('keyword for _get_index MUST be a string')
    if _HAS_ASTROPY or _HAS_PYFITS33:
        key = _strip_keyword(keyword)
        if key not in hdr:
            raise DARMAError('header does not contain keyword: %s' % keyword)
        return hdr.index(key)
    else:
        if keyword not in hdr:
            raise DARMAError('header does not contain keyword: %s' % keyword)
        return hdr.ascardlist().index_of(keyword)

def get_value(hdr, keyword, default=None):

    '''
       Return the value of a keyword/index in a fits.Header instance

             hdr: a fits.Header instance
         keyword: the keyword/index for which to get the value
         default: the value to return when the keyword/index is missing
    '''

    if not isinstance(keyword, (str, unicode, int)):
        raise DARMAError('keyword for get_value MUST be a string or int')
    if _HAS_ASTROPY or _HAS_PYFITS33:
        key = _strip_keyword(keyword)
        return hdr.get(key, default=default)
    else:
        if isinstance(keyword, int) and keyword >= len(hdr.ascardlist()):
            return default
        return hdr.get(keyword, default=default)

def add_blank(hdr, value, before=None, after=None):

    '''
       Add a BLANK card to a fits.Header instance

            hdr: a fits.Header instance
          value: value of the new blank card
         before: keyword of the card before which the BLANK card will be
                 placed
          after: keyword of the card after which the BLANK card will be
                 placed
    '''

    if _HAS_ASTROPY or _HAS_PYFITS33:
        if before:
            before = _strip_keyword(before)
        if after:
            after = _strip_keyword(after)
        hdr.add_blank(value=value, before=before, after=after)
    else:
        if not (before or after):
            if '' in hdr:
                index = hdr.ascardlist().index_of('')
                blanks = [card.value for card in hdr.ascardlist() if card.key == '']
                index += len(blanks)-1
            elif 'COMMENT' in hdr:
                index = hdr.ascardlist().index_of('COMMENT')-1
            elif 'HISTORY' in hdr:
                index = hdr.ascardlist().index_of('HISTORY')-1
            else:
                index = len(hdr.ascardlist())-1
            after = index
        hdr.add_blank(value=value, before=before, after=after)

