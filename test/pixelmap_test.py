'''
Unit test for DARMA pixelmap
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError
from .. import image, image_generator

import unittest, os

def build_test_data():

    '''
       This function builds fits files to be used in testing

       The function returns a list of names of generated files
    '''

    name_list = []

    print('Generating testdata...')

    ig = image_generator.image_generator(128, 128)
    for i in range(1,3):
        name = 'IM%02d.fits' % i
        ima = ig.generate_random_gauss(0.5*i, 1.0*i)
        ima.save(name)
        name_list.append(name)

    return name_list

def delete_test_data(name_list):

    '''
       Clean up the mess
    '''

    for filename in name_list:
        os.remove(filename)


class pixelmap_tests(unittest.TestCase):

    def test_make_map(self):
        ima = image.image('IM01.fits')
        pm = ima.thresh_to_pixmap(0.8, 1.2)
        pm.dump_pixelmap('pm.fits')
        self.assertTrue(os.path.exists('pm.fits'))
        os.remove('pm.fits')

    def test_inspect_map(self):
        ima = image.image('IM01.fits')
        pm = ima.thresh_to_pixmap(0.8, 1.2)
        self.assertEqual(pm.xsize(), ima.xsize())
        self.assertEqual(pm.ysize(), ima.ysize())

test_suite = unittest.TestSuite()
test_suite.addTest(unittest.makeSuite(pixelmap_tests))

if __name__ == '__main__':
    name_list = build_test_data()
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)
    delete_test_data(name_list)

