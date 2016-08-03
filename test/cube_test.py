'''
Unit test for DARMA cube
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError
from .. import image, cube, image_generator

import unittest, os

def build_test_data():

    '''
       This function builds fits files to be used in testing

       The function returns a list of names of generated files
    '''

    name_list = []

    print('Generating testdata...')

    ig = image_generator.image_generator(128, 128)
    for i in range(1,6):
        name = 'IM%02d.fits' % i
        ig.generate_random_gauss(0.5*i, 1.0*i).save(name)
        name_list.append(name)

    ig = image_generator.image_generator(129, 129)
    ig.generate_random_gauss(0.5*i, 1.0*i).save('IM01.large.fits')
    name_list.append('IM01.large.fits')
    return name_list

def delete_test_data(name_list):

    '''
       Clean up the mess
    '''

    for filename in name_list:
        os.remove(filename)


class cube_tests(unittest.TestCase):

    def setUp(self):
        self.im_list = [image.image('IM01.fits'),
                        image.image('IM02.fits'),
                        image.image('IM03.fits'),
                        image.image('IM04.fits')]
        self.cube = cube.cube(image_list=self.im_list)

    def tearDown(self):
        self.im_list = None
        self.cube = None

    def test_indexing(self):
        for ima1, ima2 in zip(self.cube, self.im_list):
            self.assertTrue(ima1 is ima2)

    def test_append(self):
        self.cube.append(image.image('IM01.fits'))
        st1 = self.cube[0].stat()
        st2 = self.cube[-1].stat()
        self.assertEqual(st1.median, st2.median)

class cube_arithmetic_tests(unittest.TestCase):

    def setUp(self):
        self.cube = cube.cube(image_list=[image.image('IM01.fits'),
                                          image.image('IM02.fits'),
                                          image.image('IM03.fits'),
                                          image.image('IM04.fits')])
        self.ima = image.image('IM05.fits')

    def tearDown(self):
        self.cube = None
        self.ima = None

    def test_add_cst(self):
        res = self.cube+2

    def test_iadd_cst(self):
        self.cube+=2

    def test_sub_cst(self):
        res = self.cube-2

    def test_isub_cst(self):
        self.cube-=2

    def test_mul_cst(self):
        res = self.cube*2

    def test_imul_cst(self):
        self.cube*=2

    def test_div_cst(self):
        res = self.cube/2

    def test_idiv_cst(self):
        self.cube/=2

    def test_pow_cst(self):
        res = self.cube ** 2

    def test_ipow_cst(self):
        self.cube **= 2

    def test_add_ima(self):
        res = self.cube+self.ima

    def test_iadd_ima(self):
        self.cube+=self.ima

    def test_sub_ima(self):
        res = self.cube-self.ima

    def test_isub_ima(self):
        self.cube-=self.ima

    def test_mul_ima(self):
        res = self.cube*self.ima

    def test_imul_ima(self):
        self.cube*=self.ima

    def test_div_ima(self):
        res = self.cube/self.ima

    def test_idiv_ima(self):
        self.cube/=self.ima

    def test_add_cube(self):
        res = self.cube+self.cube

    def test_iadd_cube(self):
        self.cube+=self.cube

    def test_sub_cube(self):
        res = self.cube-self.cube

    def test_isub_cube(self):
        self.cube-=self.cube

    def test_mul_cube(self):
        res = self.cube*self.cube

    def test_imul_cube(self):
        self.cube*=self.cube

    def test_div_cube(self):
        res = self.cube/self.cube

    def test_idiv_cube(self):
        self.cube/=self.cube

class cube_norm_tests(unittest.TestCase):

    def setUp(self):
        self.cube = cube.cube(image_list=[image.image('IM01.fits'),
                                          image.image('IM02.fits')])
    def tearDown(self):
        self.cube = None

    def test_normalize_mean(self):
        self.cube.normalize_mean()
        st = self.cube[0].stat()
        self.assertTrue(abs(st.avg_pix-1.0) < 0.0001)

    def test_normalize_median(self):
        self.cube.normalize_median()
        st = self.cube[0].stat()
        self.assertTrue(abs(st.median-1.0) < 0.0001)

    def test_normalize_flux(self):
        self.cube.normalize_flux()
        st = self.cube[0].stat()
        self.assertTrue(abs(st.flux-1.0) < 0.0001)

    def test_normalize_absolute_flux(self):
        self.cube.normalize_absolute_flux()
        st = self.cube[0].stat()
        self.assertTrue(abs(st.absflux-1.0) < 0.0001)

    def test_normalize_range(self):
        self.cube.normalize_range()
        st = self.cube[0].stat()
        self.assertTrue(abs(st.max_pix-1.0) < 0.0001)
        self.assertTrue(abs(st.min_pix) < 0.0001)

class cube2image_tests(unittest.TestCase):
    def setUp(self):
        self.cube = cube.cube(image_list=[image.image('IM01.fits'),
                                          image.image('IM02.fits'),
                                          image.image('IM03.fits'),
                                          image.image('IM04.fits')])

    def tearDown(self):
        self.cube = None

    def test_sum(self):
        sum = self.cube.sum()

    def test_average(self):
        avg = self.cube.average()

    def test_median(self):
        med = self.cube.median()

    def test_stdev(self):
        stdev = self.cube.stdev()

    # Tests feature that is currently unimplemented.
    def test_average_rej(self):
        avg = self.cube.average_with_rejection(0, 1)

    # Tests feature that is currently unimplemented.
    def test_average_sigclip(self):
        avg = self.cube.average_with_sigma_clip(2, 1, 0,0,3.0, -999, 0.0, 1.0)

test_suite = unittest.TestSuite()
test_suite.addTest(unittest.makeSuite(cube_tests))
test_suite.addTest(unittest.makeSuite(cube_arithmetic_tests))
test_suite.addTest(unittest.makeSuite(cube_norm_tests))
test_suite.addTest(unittest.makeSuite(cube2image_tests))

if __name__ == '__main__':
    name_list = build_test_data()

    test_runner = unittest.TextTestRunner()

    print('Testing images...')
    test_runner.run(test_suite)

    delete_test_data(name_list)

