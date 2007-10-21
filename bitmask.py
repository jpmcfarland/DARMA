'''
   A bitmask to store bad pixel information.
'''

__version__ = '@(#)$Revision$'

import pyfits, os

from common import Array
from common import DARMAError, _HAS_NUMPY, DataStruct, _adjust_index
from pixelmap import pixelmap

class bitmask(DataStruct):

    '''
       A bit mask in which to store up to 8 types of pixelmaps.
    '''

    pixelmap_type = {
                     'NonNumberMap'      :   1,
                     'SaturatedPixelMap' :   2,
                     'HotPixelMap'       :   4,
                     'ColdPixelMap'      :   8,
                     'SatelliteMap'      :  16,
                     'CosmicMap'         :  32,
                     'LinearityMap'      :  64,
                     'undefined'         : 128,
                    }

    def __init__(self, filename=None, extension=0, pmap=None, map_type=None,
                 readonly=0, *args, **kwargs):

        '''
           Construct a bit mask object that can store up to 8 bad pixel maps.

            filename: FITS filename to load bitmask from
           extension: FITS extension to use
                pmap: a pixelmap object to create bitmask from
            map_type: the type of pixelmap object (see bitmask.pixelmap_type)
            readonly: is filename readonly

           If there is no filename and no pmap, bitmask.data is set to None.
           If both self.filename and self.pmap are set, the bitmask is created
           from self.pmap.
        '''

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError, 'DARMA pixel functionality not possible: cannot import module numpy'

        self.filename  = filename
        self.extension = extension
        self.pmap      = pmap
        self.map_type  = map_type
        self.readonly  = readonly

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError, 'Filename: %s not found!' % self.filename

    def load(self):

        '''
           Proxy for load_bitmask()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self.load_bitmask()

    def load_bitmask(self):

        '''
           Load the bitmask from a file or a Pixelmask.
        '''

        filename  = self.filename
        extension = self.extension
        pmap      = self.pmap
        map_type  = self.map_type

        if pmap is None:
            if filename is not None:
                try:
                    self._data = pyfits.getdata(filename, extension)
                    if self._data.dtype.name != 'uint8':
                        self._data = self._data.astype('uint8')
                    self.clean_bitmask()
                except Exception, e:
                    raise DARMAError, 'Error loading bitmask from %s: %s' % (filename, e)
            else:
                self._data = None
        else:
            if map_type not in self.pixelmap_type:
                raise DARMAError, 'Unrecognized pixelmap type!  Did you specify one with map_type?'
            self._data = ((~pmap.data).astype('uint8') *
                          self.pmap_type[map_type])
            self.clean_bitmask()
        self.pmap = None
        self.map_type = None

        self._set_shape_attribute()
        self._set_datatype_attribute()

    def clean_bitmask(self):

        '''
           If the bitmask is masking nothing (i.e. no bits set), eliminate its
           data by setting self.data to None.
        '''
        #PERFORMANCE ISSUE
        if self.data is not None and not self.data.any():
            self.del_bitmask()

    def del_bitmask(self):

        '''
           Eliminate the bitmask data by setting self.data to None.

           NOTE: All masked information will be lost!
        '''

        self.data = None

    def as_pixelmap(self, map_type=None):

        '''
           Export this bitmask as a pixelmap.

           If map_type is None, a logical-OR of all masks is returned, else
           the specified pixelmap is returned.

           map_type: type of pixelmap to create (see bitmask.pixelmap_type)
        '''

        if self.data is None:
            return pixelmap()
        else:
            if map_type is None:
                return pixelmap(data=~self.data.astype('bool'))
            else:
                mask = ~self.data & self.pmap_type[map_type]
                return pixelmap(data=mask)

    def add_pixelmap(self, pmap, map_type):

        '''
           Merge a pixelmap into this bitmask.

               pmap: a pixelmap object to create bitmask from
           map_type: the type of pixelmap object (see bitmask.pixelmap_type)
        '''

        if map_type not in self.pixelmap_type:
            raise DARMAError, 'Unrecognized pixelmap type!'
        if self.data is not None:
            self.data |= ((~pmap.data).astype('uint8') *
                          self.pixelmap_type[map_type])
        else:
            self.data  = ((~pmap.data).astype('uint8') *
                          self.pixelmap_type[map_type])
        self.clean_bitmask()

    def del_pixelmap(self, pmap, map_type):

        '''
           Remove a pixelmap from this bitmask.

               pmap: a pixelmap object to create bitmask from
           map_type: the type of pixelmap object (see bitmask.pixelmap_type)
        '''

        if map_type not in self.pixelmap_type:
            raise DARMAError, 'Unrecognized pixelmap type!'
        if self.data is not None:
            self.data &= ~((~pmap.data).astype('uint8') *
                           self.pmap_type[map_type])
        self.clean_bitmask()

    def has_pixelmap(self, map_type=None):

        '''
           Check this bitmask for a specific pixelmap.

           If map_type is None, the result of a logical-OR of all masks is
           returned, else the existence (are any pixels set) of the specified
           mask is returned.

           map_type: type of pixelmap to create (see bitmask.pixelmap_type)
        '''

        if self.data is None:
            return False
        if map_type is None:
            return self.data.any()
        else:
            return (~(~self.data & self.pixelmap_type[map_type]).astype('bool')).any()

    def which_pixelmap(self, map_type=None):

        '''
           Return a list of the types of all the pixelmap contained in this
           bitmask.
        '''

        if self.has_pixelmap():
            map_types = []
            for map_type in self.pixelmap_type.keys():
                if self.has_pixelmap(map_type=map_type):
                    map_types.append(map_type)
            return map_types

        return []

    def __getitem__(self, key):

        '''
           Get an item from the data array using FITS convention indexes.
           x.__getitem__(i) <==> x[i]
        '''

        if self.data is None:
            return None

        key = _adjust_index(key)
        return bitmask(data=self.data.__getitem__(key))

