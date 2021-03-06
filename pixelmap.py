"""A map of boolean pixelvalues.
"""

__version__ = '@(#)$Revision$'

import os

from .common import fits, Array, fits_open
from .common import DARMAError, DataStruct, get_tmpbase


class pixelmap(DataStruct):

    """
       A class mimicing image(), but for boolean arrays indicating good (1) and
       bad (0) pixels.

       All arithmetic operation on images can be used on pixelmaps.  See the
       image() class for this and other details.
    """

    def __init__(self, filename=None, data=None, extension=0, plane=0,
                 readonly=0, memmap=1, *args, **kwargs):
        """
            filename: The name of a FITS file
                data: A data array (Python sequence, Array, etc.)
           extension: The extension (default 0)
            readonly: Indicate that the FITS file is readonly
              memmap: use memory mapping for data access (NOT IMPLEMENTED)

           If there is no filename and no data, the pixelmap data is set to
           None.  If both filename and data are set, the pixelmap is created
           from self.data.
        """

        DataStruct.__init__(self, *args, **kwargs)

        self.filename = filename or None
        self._data = data
        self.extension = extension
        self.plane = plane
        self.readonly = readonly
        self.memmap = memmap

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError('Filename: %s not found!' % self.filename)

    def load(self):
        """
           Proxy for load_pixelmap()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        """

        self.load_pixelmap()

    def load_pixelmap(self):
        """
           Load the pixelmap from a file or from the given data Array.
        """

        data = self._data
        _data = None
        if data is None:
            if self.filename is not None:
                try:
                    #_data = fits.getdata(self.filename, self.extension)
                    _data = fits_open(self.filename, memmap=self.memmap)[self.extension].data
                    if _data is not None:
                        _data.astype('bool')
                except Exception as e:
                    raise DARMAError('Error loading pixelmap from %s: %s' % (self.filename, e))
        else:
            _data = Array.asanyarray(data, dtype='bool')
            if not _data.flags.contiguous:
                _data = Array.ascontiguousarray(_data, dtype='bool')
        if _data is not None and len(_data.shape) == 3:
            _data = _data[self.plane]
        self._data = _data

    def dump_pixelmap(self, filename):
        """
           A basic save() to filename.
        """

        self.save(filename=filename)

    def save(self, filename=None, hdr=None, datatype='uint8', clobber=True,
             update_datamd5=True):
        """
           Save the data to a file.

                 filename: name of the file (str)
                      hdr: image header (header object)
                 datatype: type of data output to the FITS file
           update_datamd5: update (or add) the DATAMD5 header keyword

           NOTE: pixelmaps are Boolean arrays and cannot be saved to FITS as
                 images with this datatype.  The smallest datatype possible is
                 unsigned 8-bit integer (the default datatype here.)
        """

        DataStruct.save(self, filename=filename, hdr=hdr, datatype=datatype,
                        clobber=clobber, update_datamd5=update_datamd5)

    def as_image(self):
        """
           Return an image object constructed from this pixelmap object.
        """

        from .image import image
        return image(data=self.data)

    def as_eclipse_pixelmap(self):
        """
           Return an Eclipse pixelmap object based on this pixelmap.
        """

        tmpname = get_tmpbase(dir='/tmp', prefix='pixelmap', suffix='fits')
        self.save(filename=tmpname, update_datamd5=False)
        from eclipse import pixelmap as e_pixelmap
        e_pmap = e_pixelmap.pixelmap(tmpname)

        return e_pmap

    def set_val(self, value=0):
        """
           Set all elements of the data in this image to an arbitrary value.

              value: any number construct (int, float, imag, nan, etc.)
           datatype: Array data type
        """

        DataStruct.set_val(self, value=value, datatype='bool')

    def count(self):
        """
           Return the number of good pixels (non-zero values) in the pixelmap.
        """

        return self.data.nonzero()[0].shape[0]

    def bin_xor(self, other):
        """
           Synonym for __ixor__
        """

        return self.__ixor__(other)

    def bin_not(self):
        """
           Synonym for __invert__().
        """

        return self.__invert__()
