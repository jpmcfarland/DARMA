'''Unit test for header.
'''

__version__ = '@(#)$Revision$'

import unittest, os
from astro.util.darma import header, image, image_generator
from astro.util.darma.common import DARMAError

def build_test_data():
    '''
       This function builds fits files to be used in testing

       The function returns a list of names of generated files
    '''
    name_list = []
    ig = image_generator.image_generator(128, 128)
    ima = ig.generate_random_gauss(0.5, 1.0)
    ima.save('IM01.fits')
    name_list.append('IM01.fits')
    return name_list

def delete_test_data(name_list):
    '''Clean up the mess'''

    for filename in name_list:
        os.remove(filename)

class header_read_tests(unittest.TestCase):

    def test_bad_read(self):
        self.assertRaises(DARMAError, header.header, 'Unknown.fits')

    def test_add(self):
        h = header.header()
        h.default()
        h.add('AKEY', 1, '')
        h.add_after('AKEY', 'BKEY', 2, '')
        h['CKEY'] = 3
        self.assertEqual(h['AKEY'], 1)
        self.assertEqual(h['BKEY'], 2)
        self.assertEqual(h['CKEY'], 3)

    def test_copy(self):
        h1 = header.header()
        h1.default()
        h1['AKEY'] = 'Help'
        h2 = h1.copy()
        self.assertEqual(h1['AKEY'], 'Help')

    def test_merge(self):
        h1, h2 = header.header(), header.header()
        h1.default()
        h1['AKEY'] = 1
        h1['BKEY'] = 2

        h2.new()
        h2['BKEY'] = 3
        # Automatic verify will raise an error without this.
        h2._IS_VERIFIED = True
        h2['CKEY'] = 4
        # Automatic verify will raise an error without this.
        h2._IS_VERIFIED = True

        h3 = h1.merge(h2)
        self.assertEqual(h3['AKEY'], 1)
        self.assertEqual(h3['BKEY'], 3)
        self.assertEqual(h3['CKEY'], 4)

class header_write_tests(unittest.TestCase):

    def setUp(self):
        self.hdr = header.header()
        self.hdr.default()
        self.ima = image.image('IM01.fits')

    def tearDown(self):
        self.hdr = None

    def _test_write(self, val):
        '''Auxilary function to test writing header'''
        self.hdr['MYKEY'] = val
        self.assertEqual(self.hdr['MYKEY'], val)
        self.ima.save('tmp.fits', self.hdr)
        newhdr = header.header('tmp.fits')
        self.assertEqual(newhdr['MYKEY'], val)
        os.remove('tmp.fits')

    def test_write_int(self):
        self._test_write(1)

    def test_write_float(self):
        self._test_write(0.5)

    def test_write_str(self):
        self._test_write('abcd')

header_test_suite = unittest.TestSuite()
header_test_suite.addTest(unittest.makeSuite(header_read_tests))
header_test_suite.addTest(unittest.makeSuite(header_write_tests))

if __name__ == '__main__':
    l = build_test_data()
    test_runner = unittest.TextTestRunner()
    test_runner.run(header_test_suite)
    delete_test_data(l)

