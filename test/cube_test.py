'''
Unit test for DARMA cube
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError, unicode
from ..cube import cube
from .common_test import fits, Array

import unittest
import os
import collections

SINGLE1 = 'SEF1.fits'
SINGLE2 = 'SEF2.fits'
#SINGLES = [SINGLE1, SINGLE2]
SINGLES = [SINGLE1]
MULTI1 = 'MEF1.fits'
MULTI2 = 'MEF2.fits'
#MULTIS = [MULTI1, MULTI2]
MULTIS = [MULTI1]
EMPTY1 = 'EMPTY1.fits'
EMPTY2 = 'EMPTY2.fits'
#EMPTYS = [EMPTY1, EMPTY2]
EMPTYS = [EMPTY1]
ZERO1 = 'ZERO1.fits'
ZERO2 = 'ZERO2.fits'
#ZEROS = [ZERO1, ZERO2]
ZEROS = [ZERO1]
ONE1 = 'ONE1.fits'
ONE2 = 'ONE2.fits'
#ONES = [ONE1, ONE2]
ONES = [ONE1]
FILENAMES = SINGLES + MULTIS + EMPTYS + ZEROS + ONES


def build_test_data_sef():
    '''
       This function builds SEF files to be used in testing
    '''
    data = Array.asanyarray([
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
    ])
    for filename in SINGLES:
        fits.PrimaryHDU(data=data).writeto(filename, output_verify='silentfix', clobber=True)


def build_test_data_mef():
    '''
       This function builds MEF files to be used in testing
    '''
    data = Array.asanyarray([
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
        Array.random.normal(1.0, 0.5, (32, 16)).astype('float32'),
    ])
    for filename in MULTIS:
        hdu0 = fits.PrimaryHDU()
        hdu1 = fits.ImageHDU(data=data)
        update_header(hdu1.header, 'EXTNAME', 'EXT1')
        hdu2 = fits.ImageHDU(data=data)
        update_header(hdu2.header, 'EXTNAME', 'EXT2')
        hdu3 = fits.ImageHDU(data=data)
        update_header(hdu3.header, 'EXTNAME', 'EXT3')
        hdus = fits.HDUList([hdu0, hdu1, hdu2, hdu3])
        hdus.writeto(filename, output_verify='silentfix', clobber=True)
        hdus.close()


def build_test_data_empty():
    '''
       This function builds dataless files to be used in testing
    '''
    for filename in EMPTYS:
        fits.PrimaryHDU().writeto(filename, output_verify='silentfix', clobber=True)


def build_test_data_zero():
    '''
       This function builds SEF files with all zero data array to be
       used in testing
    '''
    data = Array.asanyarray([
        Array.zeros((32, 16), dtype='int32'),
        Array.zeros((32, 16), dtype='int32'),
        Array.zeros((32, 16), dtype='int32'),
    ])
    for filename in ZEROS:
        fits.PrimaryHDU(data=data).writeto(filename, output_verify='silentfix', clobber=True)


def build_test_data_one():
    '''
       This function builds SEF files with all one data array to be
       used in testing
    '''
    data = Array.asanyarray([
        Array.ones((32, 16), dtype='int32'),
        Array.ones((32, 16), dtype='int32'),
        Array.ones((32, 16), dtype='int32'),
    ])
    for filename in ONES:
        fits.PrimaryHDU(data=data).writeto(filename, output_verify='silentfix', clobber=True)


def delete_test_data():
    '''
       This function deletes fits files used in testing
    '''
    for filename in FILENAMES:
        if os.path.exists(filename):
            os.remove(filename)

########################################################################
#                                                                      #
#                           cube load tests                            #
#                                                                      #
########################################################################


class cube_load_error_test(unittest.TestCase):

    '''
       Do cubes loaded from bogus sources raise errors?
    '''

    def setUp(self):
        build_test_data_zero()
        build_test_data_one()

    def tearDown(self):
        delete_test_data()

    def test_load_error(self):
        print(self.__class__.__name__)
        self.assertRaises(DARMAError, cube, filename='Unknown.fits')
        cub = cube(filename=ZERO1, extension=1)
        self.assertRaises(DARMAError, cub.load)


class cube_load_empty_test(unittest.TestCase):

    '''
       Are cubes loaded without data empty?
    '''

    def setUp(self):
        build_test_data_empty()

    def tearDown(self):
        delete_test_data()

    def test_load_empty(self):
        print(self.__class__.__name__)
        cub = cube()
        self.assertIsNone(cub.data, msg='data array from empty cube not None')
        cub = cube(filename=EMPTY1)
        self.assertIsNone(cub.data, msg='data array from dataless FITS not None')

if __name__ == '__main__':
    unittest.main()
