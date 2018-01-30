"""
Unit test for DARMA common
"""

__version__ = '@(#)$Revision$'

from ..common import DARMAError, unicode, StatStruct, DataStruct

import unittest
import os
import collections
import numpy as Array

# AstroPy/PyFITS compatibility
try:
    if 'DARMA_PYFITS' in os.environ:
        raise Exception()
    from astropy.io import fits
    from astropy import __version__
    fits.__version__ = __version__
    print('DARMA unittests using Astropy version %s and NumPy version %s' % (fits.__version__, Array.__version__))
except:
    import pyfits as fits
    print('DARMA unittests using PyFITS version %s and NumPy version %s' % (fits.__version__, Array.__version__))

########################################################################
#
# common version tests
#


class common_version_test(unittest.TestCase):

    """
       Is the underlying FITS handling library version consistent?
    """

    def setUp(self):
        from ..common import fits as darma_fits, Array as darma_array
        self.darma_fits_version = darma_fits.__version__
        self.darma_array_version = darma_array.__version__
        del darma_fits, darma_array

    def tearDown(self):
        pass

    def test_darma_version(self):
        print(self.__class__.__name__)
        self.assertEqual(self.darma_fits_version, fits.__version__,
                         msg='DARMA fits version does not match test fits version')

    def test_array_version(self):
        print(self.__class__.__name__)
        self.assertEqual(self.darma_array_version, Array.__version__,
                         msg='DARMA Array version does not match test Array version')

########################################################################
#
# common StatStruct tests
#

class common_statstruct_load_test(unittest.TestCase):

    """
       Is the loaded statistics structure consistent?
    """

    def setUp(self):
        self.stat_tuple = (
            0.1, # min_pix
            0.2, # max_pix
            0.3, # avg_pix
            0.4, # median
            0.5, # stdev
            0.6, # energy
            0.7, # flux
            0.8, # absflux
            1,   # min_x
            2,   # min_y
            3,   # max_x
            4,   # max_y
            5,   # npix
            )

    def tearDown(self):
        pass

    def test_statstruct_load(self):
        print(self.__class__.__name__)
        stats = StatStruct(self.stat_tuple)
        self.assertEqual(stats.min_pix, 0.1, msg='min_pix value not set correctly')
        self.assertEqual(stats.max_pix, 0.2, msg='max_pix value not set correctly')
        self.assertEqual(stats.avg_pix, 0.3, msg='avg_pix value not set correctly')
        self.assertEqual(stats.median, 0.4, msg='median value not set correctly')
        self.assertEqual(stats.stdev, 0.5, msg='stdev value not set correctly')
        self.assertEqual(stats.energy, 0.6, msg='energy value not set correctly')
        self.assertEqual(stats.flux, 0.7, msg='flux value not set correctly')
        self.assertEqual(stats.absflux, 0.8, msg='absflux value not set correctly')
        self.assertEqual(stats.min_x, 1, msg='min_x value not set correctly')
        self.assertEqual(stats.min_y, 2, msg='min_y value not set correctly')
        self.assertEqual(stats.max_x, 3, msg='max_x value not set correctly')
        self.assertEqual(stats.max_y, 4, msg='max_y value not set correctly')
        self.assertEqual(stats.npix, 5, msg='npix value not set correctly')

class common_statstruct_show_test(unittest.TestCase):

    """
       Show the StatStruct.
    """

    def setUp(self):
        self.stat_tuple = (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,1,2,3,4,5)

    def tearDown(self):
        pass

    def test_statstruct_show(self):
        print(self.__class__.__name__)
        stats = StatStruct(self.stat_tuple)
        self.assertIsNone(stats.show(), msg='StatStruct not shown correctly')

class common_statstruct_dump_test(unittest.TestCase):

    """
       Dump the StatStruct (alias for show).
    """

    def setUp(self):
        self.stat_tuple = (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,1,2,3,4,5)

    def tearDown(self):
        pass

    def test_statstruct_dump(self):
        print(self.__class__.__name__)
        stats = StatStruct(self.stat_tuple)
        self.assertIsNone(stats.dump(), msg='StatStruct not shown correctly')

########################################################################
#
# common DataStruct tests
#

if __name__ == '__main__':
    unittest.main()
