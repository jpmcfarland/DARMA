'''
Unit test for DARMA common
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError, unicode

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
#                                                                      #
#                         common version tests                         #
#                                                                      #
########################################################################


class common_version_test(unittest.TestCase):

    '''
       Is the underlying FITS handling library version consistent?
    '''

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

if __name__ == '__main__':
    unittest.main()
