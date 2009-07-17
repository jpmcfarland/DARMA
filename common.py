'''
   Auxiliary data structures and constants.
'''

__version__ = '@(#)$Revision$'

import pyfits, math, os

# Allow DARMA to be imported even if NumPy is not available.
_HAS_NUMPY = True
try:
    import numpy as Array
    import numpy.random as Arrayrandom
    import numpy.fft as Arrayfft
    # FIXME
    #import numpy.nd_image.filters as Arrayfilters
except:
    Array = Arrayrandom = Arrayfft = None
    _HAS_NUMPY = False

FLOAT = 'float64'
INT   = 'int32'
LONG  = 'int64'

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

        print 'min_pix: %s' % self.min_pix
        print 'max_pix: %s' % self.max_pix
        print 'avg_pix: %s' % self.avg_pix
        print 'median : %s' % self.median
        print 'stdev  : %s' % self.stdev
        print 'energy : %s' % self.energy
        print 'flux   : %s' % self.flux
        print 'absflux: %s' % self.absflux
        print 'min_x  : %s' % self.min_x
        print 'min_y  : %s' % self.min_y
        print 'max_x  : %s' % self.max_x
        print 'max_y  : %s' % self.max_y
        print 'npix   : %s' % self.npix

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

    def __init__(self, *args, **kwargs):

        '''
           Abstract constructor.

           self.data MUST be defined as an Array instance by constructors
           of inherited classes.
        '''

        pass

    def load(self):

        '''
           Abstract load method.  All sub-classes should call their load_...()
           method from this method.

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self._data = None

    def _get_data(self):

        '''
           data 'getter' method
        '''

        self.load()
        return self._data

    def _set_data(self, data):

        '''
           data 'setter' method
        '''

        self._data = data

    def _del_data(self):

        '''
           data 'deleter' method
        '''

        del self._data

    data = property(_get_data, _set_data, _del_data,
                    'Attribute to store the data')

    def _get_shape(self):

        '''
        '''

        if self._data is not None:
            return self._data.shape[::-1]
        return(0,)

    shape = property(_get_shape)

    def _get_size(self):

        '''
           The total number of elements in the data array.
        '''

        if self._data is not None:
            return self._data.size
        return 0

    size = property(_get_size)

    def _get_itemsize(self):

        '''
           Return the item size (in bytes) of self.data.
        '''

        if self._data is not None:
            return self._data.itemsize
        return 0

    itemsize = property(_get_itemsize)

    def _get_datatype(self):

        '''
        '''

        if self._data is not None:
            self._datatype = self._data.dtype.name
        return self._datatype

    def _set_datatype(self, datatype):

        '''
        '''

        self._datatype = datatype

    def _del_datatype(self):

        '''
        '''

        self._datatype = None

    datatype = property(_get_datatype, _set_datatype, _del_datatype)

    def copy(self):

        '''
           Copy the data to a new object.
        '''

        if self.data is None:
            return None
        else:
            bmask = self.get_bitmask()
            if bmask is not None:
                bmask = bmask.copy()
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

        if self.data is None:
            raise DARMAError, 'No data to save!'

        if self.readonly and (filename is None or filename == self.filename):
            raise DARMAError, 'Saving read-only data'

        if not filename:
            if not self.filename:
                raise DARMAError, 'Neither filename (%s) nor self.filename (%s) contain a valid file name!' % (filename, self.filename)
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
            self.data = Array.ascontiguousarray(self.data)

        try:
            if self.datatype is datatype:
                pyfits.writeto(filename, data=self.data, header=hdr,
                               clobber=clobber, output_verify=option)
            else:
                pyfits.writeto(filename, data=self.data.astype(datatype),
                               header=hdr, clobber=clobber,
                               output_verify=option)
        except Exception, e:
            raise DARMAError, e

        if update_datamd5:
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

        if filename is None:
            import tempfile
            if self.filename is None:
                base_name = 'None'
            else:
                base_name = self.filename.split('/')[-1]
            filename = tempfile.gettempdir() + '/' + '%s' % base_name
            del tempfile
        elif os.path.exists(filename):
            raise DARMAError, 'Cowardly refusing to overwrite existing file.  Use a differnt filename.'

        self.save(filename, update_datamd5=False)

        if not os.path.exists(filename):
            raise DARMAError, 'Could not find file %s' % self.filename

        os.system('%s %s' % (viewer, filename))
        os.remove(filename)

    def bin(self, xbin=2, ybin=2):

        '''
           Return with a binned version of the data.  Negative binning factors
           are allowed.  If a negative binning factor is used, this has the
           effect of reversing the axis.

           xbin: X-axis binning factor (int)
           ybin: Y-axis binning factor (int)

           Note: If the binning factor is not a factor of the length of the
                 axis, the last axis_len % Nbin elements of the data will be
                 truncated (e.g., a 49x49 pixel image binned 2x2 will be a
                 24x24 pixel image where where the last column and row of data
                 are eliminated).

                 Also, if the datatype is not sufficient to handle the binned
                 data dynamic range, it will be truncated.
        '''

        x_bin = abs(int(xbin))
        y_bin = abs(int(ybin))

        if x_bin == 0 or y_bin == 0:
            raise DARMAError, 'Unsupported binning factor(s): (%s, %s)' % (str(xbin), str(ybin))

        if x_bin != 1 and y_bin != 1:
            xindex  = 1
            yindex  = 1
            # PyFITS Array axes are reversed.
            # XXX bitmask support should probably be included here for
            #     completeness
            halfbin = self.__class__(data=Array.zeros(shape=(self.ysize(),
                                     self.xsize()/x_bin), dtype=self.datatype))
            fullbin = self.__class__(data=Array.zeros(shape=(self.ysize()/y_bin,
                                     self.xsize()/x_bin), dtype=self.datatype))

            for i in range(1, fullbin.xsize()+1):
                for j in range(x_bin):
                    halfbin[i, :] += self[xindex, :]
                    xindex += 1
            for i in range(1, fullbin.ysize()+1):
                for j in range(y_bin):
                    fullbin[:, i] += halfbin[:, yindex]
                    yindex += 1
            del halfbin
        else:
            fullbin = self.copy()

        if xbin < 0:
            fullbin = fullbin[::-1, ::]
        if ybin < 0:
            fullbin = fullbin[::, ::-1]

        return fullbin

    def flip(self):

        '''
           Return a copy with the Y-axis flipped (top to bottom).
        '''

        return self.bin(1,-1)

    def flop(self):

        '''
           Return a copy with the X-axis flipped (left to right).
        '''

        return self.bin(-1,1)

    def reshape(self, shape):

        '''
           Set the shape of the image's data array to shape.

           shape: a tuple giving the shape

           The shape will generally be a tuple of the form (x,y) or (n,).
        '''

        if self.data is not None:
            if self.has_bitmask():
                self.bmask.reshape(shape)
            self.data = self.data.reshape(shape[::-1])

    def swapaxes(self):

        '''
           Swap NAXIS1 and NAXIS2 inplace.
        '''

        if self.data is not None:
            if self.has_bitmask():
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

        if x0 < 1 or y0 < 1 or x1 > self.xsize() or y1 > self.ysize():
            raise DARMAError, 'Cannot extract region %s: region not contained completely within the %s!' % (`(x0, y0, x1, y1)`, self.__class__.__name__)

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
        print '   image class: %s'       %  self.__class__
        print '         shape: %s'       % `self.shape`
        print '       npixels: %s'       %  size
        print '      datatype: %s'       %  self.datatype
        print '      itemsize: %s bytes' %  item_size
        print '      datasize: %s bytes' %  data_size
        print 'has nonnumbers: %s'       %  has_nonnumbers
        print '  bitmask size: %s bytes' %  bitmask_size
        print '    total size: %s bytes' %  total_size

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

        if self.data is not None:
            if self.has_bitmask():
                bmask = self.bmask.__getitem__(key)
            else:
                bmask = None
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

        if self.data is not None:
            key = _adjust_index(key)

            self.data.__setitem__(key, value.data)
        else:
            raise DARMAError, 'Cannot set item.  Data array does not exist!'

    def __contains__(self, value):

        '''
           Return existence of value in self.
           x.__contains__(y) <==> y in x
        '''

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

        if isinstance(other, DataStruct):
            if other.data is not None:
                return self.__class__(data=op(other.data, *args, **kwargs),
                                      bmask=self.get_bitmask())
            else:
                return self.copy()
        else:
            return self.__class__(data=op(other, *args, **kwargs),
                                  bmask=self.get_bitmask())

    def _inplace_op_(self, op, other, *args, **kwargs):

        '''
           Provide a common interface for in-place operations on images by
           other images and non-images.
        '''

        if isinstance(other, DataStruct):
            if other.data is not None:
                self.data = op(other.data, *args, **kwargs)
        else:
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
           integer representation.
        '''

        if self.data is not None:
            return self.__class__(data=self.data.astype(INT),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __long__(self):

        '''
           Long datatype conversion.  Return with the data converted to a long
           integer representation.
        '''

        if self.data is not None:
            return self.__class__(data=self.data.astype(LONG),
                                  bmask=self.get_bitmask())
        else:
            return self

    def __float__(self):

        '''
           Float datatype conversion.  Return with the data converted to a
           float64 representation (PyFITS converts 16 and -32 BITPIX data into
           float32 by default).
        '''

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

        if self.data is not None:
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

        self.data.fill(value)

    def set_zero(self):

        '''
           Set all elements of the data in this image to zero.
        '''

        # Same as Array.zeros()
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
        raise DARMAError, 'No FITS file (%s) to calcualte MD5SUM from!' % filename

    fitsfile = pyfits.open(filename, mode='readonly', memmap=1)
    md5sum   = md5.md5()

    block  = 2880
    number = buffer_blocks
    if regions is None:
        regions = range(len(fitsfile))
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
        raise DARMAError, 'No FITS file (%s) to update DATAMD5 for!' % filename
    if len(datamd5) != 32:
        raise DARMAError, '%s does not appear to be a valid MD5SUM.' % datamd5

    fitsfile = pyfits.open(filename, mode='update', memmap=1)
    fitsfile[0].header.update('DATAMD5', datamd5, comment='MD5 checksum of all data regions')
    fitsfile.close()
    # XXX TODO EMH PyFits in the module NA_pyfits.py does something nasty.
    # Under certain circumstances the signal handler is redefined to
    # ignore Ctrl-C keystrokes, the next two lines mean to reset the signal
    # handler to its original state, which is omitted in PyFits.
    import signal
    signal.signal(signal.SIGINT,signal.SIG_DFL)

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
    if type(key) is tuple:
        # Make sure no more than 2 indexes exist.
        if len(key) > 2:
            raise IndexError, 'Maximum 2 indexes/slices allowed!'
        key0 = key[0]
        key1 = key[1]
        # Slice modification for first index.
        if type(key0) is slice:
            start = key0.start
            stop  = key0.stop
            step  = key0.step
            if start == 0 or stop == 0:
                raise DARMAError, 'Slice [%d:%d, _] not in FITS convention!' % (start, stop)
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
                raise DARMAError, 'Index [%d, _] not in FITS convention!' % key0
            # Rectify negative indexes.
            if key0 is not None and key0 < 0: key0 += 1
            # Shift indexes for zero-indexed array.
            key0 -= 1
        # Slice modification for second index.
        if type(key1) is slice:
            start = key1.start
            stop  = key1.stop
            step  = key1.step
            if start == 0 or stop == 0:
                raise DARMAError, 'Slice [_, %d:%d] not in FITS convention!' % (start, stop)
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
                raise DARMAError, 'Index [_, %d] not in FITS convention!' % key1
            # Rectify negative indexes.
            if key1 is not None and key1 < 0: key1 += 1
            # Shift indexes for zero-indexed array.
            key1 -= 1
        return (key1, key0) # PyFITS Array axes are reversed.
    # If one index.
    else:
        key0 = key
        # Slice modification.
        if type(key0) is slice:
            start = key0.start
            stop  = key0.stop
            step  = key0.step
            if start == 0 or stop == 0:
                raise DARMAError, 'Slice [%d:%d] not in FITS convention!' % (start, stop)
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
                raise DARMAError, 'Index [%d] not in FITS convention!' % key0
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

