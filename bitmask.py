'''
   A bitmask to store flagged pixel information.
'''

__version__ = '@(#)$Revision$'

import pyfits, os

from astro.util.darma.common import Array, pyfits_open
from astro.util.darma.common import DARMAError, DataStruct, _adjust_index
from astro.util.darma.pixelmap import pixelmap
try:
    range = xrange # Python 2
except NameError:
    pass # Python 3


IMPORT_TYPES = ['bool', 'int8', 'int16', 'int32', 'uint8','uint16','uint32']
EXPORT_TYPES = ['uint8', 'int16', 'int32']

class bitmask(DataStruct):

    '''
       A bit mask in which to store up to 32 types of pixelmaps.
    '''

    def __init__(self, filename=None, extension=0, datatype=None, pmap=None,
                 bit=None, data=None, conserve=False, readonly=0, memmap=1,
                 *args, **kwargs):

        '''
           Construct a bit mask object that can store up to 8 bad pixel maps.

            filename: FITS filename to load bitmask from
           extension: FITS extension to use
            datatype: datatype of internal representation (converted from
                      original datatype if set)
                pmap: a pixelmap object to create bitmask from
                 bit: the bit to assign to the flagged pixels in the pixelmap
                data: a data array to create this bitmask from
            conserve: conserve memory by deleting data array when nothing is
                      flagged
            readonly: is filename readonly
              memmap: use memory mapping for data access

           If there is no filename and no pmap, bitmask.data is set to None.
           If both self.filename and self.pmap are set, the bitmask is created
           from self.pmap.
        '''

        DataStruct.__init__(self, *args, **kwargs)
        self.log('bitmask constructor', 'verbose')
        self.log('bitmask constructor: filename=%s, extension=%s, datatype=%s, pmap=%s, bit=%s, data=%s, conserve=%s, readonly=%s, memmap=%s, args=%s, kwargs=%s' % (filename, extension, datatype, pmap, bit, data, conserve, readonly, memmap, args, kwargs), 'debug')

        self.filename  = filename
        self.extension = extension
        self._datatype = datatype
        self.pmap      = pmap
        self.bit       = bit
        self._data     = data
        self.conserve  = conserve
        self.readonly  = readonly
        self.memmap    = memmap

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError('Filename: %s not found!' % self.filename)
        # Check datatype (can only use integers internally, and can only
        # export uint8, int16, and int32 to FITS)
        if datatype and Array.dtype(datatype).name not in IMPORT_TYPES:
            raise DARMAError('Error -- datatype MUST be of boolean type or of integer type not more than 32-bits!')

    def load(self):

        '''
           Proxy for load_bitmask()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self.log('bitmask load', 'verbose')
        self.load_bitmask()

    def load_bitmask(self):

        '''
           Load the bitmask from a file or a Pixelmask.
        '''

        log = self.log
        log('bitmask load_bitmask', 'verbose')
        filename  = self.filename
        extension = self.extension
        pmap      = self.pmap
        datatype  = self._datatype
        bit       = self.bit
        conserve  = self.conserve
        memmap    = self.memmap

        if pmap is None:
            if self._data is None:
                if filename is not None:
                    try:
                        log('bitmask load_bitmask from file: filename=%s, memmap=%s, extension=%s' % (filename, memmap, extension), 'debug')
                        #self._data = pyfits.getdata(filename, extension)
                        self._data = pyfits_open(filename, memmap=memmap)[extension].data
                        if datatype and self._data.dtype.name != datatype:
                            log('bitmask load_bitmask convert datatype', 'debug')
                            self._data = self._data.astype(datatype)
                        if conserve:
                            self._clean_bitmask()
                    except Exception as e:
                        raise DARMAError('Error loading bitmask from %s: %s' % (filename, e))
            else:
                log('bitmask load_bitmask from data array: data=%s, dtype=%s' % (self._data, datatype), 'debug')
                self._data = Array.asanyarray(self._data, dtype=datatype)
            if self._data is not None and not self._data.flags.contiguous:
                log('bitmask load_bitmask make contiguous', 'debug')
                self._data = Array.ascontiguousarray(self._data, dtype=datatype)
        else:
            #FIXME convert input Eclipse pixelmaps
            log('bitmask load_bitmask from pixelmap: bit=%s, pmap=%s, astype=%s' % (bit, pmap.data, datatype), 'debug')
            if bit is None:
                bit = 0
            self._data = ((~pmap.data)<<bit).astype(datatype)
            if conserve:
                self._clean_bitmask()
        del(pmap, self.pmap)
        self.pmap = None

    def _clean_bitmask(self):


        '''
           If the bitmask is masking nothing (i.e. no bits set), eliminate its
           data by setting self.data to None.
        '''

        self.log('bitmask _clean_bitmask', 'debug')
        #PERFORMANCE ISSUE
        if self.data is not None and not self.data.any():
            self.log('bitmask _clean_bitmask deleting bitmask', 'debug')
            self._del_bitmask()

    def _del_bitmask(self):

        '''
           Eliminate the bitmask data by setting self.data to None.

           NOTE: All masked information will be lost!
        '''

        self.log('bitmask _del_bitmask', 'debug')
        del(self.data)
        self.data = None

    def _get_dtype(self):

        '''
           dtype getter
        '''

        self.log('bitmask dtype getter', 'debug')
        return Array.dtype(self.datatype)

    dtype = property(_get_dtype, None, None, 'a representation of datatype')

    def _get_bits(self):

        '''
           bits getter
        '''

        self.log('bitmask bits getter', 'debug')
        return self.dtype.itemsize*8

    bits = property(_get_bits, None, None, 'number of bits per pixel of the current datatype')

    def as_pixelmap(self, mask=None):

        '''
           Export this bitmask as a pixelmap.

           If mask is None, a logical-OR of all masks is returned, else
           a pixelmap of the specified mask is returned.

           mask: mask of bits to collapse to pixelmap
        '''

        self.log('bitmask as_pixelmap', 'verbose')
        if self.data is None:
            return pixelmap()
        else:
            if mask is None:
                data = ~(self.data).astype('bool')
            else:
                data = ~(self.data & mask).astype('bool')
            return pixelmap(data=data)

    def as_eclipse_pixelmap(self, mask=None):

        '''
           Export this bitmask as a proper Eclipse pixelmap.

           If mask is None, a logical-OR of all masks is returned, else
           a pixelmap of the specified mask is returned.

           mask: mask of bits to collapse to pixelmap
        '''

        self.log('bitmask as_eclipse_pixelmap', 'verbose')
        return self.as_pixelmap(mask=mask).as_eclipse_pixelmap()

    def add_bitmask(self, bmask):

        '''
           Merge a bitmask into this bitmask.

           bmask: a bitmask object
        '''

        self.log('bitmask add_bitmask', 'verbose')
        if self.data is not None:
            self.data |= bmask.data.astype(self.datatype)
        else:
            self.data  = bmask.data.astype(self.datatype)

    def del_bitmask(self, bmask):

        '''
           Remove a bitmask from this bitmask.

           bmask: a bitmask object
        '''

        self.log('bitmask del_bitmask', 'verbose')
        if self.data is not None:
            self.data &= ~bmask.data.astype(self.datatype)
        if self.conserve:
            self._clean_bitmask()

    def add_pixelmap(self, pmap, bit):

        '''
           Merge a pixelmap into this bitmask.

           pmap: a pixelmap object to create bitmask from
            bit: the bit to set for this pixelmap
        '''

        self.log('bitmask add_pixelmap', 'verbose')
        if self.data is not None:
            self.data |= ((~pmap.data)<<bit).astype(self.datatype)
        else:
            self.data  = ((~pmap.data)<<bit).astype(self.datatype)

    def del_pixelmap(self, pmap, bit):

        '''
           Remove a pixelmap from this bitmask.

           pmap: a pixelmap object to create bitmask from
            bit: the bit of the pixelmap to remove
        '''

        self.log('bitmask del_pixelmap', 'verbose')
        if self.data is not None:
            self.data &= ~((~pmap.data)<<bit).astype(self.datatype)
        if self.conserve:
            self._clean_bitmask()

    def has_bit(self, bit=None):

        '''
           Check this bitmask for a specific bit.

           If bit is None, the result of a logical-OR of all masks is
           returned, else the existence (are any pixels set) of the specified
           mask is returned.

           bit: the bit to test for
        '''

        self.log('bitmask has_bit', 'verbose')
        if self.data is None:
            return False
        if bit is None:
            return self.data.any()
        else:
            return (self.data & 1<<bit).astype('bool').any()

    def which_bits(self):

        '''
           Return a list of the bits set in this bitmask.
        '''

        self.log('bitmask which_bits', 'verbose')
        bits = []
        for bit in range(self.bits):
            if self.has_bit(bit=bit):
                bits.append(bit)
        return bits

    def count(self):

        '''
           Return the number of flagged pixels (non-zero values) in the
           bitmask.
        '''

        self.log('bitmask count', 'verbose')
        return self.data.nonzero()[0].shape[0]

    def save(self, filename=None, hdr=None, datatype='int32', clobber=True,
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

        self.log('bitmask save', 'verbose')
        if datatype not in EXPORT_TYPES:
            raise DARMAError('ERROR -- unsupported export datatype: %s not in %s' % (datatype, EXPORT_TYPES))
        DataStruct.save(self, filename=filename, hdr=hdr, datatype=datatype, clobber=clobber, update_datamd5=update_datamd5, option=option)

    #def __getitem__(self, key):

    #    '''
    #       Get an item from the data array using FITS convention indexes.
    #       x.__getitem__(i) <==> x[i]
    #    '''

    #    if self.data is None:
    #        return None

    #    key = _adjust_index(key)
    #    return bitmask(data=self.data.__getitem__(key))

