'''
Unit test for DARMA image
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError
from .. import image, header, image_generator

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
        ig.generate_random_gauss(0.5*i, 1.0*i).save(name)
        name_list.append(name)

    ig = image_generator.image_generator(129, 129)
    ig.generate_random_gauss(0.5*i, 1.0*i).save('IM01.large.fits')
    name_list.append('IM01.large.fits')
    return name_list

def delete_test_data(name_list):

    '''Clean up the mess'''

    for filename in name_list:
        os.remove(filename)

class image_tests(unittest.TestCase):

    def test_load_good_filename(self):
        ima = image.image('IM01.fits')
        self.assertIsNotNone(ima.data)

    def test_load_bad_filename(self):
        self.assertRaises(DARMAError, image.image, 'IM.fits')

    def test_save_good(self):
        image.image('IM01.fits').save('IM06.fits')
        self.failUnless(os.path.exists('IM06.fits'))
        os.remove('IM06.fits')

    def test_save_header_good(self):
        ima = image.image('IM01.fits')
        hdr = header.header()
        hdr.default()
        hdr['AKEY'] = 1
        ima.save('IM06.fits', hdr)
        self.failUnless(os.path.exists('IM06.fits'))
        os.remove('IM06.fits')

    def test_save_bad_no_image(self):
        ima = image.image()
        self.assertRaises(DARMAError, ima.save, 'IM06.fits')

    def test_save_bad_filename(self):
        ima = image.image('IM01.fits')
        self.assertRaises(DARMAError, ima.save, 'dddd/IM06.fits')

    def test_save_header_bad_filename(self):
        ima = image.image('IM01.fits')
        hdr = header.header()
        hdr.default()
        hdr['AKEY'] = 1
        self.assertRaises(DARMAError, ima.save, 'dddd/IM06.fits', hdr)

    def test_copy(self):
        ima = image.image('IM01.fits')
        newima = ima.copy()
        self.assertIsNotNone(ima.data)
        self.assertIsNotNone(newima.data)

    def test_size(self):
        ima = image.image('IM01.fits')
        self.assertEqual(ima.xsize(), 128)
        self.assertEqual(ima.ysize(), 128)

##     def test_fastcopy_reloadable(self):
##         ima = image.image('IM01.fits')
##         newima = ima.fast_copy()
##         self.assertFalse(ima._p_cube)
##         self.assertTrue(newima.p_ima)

##     def test_fastcopy_not_reloadable(self):
##         ima = image.image('IM01.fits').fast_copy()
##         newima = ima.fast_copy()
##         self.assertTrue(ima.p_ima)
##         self.assertTrue(newima.p_ima)


class image_statistics_tests(unittest.TestCase):

    def setUp(self):
        self.ima = image.image('IM01.fits')

    def tearDown(self):
        self.ima = None

    def test_stat(self):
        s = self.ima.stat()

    def test_stats_no_median(self):
        s = self.ima.stat(domedian=0)
        self.assertEqual(s.median, 0.0)

    def test_stat_opt_pixmap(self):
        pm = self.ima.thresh_to_pixmap(0.8, 1.2)
        s = self.ima.stat_opts(pixmap = pm)
        self.assertNotEqual(s.stdev, 0.0)

    def test_stat_opt_range(self):
        s = self.ima.stat_opts(pixrange=[0.8, 1.2])
        self.assertNotEqual(s.stdev, 0.0)

    def test_stat_opt_zone(self):
        s1 = self.ima.stat_opts(zone=[10, 10, 20, 20])
        s2 = self.ima.extract_region(10, 10, 20, 20).stat()
        self.assertEqual(s1.avg_pix, s2.avg_pix)

    def test_iter_stat(self):
        s = self.ima.iter_stat()
        self.assertEqual(s.convergence, 1)

    def test_iter_stat_opt_zone(self):
        s1 = self.ima.iter_stat_opts(zone=[10, 10, 20, 20])
        s2 = self.ima.extract_region(10, 10, 20, 20).iter_stat()
        self.assertEqual(s1.avg_pix, s2.avg_pix)

class image_arithmetic_tests(unittest.TestCase):

    def setUp(self):
        self.c1 = image.image('IM01.fits')
        self.c2 = image.image('IM02.fits')
        self.bad = image.image('IM01.large.fits')
        self.stat = self.c1.stat()

    def tearDown(self):
        self.c1  = None
        self.c2  = None
        self.bad = None

    def test_add(self):
        res = self.c1+self.c2

    def test_add_scalar(self):
        res = self.c1 + 2
        rs = res.stat()
        self.assertTrue(abs(self.stat.median+2 - rs.median)<0.0001)

    def test_radd(self):
        res = 1+self.c1

    def test_add_bad(self):
        self.assertRaises(ValueError, eval, "self.c1+self.bad")

    def test_sub(self):
        res = self.c1-self.c2

    def test_sub_scalar(self):
        res = self.c1 - 2
        rs = res.stat()
        self.assertTrue(abs(self.stat.median-2 - rs.median)<0.0001)

    def test_rsub(self):
        res = 1-self.c1

    def test_sub_bad(self):
        self.assertRaises(ValueError, eval, "self.c1-self.bad")

    def test_mul(self):
        res = self.c1*self.c2

    def test_mul_scalar(self):
        res = self.c1 * 2
        rs = res.stat()
        self.assertTrue(abs(self.stat.median*2 - rs.median)<0.0001)

    def test_rmul(self):
        res = 2*self.c1

    def test_mul_bad(self):
        self.assertRaises(ValueError, eval, "self.c1*self.bad")

    def test_div(self):
        res = self.c1/self.c2

    def test_div_scalar(self):
        res = self.c1 / 2
        rs = res.stat()
        self.assertTrue(abs(self.stat.median/2 - rs.median)<0.0001)

    #def test_zerodiv(self):
    #    self.assertRaises(ZeroDivisionError, eval, "self.c1/0")

    def test_rdiv(self):
        res = 1/self.c1

    def test_div_bad(self):
        self.assertRaises(ValueError, eval, "self.c1/self.bad")

    def test_pow(self):
        res = self.c1**0.5

    def test_pow_bad(self):
        self.assertRaises(ValueError, eval, "self.c1**self.bad")

    def test_rpow(self):
        res = 10 ** self.c1

    def test_ipow(self):
        self.c1 **= 0.5

class image_norm_tests(unittest.TestCase):

    def setUp(self):
        self.ima = image.image('IM01.fits')

    def tearDown(self):
        self.ima = None

    def test_normalize_mean(self):
        self.ima.normalize_mean()
        st = self.ima.stat()
        self.assertTrue(abs(st.avg_pix-1.0) < 0.0001)

    def test_normalize_median(self):
        self.ima.normalize_median()
        st = self.ima.stat()
        self.assertTrue(abs(st.median-1.0) < 0.0001)

    def test_normalize_flux(self):
        self.ima.normalize_flux()
        st = self.ima.stat()
        self.assertTrue(abs(st.flux-1.0) < 0.0001)

    def test_normalize_absolute_flux(self):
        self.ima.normalize_absolute_flux()
        st = self.ima.stat()
        self.assertTrue(abs(st.absflux-1.0) < 0.0001)

    def test_normalize_range(self):
        self.ima.normalize_range()
        st = self.ima.stat()
        self.assertTrue(abs(st.max_pix-1.0) < 0.0001)
        self.assertTrue(abs(st.min_pix) < 0.0001)

class image_filter_tests(unittest.TestCase):

    def setUp(self):
        self.ima = image.image('IM01.fits')

    def tearDown(self):
        self.ima = None

    def test_clean_bad_pixels(self):
        pixmap = self.ima.thresh_to_pixmap(-2.0, 2.0)
        result = self.ima.clean_bad_pixels(pixmap, 5)

    # Tests feature that is currently unimplemented.
    def test_mean(self):
        result = self.ima.filter_mean()

    # Tests feature that is currently unimplemented.
    def test_dx(self):
        result = self.ima.filter_dx()

    # Tests feature that is currently unimplemented.
    def test_dy(self):
        result = self.ima.filter_dy()

    # Tests feature that is currently unimplemented.
    def test_dx2(self):
        result = self.ima.filter_dx2()

    # Tests feature that is currently unimplemented.
    def test_dy2(self):
        result = self.ima.filter_dy2()

    # Tests feature that is currently unimplemented.
    def test_contour1(self):
        result = self.ima.filter_contour1()

    # Tests feature that is currently unimplemented.
    def test_contour2(self):
        result = self.ima.filter_contour2()

    # Tests feature that is currently unimplemented.
    def test_contour3(self):
        result = self.ima.filter_contour3()

    # Tests feature that is currently unimplemented.
    def test_contrast1(self):
        result = self.ima.filter_contrast1()

class fft_tests(unittest.TestCase):

    def test_roundtrip(self):
        real = image.image('IM01.fits')
        r, i = image.fft(real)
        r, i = image.fft(r, i, direction=1)
        self.assertTrue(abs((real/r).stat().median-1)<0.000001)
        self.assertTrue(abs(i.stat().median)<0.000001)

class make_image_tests(unittest.TestCase):

    def test_make(self):
        ima = image.make_image(1024, 1024)
        self.assertEqual(ima.xsize(), 1024)
        self.assertEqual(ima.ysize(), 1024)

class image_QC_tests(unittest.TestCase):

    def test_signtest(self):
        self.ima = image.image('IM01.fits')
        result, number = self.ima.run_signtest(4,8)


    def test_run_flattest(self):
        self.ima = image.image('IM01.fits')
        result, number = self.ima.run_flattest(4,8)

    def test_run_flatfittingtest(self):
        self.ima = image.image('IM01.fits')
        result, number = self.ima.run_flatfittingtest(4,8,4,8)

    # Tests feature that is currently unimplemented.
    def test_imsurfit(self):
        self.ima = image.image('IM01.fits')
        result = self.ima.run_imsurfit(4,8)

    # Tests feature that is currently unimplemented.
    def test_run_counttest(self):
        self.ima = image.image('IM01.fits')
        result = self.ima.run_counttest(1)

test_suite = unittest.TestSuite()
test_suite.addTest(unittest.makeSuite(image_tests))
test_suite.addTest(unittest.makeSuite(image_statistics_tests))
test_suite.addTest(unittest.makeSuite(image_arithmetic_tests))
test_suite.addTest(unittest.makeSuite(image_norm_tests))
test_suite.addTest(unittest.makeSuite(image_filter_tests))
test_suite.addTest(unittest.makeSuite(fft_tests))
test_suite.addTest(unittest.makeSuite(make_image_tests))
test_suite.addTest(unittest.makeSuite(image_QC_tests))

if __name__ == '__main__':
    name_list = build_test_data()
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)
    delete_test_data(name_list)

