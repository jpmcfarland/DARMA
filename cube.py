'''
   A list of images or pixelmaps with methods that process stacks of them.
'''

__version__ = '@(#)$Revision$'

import pyfits, os

from common import Array, FLOAT, INT, LONG
from common import DARMAError, _datamd5, _update_datamd5
from image import image
from pixelmap import pixelmap

#XXX convert cube from list to DataStruct

class cube(list):

    '''
       cubes are stacks (actually just lists) of images or pixelmaps that can
       be manipulated in similar fashions to images or pixelmaps.  Normal
       arithmetic (addition, subtraction, multiplication, division, etc.) is
       performed on all members of the stack in turn (i1*constant, i2*constant,
       etc.), but other operations, such as statistics, are performed on sets
       of pixels in the `z' direction of the stack.

       It is assumed that all members of a cube are the same shape, type, and
       datatype.

       The functionality of a cube is very similar to that of an image or a
       pixelmap, except that the operations are typically broadcasted over all
       members of the cube, while others condense the members of the cube to an
       image or a pixelmap.
    '''

    def __init__(self, image_list=None, filename=None, extension=0,
                 readonly=0, *args, **kwargs):

        '''
           image_list: A list of images or pixelmaps
             filename: The name of a FITS file the cube can be loaded from
            extension: A FITS extension number
                plane: The plane in a 3D image stack
             readonly: Indicate that the FITS file is readonly
        '''

        self.image_list = image_list
        self.filename   = filename or None
        self.extension  = extension
        self.readonly   = readonly

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError, 'Filename: %s not found!' % self.filename

        self.load_cube()

    def load(self):

        '''
           Proxy for load_cube()
        '''

        self.load_cube()

    def load_cube(self):

        '''
           Load the images from a file or from the given image_list.  If there
           is no filename and no images, the list is empty.  A new cube
           can be loaded into the current instance by setting self.image_list
           to a new list of images or pixelmaps and calling self.load_cube().
           However, it is preferred to instantiate a new cube.
        '''

        if self.image_list is not None:

            list.__init__(self, self.image_list)
            del self.image_list

        else:

            filename  = self.filename
            extension = self.extension
            readonly  = self.readonly

            if filename is not None:
                try:
                    self.image_list = []
                    data = pyfits.getdata(filename, extension)
                    if len(data.shape) == 3:
                        for plane in range(data.shape[0]):
                            idx = filename.rfind('.')
                            fname = filename[:idx] + '_plane%d'%plane + filename[idx:]
                            self.image_list.append(image(data=data[plane], filename=fname))
                    elif len(data.shape) == 2:
                        self.image_list.append(image(data=data, filename=filename))
                    del data
                    list.__init__(self, self.image_list)
                    del self.image_list
                except Exception, e:
                    raise DARMAError, 'Error loading cube from %s: %s' % (filename, e)
            else:
                list.__init__(self, [])

        self._set_shape_attribute()
        self._set_datatype_attribute()

    def _set_shape_attribute(self):

        '''
           Set the shape attribute to a tuple of (len(self), xsize, ysize)
        '''

        if len(self) > 0:
            if self[0]._data is not None:
                # PyFITS Array axes are reversed.
                self.shape = (len(self), self[0]._data.shape[::-1])
            else:
                self.shape = (len(self),)
        else:
            self.shape = (0,)

    def _set_datatype_attribute(self):

        '''
           Set the datatype of self.data.
        '''

        if len(self) > 0:
            if self[0]._data is not None:
                self.datatype = self[0]._data.dtype.name
        else:
            self.datatype = None

    def _make_cube(self):

        '''
           Return a list of pointers (actually Array views) to the image data
           Arrays.
        '''

        try:
            view_cube = [img.data.view() for img in self]
        except Exception, e:
            raise DARMAError, 'Error allocating cube: %s' % e
        return view_cube

    def as_image_list(self):

        '''
           Return a list of individual image,pixelmap objects, each
           corresponding to plane in the data cube.  This replicates the way
           Eclipse stored cube data.

           NOT YET IMPLEMENTED!
        '''

        return NotImplementedError, 'When cube houses a real data cube, this will replicate previous cube behavior.'

    def copy(self):

        '''
           Copy the data to a new object.
        '''

        return cube(image_list=[img.copy() for img in self])

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
            raise DARMAError, 'Saving read-only data'

        if filename is None:
            if self.filename is None:
                raise DARMAError, 'No filename to save the file to!'
            else:
                filename = self.filename
        else:
            if self.filename is None:
                self.filename = filename

        if hasattr(hdr, 'hdr'):
            hdr = hdr.hdr

        if extension is None:
            extension = self.extension

        if datatype is None and self[0].datatype == 'bool':
            datatype='uint8'

        for img in self:
            if not img.data.flags.contiguous:
                img.data = Array.ascontiguousarray(img.data)

        if self.datatype is datatype:
            data = Array.concatenate([img.data for img in self])
        else:
            data = Array.concatenate([img.data for img in self],
                                     dtype=datatype)
        data = data.reshape(self.shape)

        pyfits.writeto(filename=filename, data=data, header=hdr,
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

        return self[0].data.shape[1] # PyFITS Array axes are reversed

    def ysize(self):

        '''
           The length of the y-axis data of the cube members.
        '''

        return self[0].data.shape[0] # PyFITS Array axes are reversed


    ########################################################################
    #
    # Abstract operations methods
    #

    def _arith_op_(self, op, other, *args, **kwargs):

        '''
           Provide a common interface for operations on cubes by other cubes
           and non-cubes.
        '''

        result = []

        if isinstance(other, cube):
            if len(self) != len(other):
                raise DARMAError, 'Operation on cubes of unequal length'
            else:
                for ima, oth in zip(self, other):
                    result.append(op(ima, oth, *args, **kwargs))
        else:
            for ima in self:
                result.append(op(ima, other, *args, **kwargs))

        return cube(image_list=result)

    def _inplace_op_(self, op, other, *args, **kwargs):

        '''
           Provide a common interface for in-place operations on cubes by
           other cubes and non-cubes.
        '''

        if isinstance(other, cube):
            if len(self) != len(other):
                raise DARMAError, "Operation on cubes of unequal length"
            for i, oth in zip(range(len(self)), other):
                self[i] = op(self[i], oth, *args, **kwargs)
        else:
            for i in range(len(self)):
                self[i] = op(self[i], other, *args, **kwargs)

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

        return self._arith_op_(self[0].__class__.__lt__, other)

    def __le__(self, other):

        '''
           Less than equal to comparison.
           x.__le__(y) <==> x <= y
        '''

        return self._arith_op_(self[0].__class__.__le__, other)

    def __eq__(self, other):

        '''
           Equal to comparison.
           x.__eq__(y) <==> x == y
        '''

        return self._arith_op_(self[0].__class__.__eq__, other)

    def __ne__(self, other):

        '''
           Not equal to comparison.
           x.__ne__(y) <==> x != y
        '''

        return self._arith_op_(self[0].__class__.__ne__, other)

    def __gt__(self, other):

        '''
           Greater than comparison.
           x.__gt__(y) <==> x > y
        '''

        return self._arith_op_(self[0].__class__.__gt__, other)

    def __ge__(self, other):

        '''
           Greater than equal to comparison.
           x.__ge__(y) <==> x >= y
        '''

        return self._arith_op_(self[0].__class__.__ge__, other)

    ########################################################################
    #
    # Arithmetic operations (binary)
    #

    def __add__(self, other):

        '''
           Add binary operation.
           x.__add__(y) <==> x + y
        '''

        return self._arith_op_(self[0].__class__.__add__, other)

    def __sub__(self, other):

        '''
           Subtract binary operation.
           x.__sub__(y) <==> x - y
        '''

        return self._arith_op_(self[0].__class__.__sub__, other)

    def __mul__(self, other):

        '''
           Multiply binary operation.
           x.__mul__(y) <==> x * y
        '''

        return self._arith_op_(self[0].__class__.__mul__, other)

    def __floordiv__(self, other):

        '''
           Floor divide binary operation.
           x.__floordiv__(y) <==> x // y
        '''

        return self._arith_op_(self[0].__class__.__div__, other)

    def __mod__(self, other):

        '''
           Modulus binary operation.
           x.__mod__(y) <==> x % y
        '''

        return self._arith_op_(self[0].__class__.__mod__, other)

    def __divmod__(self, other):

        '''
           Divide modulus binary operation.
           x.__divmod__(y) <==> divmod(x, y)
        '''

        return self._arith_op_(self[0].__class__.__divmod__, other)

    def __pow__(self, other):

        '''
           Power binary operation.
           x.__pow__(y) <==> pow(x, y) or x ** y
        '''

        return self._arith_op_(self[0].__class__.__pow__, other)

    def __lshift__(self, other):

        '''
           Left shift binary operation.
           x.__lshift__(y) <==> x << y
        '''

        return self._arith_op_(self[0].__class__.__lshift__, other)

    def __rshift__(self, other):

        '''
           Right shift binary operation.
           x.__rshift__(y) <==> x >> y
        '''

        return self._arith_op_(self[0].__class__.__rshift__, other)

    def __and__(self, other):

        '''
           AND binary operation.
           x.__and__(y) <==> x & y
        '''

        return self._arith_op_(self[0].__class__.__and__, other)

    def __xor__(self, other):

        '''
           XOR binary operation.
           x.__xor__(y) <==> x ^ y
        '''

        return self._arith_op_(self[0].__class__.__xor__, other)

    def __or__(self, other):

        '''
           OR binary operation.
           x.__or__(y) <==> x | y
        '''

        return self._arith_op_(self[0].__class__.__or__, other)

    def __div__(self, other):

        '''
           Divide binary operation.
           x.__div__(y) <==> x / y
        '''

        return self._arith_op_(self[0].__class__.__div__, other)


    def __truediv__(self, other):

        '''
           True divide binary operation.  Replaces __div__() when
           __future__.division is in effect.
           x.__truediv__(y) <==> x / y
        '''

        return self._arith_op_(self[0].__class__.__truediv__, other)

    ########################################################################
    #
    # Arithmetic operations (binary/in-place)
    #

    def __iadd__(self, other):

        '''
           Add in place binary operation.
           x = x.__iadd__(y) <==> x += y
        '''

        return self._inplace_op_(self[0].__class__.__iadd__, other)

    def __isub__(self, other):

        '''
           Subtract in place binary operation.
           x = x.__isub__(y) <==> x -= y
        '''

        return self._inplace_op_(self[0].__class__.__isub__, other)

    def __imul__(self, other):

        '''
           Multiply in place binary operation.
           x = x.__imul__(y) <==> x *= y
        '''

        return self._inplace_op_(self[0].__class__.__imul__, other)

    def __idiv__(self, other):

        '''
           Divide in place binary operation.
           x = x.__idiv__(y) <==> x /= y
        '''

        return self._inplace_op_(self[0].__class__.__idiv__, other)

    def __itruediv__(self, other):

        '''
           True divide in place binary operation.  Replaces __idiv__() when
           __future__.division is in effect.
           x = x.__idiv__(y) <==> x /= y
        '''

        return self._inplace_op_(self[0].__class__.__itruediv__, other)

    def __ifloordiv__(self, other):

        '''
           Floor divide in place binary operation.
           x = x.__ifloordiv__(y) <==> x //= y
        '''

        return self._inplace_op_(self[0].__class__.__ifloordiv__, other)

    def __imod__(self, other):

        '''
           Modulus in place binary operation.
           x = x.__imod__(y) <==> x %= y
        '''

        return self._inplace_op_(self[0].__class__.__imod__, other)

    def __ipow__(self, other):

        '''
           Power in place binary operation.
           x = x.__ipow__(y) <==> x **= y
        '''

        return self._inplace_op_(self[0].__class__.__ipow__, other)

    def __ilshift__(self, other):

        '''
           Left shift in place binary operation.
           x = x.__ilshift__(y) <==> x <<= y
        '''

        return self._inplace_op_(self[0].__class__.__ilshift__, other)

    def __irshift__(self, other):

        '''
           Right shift in place binary operation.
           x = x.__irshift__(y) <==> x >>= y
        '''

        return self._inplace_op_(self[0].__class__.__irshift__, other)

    def __iand__(self, other):

        '''
           AND in place binary operation.
           x = x.__iand__(y) <==> x &= y
        '''

        return self._inplace_op_(self[0].__class__.__iand__, other)

    def __ixor__(self, other):

        '''
           XOR in place binary operation.
           x = x.__ixor__(y) <==> x ^= y
        '''

        return self._inplace_op_(self[0].__class__.__ixor__, other)

    def __ior__(self, other):

        '''
           OR in place binary operation.
           x = x.__ior__(y) <==> x |= y
        '''

        return self._inplace_op_(self[0].__class__.__ior__, other)

    ########################################################################
    #
    # Arithmetic operations (binary/reflected)
    #

    def __radd__(self, other):

        '''
           Add reflected (swapped operands) binary operation.
           x.__radd__(y) <==> y + x
        '''

        return self._arith_op_(self[0].__class__.__radd__, other)

    def __rsub__(self, other):

        '''
           Subtract reflected (swapped operands) binary operation.
           x.__rsub__(y) <==> y - x
        '''

        return self._arith_op_(self[0].__class__.__rsub__, other)

    def __rmul__(self, other):

        '''
           Multiply reflected (swapped operands) binary operation.
           x.__rmul__(y) <==> y * x
        '''

        return self._arith_op_(self[0].__class__.__rmul__, other)

    def __rdiv__(self, other):

        '''
           Divide reflected (swapped operands) binary operation.
           x.__rdiv__(y) <==> y / x
        '''

        return self._arith_op_(self[0].__class__.__rdiv__, other)

    def __rtruediv__(self, other):

        '''
           True divide reflected (swapped operands) binary operation.  Replaces
           __rdiv__() when __future__.division is in effect.
           x.__rtruediv__(y) <==> y / x
        '''

        return self._arith_op_(self[0].__class__.__rtruediv__, other)

    def __rfloordiv__(self, other):

        '''
           Floor divide reflected (swapped operands) binary operation.
           x.__r__(y) <==> y // x
        '''

        return self._arith_op_(self[0].__class__.__rfloordiv__, other)

    def __rmod__(self, other):

        '''
           Modulus reflected (swapped operands) binary operation.
           x.__rmod__(y) <==> y % x
        '''

        return self._arith_op_(self[0].__class__.__rmod__, other)

    def __rdivmod__(self, other):

        '''
           Divide modulus reflected (swapped operands) binary operation.
           x.__rdivmod__(y) <==> divmod(y, x)
        '''

        return self._arith_op_(self[0].__class__.__rdivmod__, other)

    def __rpow__(self, other):

        '''
        '''

        raise DARMAError, "scalar**cube does not make sense"

    def __rlshift__(self, other):

        '''
           Left shift reflected (swapped operands) binary operation.
           x.__rlshift__(y) <==> y << x
        '''

        return self._arith_op_(self[0].__class__.__rlshift__, other)

    def __rrshift__(self, other):

        '''
           Right shift reflected (swapped operands) binary operation.
           x.__rrshift__(y) <==> y >> x
        '''

        return self._arith_op_(self[0].__class__.__rrshift__, other)

    def __rand__(self, other):

        '''
           AND reflected (swapped operands) binary operation.
           x.__rand__(y) <==> y & x
        '''

        return self._arith_op_(self[0].__class__.__rand__, other)

    def __rxor__(self, other):

        '''
           XOR reflected (swapped operands) binary operation.
           x.__rxor__(y) <==> y ^ x
        '''

        return self._arith_op_(self[0].__class__.__rxor__, other)

    def __ror__(self, other):

        '''
           OR reflected (swapped operands) binary operation.
           x.__ror__(y) <==> y | x
        '''

        return self._arith_op_(self[0].__class__.__ror__, other)

    ########################################################################
    #
    # Abstract looping operations methods
    #

    def _image_loop_(self, method, pixmap=None, *args, **kwargs):

        '''
           Modify the images in place, by applying image, pixelmap, args and
           kwargs to method.
        '''

        if pixmap is None:
            for ima in self:
                method(ima, *args, **kwargs)
        elif isinstance(pixmap, pixelmap):
            for ima in self:
                method(ima, pixmap=pixmap, *args, **kwargs)
        elif len(pixmap) == len(self):
            for ima, pmap in zip(self, pixmap):
                method(ima, pixmap=pmap, *args, **kwargs)
        else:
            raise DARMAError, 'image and pixelmap lists are not of the same length!'

    def _return_image_loop_(self, method, pixmap=None, *args, **kwargs):

        '''
           Modify the images in place, by applying image, pixelmap, args and
           kwargs to method.
        '''

        result = []

        if pixmap is None:
            for ima in self:
                result.append(method(ima, *args, **kwargs))
        elif isinstance(pixmap, pixelmap):
            for ima in self:
                result.append(method(ima, pixmap=pixmap, *args, **kwargs))
        elif len(pixmap) == len(self):
            for ima, pmap in zip(self, pixmap):
                result.append(method(ima, pixmap=pmap, *args, **kwargs))
        else:
            raise DARMAError, 'image and pixelmap lists are not of the same length!'

        return cube(image_list=result)

    ########################################################################
    #
    # Initialization conversion
    #

    def set_val(self, value=0, datatype=None):

        '''
           Set all elements of each image in this cube to an arbitrary value.

           value: any number construct (int, float, imag, nan, etc.)
            datatype: Array data type
        '''

        if datatype is None:
            datatype = self[0].datatype

        self._image_loop_(self[0].__class__.set_val, pixmap=None,  value=value,
                          datatype=datatype)

    def set_zero(self):

        '''
           Set all elements of each image in this cube to zero.
        '''

        self._image_loop_(self[0].__class__.set_zero, pixmap=None, value=value,
                          datatype=datatype)

    ########################################################################
    #
    # Arithmetic operations (unary)
    #

    def __neg__(self):

        '''
           Negative unary operation.
           x.__neg__() <==> -x
        '''

        return self._return_image_loop_(self[0].__class__.__neg__)

    def __pos__(self):

        '''
           Positive unary operation.
           x.__pos__() <==> +x
        '''

        return self._return_image_loop_(self[0].__class__.__pos__)

    def __abs__(self):

        '''
           Absolute value unary operation.
           x.__abs__() <==> abs(x)
        '''

        return self._return_image_loop_(self[0].__class__.__abs__)

    def __invert__(self):

        '''
           Invert unary operation.
           x.__invert__() <==> ~x

           NOTE: only works on integer data types
        '''

        return self._return_image_loop_(self[0].__class__.__invert__)

    ########################################################################
    #
    # Datatype conversion
    #

    def __int__(self):

        '''
           Integer datatype conversion.  Returns an integet representation of
           the cube.
        '''

        return self._return_image_loop_(self[0].__class__.astype, pixmap=None,
                                        datatype=INT)

    def __long__(self):

        '''
           Long datatype conversion.  Returns a long integer representation of
           the cube.
        '''

        return self._return_image_loop_(self[0].__class__.astype, pixmap=None,
                                        datatype=LONG)

    def __float__(self):

        '''
           Float datatype conversion.  Returns a float64 representation of the
           cube (PyFITS converts 16 and -32 BITPIX data into float32 by
           default).
        '''

        return self._return_image_loop_(self[0].__class__.astype, pixmap=None,
                                        datatype='float64')

    def astype(self, datatype=FLOAT):

        '''
           Return image as an arbitrary Array datatype (uint8, float32, etc.).

           datatype: Array data type
        '''

        return self._return_image_loop_(self[0].__class__.astype, pixmap=None,
                                        datatype=datatype)

    ########################################################################
    #
    # Type conversion
    #

    def as_image(self):

        '''
           Return an image object constructed from this pixelmap object.
        '''

        return self._return_image_loop_(pixelmap.as_image)

    def as_pixelmap(self):

        '''
           Return a pixelmap object constructed from this image object.
        '''

        return self._return_image_loop_(image.as_pixelmap)


    ##################################################################
    #
    # In-place operations
    #

    def normalize_mean(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):

        '''
           Normalize the images to a mean of 1.0.

           The mean can be computed in a restricted area.  This function
           modifies the image in-place.

             pixmap: map of valid pixels (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        if self[0].__class__ is pixelmap:
            raise DARMAError, '%s does not support this operation!' % pixelmap

        self._image_loop_(self[0].__class__.normalize_mean, pixmap=pixmap,
                         pixrange=pixrange, zone=zone, scale=scale)

    def normalize_median(self, pixmap=None, pixrange=None, zone=None,
                         scale=1.0):

        '''
           Normalize the images to a median of 1.0.

           The median can be computed in a restricted area.  This function
           modifies the image in-place.

             pixmap: map of valid pixelsd (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        if self[0].__class__ is pixelmap:
            raise DARMAError, '%s does not support this operation!' % pixelmap

        self._image_loop_(self[0].__class__.normalize_median, pixmap=pixmap,
                         pixrange=pixrange, zone=zone, scale=scale)

    def normalize_flux(self, pixmap=None, pixrange=None, zone=None,
                       scale=1.0):

        '''
           Normalize the images to a flux of 1.0.

           The flux can be computed in a restricted area.  This function
           modifies the image in-place.

             pixmap: map of valid pixelsd (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different scale (default=1.0)
        '''

        if self[0].__class__ is pixelmap:
            raise DARMAError, '%s does not support this operation!' % pixelmap

        self._image_loop_(self[0].__class__.normalize_flux, pixmap=pixmap,
                         pixrange=pixrange, zone=zone, scale=scale)

    def normalize_range(self, pixmap=None, pixrange=None, zone=None,
                        scale=1.0):

        '''
           Normalize the images to a range of values between 0.0 and 1.0.

           The range can be computed in a restricted area.  This function
           modifies the image in-place.

             pixmap: map of valid pixelsd (default=None)
           pixrange: a range of valid values [low, high] (default=None)
               zone: a valid zone [x0, y0, x1, y1]
              scale: normalize to a different maximum (default=1.0)
        '''

        if self[0].__class__ is pixelmap:
            raise DARMAError, '%s does not support this operation!' % pixelmap

        self._image_loop_(self[0].__class__.normalize_range, pixmap=pixmap,
                         pixrange=pixrange, zone=zone, scale=scale)

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

        if self[0].__class__ is pixelmap:
            raise DARMAError, '%s does not support this operation!' % pixelmap

        self._image_loop_(self[0].__class__.normalize_absolute_flux,
                          pixmap=pixmap, pixrange=pixrange, zone=zone,
                          scale=scale)

    ########################################################################
    #
    # image producing operations
    #

    def sum(self):

        '''
           Sum all images in the cube to a single image.
        '''

        if len(self) == 0:
            raise DARMAError, 'No images in cube to sum'

        result = self[0].copy()
        for ima in self[1:]:
            result+=ima
        return result

    def average(self):

        '''
           Do a straight average of all images in the cube.
        '''

        result = self.sum()
        result /= len(self)
        return result

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

        if len(self) < 2:
            raise DARMAError, 'stdev requires at least two images!'

        if mean is None:
            mean = self.average()

        stdev = (self[0]-mean)
        stdev *= stdev
        for ima in self[1:]:
            devima = ima-mean
            devima *= devima
            stdev += devima
            devima = None # force unload

        stdev /= len(self)
        return stdev ** 0.5

    def median(self, buffer_size=16):

        '''
           Do a median average of all images in the cube.

           buffer_size: number of rows to median at a time (MUST be int)

           This method is buffered to reduce memory usage and increase
           performance.
        '''

        num = len(self)
        if num < 3:
            raise DARMAError, 'median requires at least three images!'

        bsize = int(buffer_size)

        # A list of Array objects, not images or pixelmaps
        pcube  = self._make_cube()
        result = Array.empty(shape=pcube[0].shape, dtype=pcube[0].dtype)

        remain = len(pcube[0])%bsize
        length = len(pcube[0])-remain

        for i in range(bsize, length+bsize, bsize):
            #bcube = Array.asarray([image[i-bsize:i] for image in pcube])
            bcube = Array.concatenate([image[i-bsize:i] for image in pcube])
            bcube = bcube.reshape((num,)+pcube[0][i-bsize:i].shape)
            result[i-bsize:i] = Array.median(bcube)
        if remain:
            #bcube = Array.asarray([image[i:i+remain] for image in pcube])
            bcube = Array.concatenate([image[i:i+remain] for image in pcube])
            bcube = bcube.reshape((num,)+pcube[0][i:i+remain].shape)
            result[i:i+remain] = Array.median(bcube)

        return self[0].__class__(data=result)

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
#        pcube = self._make_cube()
#        result.p_ima = c_eclipse.cube_avg_reject(pcube,
#                                                 low_reject, high_reject)
#        c_eclipse.cube_del_shallow(pcube)
#        result.pcheck('Error in average')
#        return result

    def average_with_sigma_clip(self, n_cycle, nmin, bias,scaling,thresh, badval, rn, gain):

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
#        pcube_in = self._make_cube()
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

