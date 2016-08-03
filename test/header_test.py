'''
Unit test for DARMA header
'''

__version__ = '@(#)$Revision$'

from ..common import DARMAError, fits as darma_fits, Array as darma_array, unicode
darma_fits_version = darma_fits.__version__
darma_array_version = darma_array.__version__
del darma_fits, darma_array
from ..header import header, getval, get_headers, update_header_in_file, get_keyword

import unittest, os, collections, numpy as Array

# AstroPy/PyFITS compatibility
try:
    if 'DARMA_PYFITS' in os.environ:
        raise Exception()
    from astropy.io import fits
    from astropy import __version__
    fits.__version__ = __version__
    get_cardlist = lambda hdr: hdr.cards
    get_cardimage = lambda card: card.image
    update_header = lambda hdr, keyword, value: hdr.update([(keyword, value)])
    print('DARMA header test using Astropy version %s and NumPy version %s' % (fits.__version__, Array.__version__))
except:
    import pyfits as fits
    if fits.__version__ < '3.3':
        get_cardlist = lambda hdr: hdr.ascardlist()
        get_cardimage = lambda card: card.ascardimage()
        update_header = lambda hdr, keyword, value: hdr.update(keyword, value)
    else:
        get_cardlist = lambda hdr: hdr.cards
        get_cardimage = lambda card: card.image
        update_header = lambda hdr, keyword, value: hdr.update([(keyword, value)])
    print('DARMA header test using PyFITS version %s and NumPy version %s' % (fits.__version__, Array.__version__))

SINGLE1 = 'SEF1.fits'
SINGLE2 = 'SEF2.fits'
#SINGLES = [SINGLE1, SINGLE2]
SINGLES = [SINGLE1]
MULTI1 = 'MEF1.fits'
MULTI2 = 'MEF2.fits'
#MULTIS = [MULTI1, MULTI2]
MULTIS = [MULTI1]
ASCII1 = 'ASCII1.fits'
ASCII2 = 'ASCII2.fits'
#ASCIIS = [ASCII1, ASCII2]
ASCIIS = [ASCII1]
#FILENAMES = [SINGLE1, SINGLE2, MULTI1, MULTI2, ASCII1, ASCII2]
FILENAMES = [SINGLE1, MULTI1, ASCII1]
PRIMARY = [
    '''SIMPLE  =                    T / conforms to FITS standard                      ''',
    '''BITPIX  =                    8 / array data type                                ''',
    '''NAXIS   =                    0 / number of array dimensions                     ''',
    '''EXTEND  =                    T                                                  ''',
    ]
TYPES = [
    '''STRING  =           'string  ' / string type keyword                            ''',
    '''BOOL    =                    F / string type keyword                            ''',
    '''INT     =                    1 / string type keyword                            ''',
    '''FLOAT   =                  2.0 / string type keyword                            ''',
    ]
HIERARCH = [
    '''HIERARCH DARMA Hierarch Card 1 = 'one     '                                     ''',
    '''HIERARCH DARMA Hierarch Card 2 = 2                                              ''',
    '''HIERARCH DARMA Hierarch Card 3 = 3.0                                            ''',
    ]
# hdr['CONTKEY1'] = '1234567890'*8
# hdr['CONTKEY2'] = ('1234567890'*8, '1234567890'*8)
CONTINUE = []
#    """CONTKEY1= '1234567890123456789012345678901234567890123456789012345678901234567&'""",
#    """CONTINUE  '8901234567890'                                                       """,
#    """CONTKEY2= '1234567890123456789012345678901234567890123456789012345678901234567&'""",
#    """CONTINUE  '8901234567890&'                                                      """,
#    """CONTINUE  '&' / 1234567890123456789012345678901234567890123456789012345678901234"""
#    """CONTINUE  '' / 5678901234567890                                                 """
#    ]
BLANK = [
    '''        DARMA Blank Card 1                                                      ''',
    '''        DARMA Blank Card 2                                                      ''',
    '''        DARMA Blank Card 3                                                      ''',
    ]
#BLANKCARDS = [
#    '''BLANK KEYWORD4=           'four    ' / DARMA Blank Card 4                       ''',
#    '''BLANK KEYWORD5=                    5 / DARMA Blank Card 5                       ''',
#    '''BLANK KEYWORD6=                  6.0 / DARMA Blank Card 6                       ''',
#    ]
COMMENT = [
    '''COMMENT DARMA Comment Card 1                                                    ''',
    '''COMMENT DARMA Comment Card 2                                                    ''',
    '''COMMENT DARMA Comment Card 3                                                    ''',
    ]
COMMENTCARDS = [
    '''COMMENT KEYWORD4=           'four    ' / DARMA Comment Card 4                   ''',
    '''COMMENT KEYWORD5=                    5 / DARMA Comment Card 5                   ''',
    '''COMMENT KEYWORD6=                  6.0 / DARMA Comment Card 6                   ''',
    ]
HISTORY = [
    '''HISTORY DARMA History Card 1                                                    ''',
    '''HISTORY DARMA History Card 2                                                    ''',
    '''HISTORY DARMA History Card 3                                                    ''',
    ]
HISTORYCARDS = [
    '''HISTORY KEYWORD4=           'four    ' / DARMA Comment Card 4                   ''',
    '''HISTORY KEYWORD5=                    5 / DARMA Comment Card 5                   ''',
    '''HISTORY KEYWORD6=                  6.0 / DARMA Comment Card 6                   ''',
    ]
STRINGS = PRIMARY + TYPES + HIERARCH + CONTINUE + BLANK + COMMENT + COMMENTCARDS + HISTORY + HISTORYCARDS
CARDS = [fits.Card().fromstring(string) for string in STRINGS]

def build_test_data_sef():
    '''
       This function builds SEF files to be used in testing
    '''
    data = Array.random.normal(1.0, 0.5, (32,32)).astype('float32')
    for filename in SINGLES:
        fits.PrimaryHDU(data=data).writeto(filename, output_verify='silentfix', clobber=True)

def build_test_data_mef():
    '''
       This function builds MEF files to be used in testing
    '''
    data = Array.random.normal(1.0, 0.5, (32,32)).astype('float32')
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

def build_test_data_ascii():
    '''
       This function builds ASCII header files to be used in testing
    '''
    for filename in ASCIIS:
        hdu = fits.PrimaryHDU()
        with open(filename, 'w') as fd:
            lines = ['%s\n' % get_cardimage(card) for card in get_cardlist(hdu.header)]
            lines.append('END%s\n' % (' '*77))
            fd.writelines(lines)

def delete_test_data():
    '''
       This function deletes fits files used in testing
    '''
    for filename in FILENAMES:
        if os.path.exists(filename):
            os.remove(filename)

########################################################################
#                                                                      #
#                         header version tests                         #
#                                                                      #
########################################################################

class header_version_test(unittest.TestCase):

    '''
       Is the underlying FITS handling library version consistent?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_darma_version(self):
        self.assertEqual(darma_fits_version, fits.__version__, msg='DARMA fits version does not match test fits version')

    def test_array_version(self):
        self.assertEqual(darma_array_version, Array.__version__, msg='DARMA Array version does not match test Array version')

########################################################################
#                                                                      #
#                          header load tests                           #
#                                                                      #
########################################################################

class header_load_error_test(unittest.TestCase):

    '''
       Do headers loaded from bogus sources raise errors?
    '''

    def setUp(self):
        build_test_data_sef()

    def tearDown(self):
        delete_test_data()

    def test_load_error(self):
        self.assertRaises(DARMAError, header, filename='Unknown.fits')
        self.assertRaises(DARMAError, header, filename=SINGLE1, extension=1)
        self.assertRaises(DARMAError, header, cardlist='Unknown.fits')
        self.assertRaises(DARMAError, header, cardlist=[1,2,3])
        self.assertRaises(DARMAError, header, cardlist=())
        self.assertRaises(DARMAError, header, cardlist={})

class header_load_empty_test(unittest.TestCase):

    '''
       Are headers loaded without data empty?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_empty(self):
        hdr = header(cardlist=[])
        self.assertIsInstance(hdr, header, msg='empty cardlist header not a header instance')
        self.assertEqual(len(hdr), 0, msg='empty cardlist header is wrong length')
        hdr = header()
        self.assertIsInstance(hdr, header, msg='empty header not a header instance')
        self.assertEqual(len(hdr), 0, msg='empty header is wrong length')
        hdr = header().default()
        self.assertIsInstance(hdr, header, msg='default header not a header instance')
        self.assertEqual(len(hdr), 4, msg='default header is wrong length')
        new = hdr.new()
        self.assertIsInstance(new, header, msg='new header not a header instance')
        self.assertEqual(len(new), 0, msg='new header is wrong length')
        self.assertIsInstance(hdr, header, msg='emptied header not a header instance')
        self.assertEqual(len(hdr), 0, msg='emptied header is wrong length')

class header_load_filename_test(unittest.TestCase):

    '''
       Are headers able to be loaded properly from SEFs?
    '''

    def setUp(self):
        build_test_data_sef()

    def tearDown(self):
        delete_test_data()

    def test_load_filename(self):
        self.assertIsInstance(header(filename=SINGLE1), header, msg='not a header instance')

class header_load_filename_extensions_test(unittest.TestCase):

    '''
       Are headers able to be loaded properly from MEFs?
    '''

    def setUp(self):
        build_test_data_mef()

    def tearDown(self):
        delete_test_data()

    def test_load_filename_extensions(self):
        hdr0 = header(filename=MULTI1, extension=0)
        self.assertIsInstance(hdr0, header, msg='not a header instance')
        self.assertEqual(hdr0['EXTNAME'], None, msg='not extension primary extension')
        hdr1 = header(filename=MULTI1, extension=1)
        self.assertIsInstance(hdr1, header, msg='not a header instance')
        self.assertEqual(hdr1['EXTNAME'], 'EXT1', msg='not extension 1')
        hdr2 = header(filename=MULTI1, extension=2)
        self.assertIsInstance(hdr2, header, msg='not a header instance')
        self.assertEqual(hdr2['EXTNAME'], 'EXT2', msg='not extension 2')
        hdr3 = header(filename=MULTI1, extension=3)
        self.assertIsInstance(hdr3, header, msg='not a header instance')
        self.assertEqual(hdr3['EXTNAME'], 'EXT3', msg='not extension 3')

class header_load_cardlist_strings_test(unittest.TestCase):

    '''
       Are headers able to be loaded from a list string cards?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_cardlist_strings(self):
        hdr = header(cardlist=STRINGS)
        self.assertIsInstance(hdr, header, msg='strings header not a header instance')
        self.assertEqual(len(hdr), len(STRINGS), msg='strings header is wrong length')

class header_load_cardlist_unicode_test(unittest.TestCase):

    '''
       Are headers able to be loaded from a list of unicode cards?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_cardlist_unicode(self):
        hdr = header(cardlist=[u'%s' % string for string in STRINGS])
        self.assertIsInstance(hdr, header, msg='unicode header not a header instance')
        self.assertEqual(len(hdr), len(STRINGS), msg='unicode header is wrong length')

class header_load_cardlist_cards_test(unittest.TestCase):

    '''
       Are headers able to be loaded from a list of fits.Card instances?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_cardlist_cards(self):
        hdr = header(cardlist=CARDS)
        self.assertIsInstance(hdr, header, msg='cards header not a header instance')
        self.assertEqual(len(hdr), len(CARDS), msg='cards header is wrong length')

class header_load_cardlist_file_test(unittest.TestCase):

    '''
       Are headers able to be loaded from ASCII files?
    '''

    def setUp(self):
        build_test_data_ascii()

    def tearDown(self):
        delete_test_data()

    def test_load_cardlist_file(self):
        hdr = header(cardlist=ASCII1)
        self.assertIsInstance(hdr, header, msg='ASCII header not a header instance')
        self.assertEqual(len(hdr), 4, msg='incorrect number of cards for ASCII header')

class header_load_all_headers_test(unittest.TestCase):

    '''
       Are all headers able to be loaded from FITS files?
    '''

    def setUp(self):
        build_test_data_sef()
        build_test_data_mef()

    def tearDown(self):
        delete_test_data()

    def test_load_all_headers(self):
        hdr = header(filename=SINGLE1)
        hdrs = hdr.get_all_headers()
        self.assertEqual(len(hdrs), 1, msg='wrong number of headers loaded')
        self.assertIsInstance(hdrs[0], header, msg='loaded header not a header instance')
        hdr = header(filename=MULTI1)
        hdrs = hdr.get_all_headers()
        self.assertEqual(len(hdrs), 4, msg='wrong number of headers loaded')
        for hdr in hdrs:
            self.assertIsInstance(hdr, header, msg='loaded header not a header instance')

class header_load_headers_filename_test(unittest.TestCase):

    '''
       Are all headers able to be loaded from FITS files via function?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_headers_filename(self):
        '''
           Tested by test_load_all_headers.
        '''
        pass

class header_load_headers_cardlist_strings_test(unittest.TestCase):

    '''
       Are all headers able to be loaded from ASCII strings via function?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_headers_cardlist_strings(self):
        endcard = 'END%s' % (' '*77)
        strings = STRINGS+[endcard]
        strings *= 4
        hdrs = get_headers(cardlist=strings)
        self.assertEqual(len(hdrs), 4, msg='wrong number of headers loaded')
        for hdr in hdrs:
            self.assertIsInstance(hdr, header, msg='loaded header not a header instance')

class header_load_headers_cardlist_cards_test(unittest.TestCase):

    '''
       Are all headers able to be loaded from fits.Cards instances via
       function?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_headers_cardlist_cards(self):
        '''
           Not yet testable.
        '''
        pass

class header_load_headers_cardlist_file_test(unittest.TestCase):

    '''
       Are all headers able to be loaded from ASCII files via function?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_headers_cardlist_file(self):
        '''
           Not yet testable.
        '''
        pass

########################################################################
#                                                                      #
#                          header save tests                           #
#                                                                      #
########################################################################

class header_save_raw_test(unittest.TestCase):

    '''
       Are headers able to be saved in raw format without data?
    '''

    def setUp(self):
        self.pri = header().default()
        self.filename = 'raw.fits'

    def tearDown(self):
        del self.pri
        filename = self.filename
        if os.path.exists(filename):
            os.remove(filename)

    def test_save_raw(self):
        pri = self.pri
        filename = self.filename
        pri.save(filename, raw=True)
        self.assertTrue(os.path.exists(filename), msg='raw file did not save')
        self.assertTrue(os.path.getsize(filename) % 2880 == 0, msg='size of raw file is not a multiple of 2880')
        with open(filename, 'rb') as fd:
            contents = fd.read()
        self.assertEqual(contents[:6], b'SIMPLE', msg='raw file does not start with SIMPLE')
        self.assertFalse(b'\n' in contents, msg='raw file contains newlines')

class header_save_ascii_test(unittest.TestCase):

    '''
       Are headers able to be saved in ASCII format?
    '''

    def setUp(self):
        self.pri = header().default()
        self.filename = 'ascii.head'

    def tearDown(self):
        del self.pri
        filename = self.filename
        if os.path.exists(filename):
            os.remove(filename)

    def test_save_ascii(self):
        pri = self.pri
        filename = self.filename
        pri.save(filename, raw=False)
        self.assertTrue(os.path.exists(filename), msg='ascii file did not save')
        with open(filename, 'r') as fd:
            contents = fd.read()
        self.assertEqual(contents[:6], 'SIMPLE', msg='ascii file does not start with SIMPLE')
        self.assertTrue('\n' in contents, msg='ascii file contains newlines')
        self.assertEqual(contents[-1], '\n', msg='ascii file contains newlines')

class header_save_clobber_test(unittest.TestCase):

    '''
       Are headers able to be saved overwriting existing files?
    '''

    def setUp(self):
        self.pri = header().default()
        self.filename = 'clobber.fits'

    def tearDown(self):
        del self.pri
        filename = self.filename
        if os.path.exists(filename):
            os.remove(filename)

    def test_save_clobber(self):
        pri = self.pri
        filename = self.filename
        with open(filename, 'w') as fd:
            pass
        self.assertTrue(os.path.exists(filename), msg='clobber file did not save')
        self.assertEqual(os.path.getsize(filename), 0, msg='initial size of clobber file is not 0')
        pri.save(filename, raw=True, mode='clobber')
        with open(filename, 'rb') as fd:
            contents = fd.read()
        self.assertEqual(contents[:6], b'SIMPLE', msg='raw file does not start with SIMPLE')

class header_save_append_test(unittest.TestCase):

    '''
       Are headers able to be saved appending to an existing file?
    '''

    def setUp(self):
        self.pri = header().default()
        self.filename = 'append.fits'

    def tearDown(self):
        del self.pri
        filename = self.filename
        if os.path.exists(filename):
            os.remove(filename)

    def test_save_append(self):
        pri = self.pri
        filename = self.filename
        with open(filename, 'w') as fd:
            pass
        self.assertTrue(os.path.exists(filename), msg='append file did not save')
        self.assertEqual(os.path.getsize(filename), 0, msg='initial size of append file is not 0')
        pri.save(filename, raw=True, mode='append')
        self.assertTrue(os.path.exists(filename), msg='append file did not save')
        self.assertTrue(os.path.getsize(filename) % 2880 == 0, msg='size of append file is not a multiple of 2880')
        size1 = os.path.getsize(filename)
        pri.save(filename, raw=True, mode='append')
        size2 = os.path.getsize(filename)
        self.assertTrue(os.path.getsize(filename) % 2880 == 0, msg='size of append file is not a multiple of 2880')
        self.assertEqual(size2, 2*size1, msg='final size of append file not twice the initial size')
        with open(filename, 'rb') as fd:
            contents = fd.read()
        self.assertEqual(contents[:6], b'SIMPLE', msg='raw file does not start with SIMPLE')
        self.assertEqual(contents.count(b'SIMPLE'), 2, msg='raw file does not contain 2 SIMPLE cards')

class header_save_dataless_test(unittest.TestCase):

    '''
       Are headers able to be saved in dataless format?
    '''

    def setUp(self):
        build_test_data_sef()
        self.sef = header(filename=SINGLE1)
        self.filename = 'dataless.fits'

    def tearDown(self):
        delete_test_data()
        del self.sef
        filename = self.filename
        if os.path.exists(filename):
            os.remove(filename)

    def test_save_dataless(self):
        sef = self.sef
        filename = self.filename
        sef.save(filename=filename, raw=True, dataless=True)
        hdr = header(filename=filename)
        self.assertEqual(hdr['NAXIS'], 0, msg='')
        self.assertNotEqual(hdr['NAXIS'], sef['NAXIS'], msg='')
        self.assertEqual(sef['NAXIS1'], 32, msg='')
        self.assertEqual(sef['NAXIS2'], 32, msg='')
        self.assertEqual(hdr['NAXIS1'], None, msg='')
        self.assertEqual(hdr['NAXIS2'], None, msg='')

########################################################################
#                                                                      #
#                        header creation tests                         #
#                                                                      #
########################################################################

class header_creation_new_test(unittest.TestCase):

    '''
       Are new headers created correctly?
    '''

    def setUp(self):
        self.new = header().new()

    def tearDown(self):
        pass

    def test_creation_new(self):
        hdr = header().new()
        self.assertIsInstance(hdr, header, msg='not a header instance')
        self.assertEqual(len(hdr.cards), 0, msg='cards not empty')

class header_creation_default_primary_test(unittest.TestCase):

    '''
       Are default primary headers created correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation_default_primary(self):
        hdr = header().default(type='primary')
        self.assertIsInstance(hdr, header, msg='not a header instance')
        self.assertEqual(len(hdr.cards), 4, msg='incorrect number of cards for primary header')
        self.assertEqual(hdr['SIMPLE'], True, msg='keyword SIMPLE is not True')
        self.assertEqual(hdr['BITPIX'], 8, msg='keyword BITPIX is not 8')
        self.assertEqual(hdr['NAXIS'], 0, msg='keyword NAXIS is not 0')
        self.assertEqual(hdr['EXTEND'], True, msg='keyword EXTEND is not True')
        self.assertIsInstance(getattr(hdr, 'SIMPLE'), fits.Card, msg='SIMPLE attribute missing')
        self.assertIsInstance(getattr(hdr, 'BITPIX'), fits.Card, msg='BITPIX attribute missing')
        self.assertIsInstance(getattr(hdr, 'NAXIS'), fits.Card, msg='NAXIS attribute missing')
        self.assertIsInstance(getattr(hdr, 'EXTEND'), fits.Card, msg='EXTEND attribute missing')

class header_creation_default_image_test(unittest.TestCase):

    '''
       Are default extension headers created correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation_default_image(self):
        hdr = header().default(type='image')
        self.assertIsInstance(hdr, header, msg='not a header instance')
        self.assertEqual(len(hdr.cards), 5, msg='incorrect number of cards for image header')
        self.assertEqual(hdr['XTENSION'], 'IMAGE', msg='keyword XTENSION is not IMAGE')
        self.assertEqual(hdr['BITPIX'], 8, msg='keyword BITPIX is not 8')
        self.assertEqual(hdr['NAXIS'], 0, msg='keyword NAXIS is not 0')
        self.assertEqual(hdr['PCOUNT'], 0, msg='keyword PCOUNT is not 0')
        self.assertEqual(hdr['GCOUNT'], 1, msg='keyword GCount is not 1')
        self.assertIsInstance(getattr(hdr, 'XTENSION'), fits.Card, msg='XTENSION attribute missing')
        self.assertIsInstance(getattr(hdr, 'BITPIX'), fits.Card, msg='BITPIX attribute missing')
        self.assertIsInstance(getattr(hdr, 'NAXIS'), fits.Card, msg='NAXIS attribute missing')
        self.assertIsInstance(getattr(hdr, 'PCOUNT'), fits.Card, msg='PCOUNT attribute missing')
        self.assertIsInstance(getattr(hdr, 'GCOUNT'), fits.Card, msg='GCOUNT attribute missing')

class header_creation_copy_test(unittest.TestCase):

    '''
       Are headers copied correctly?
    '''

    def setUp(self):
        self.hdr = header()

    def tearDown(self):
        del self.hdr

    def test_creation_copy(self):
        hdr = self.hdr
        copy = hdr.copy()
        self.assertIsInstance(copy, header, msg='not a header instance')
        for keyword in hdr:
            self.assertEqual(copy[keyword], hdr[keyword], msg='%s keywords not copied properly' % keyword)

########################################################################
#                                                                      #
#                       header properties tests                        #
#                                                                      #
########################################################################

class header_properties_hdr_test(unittest.TestCase):

    '''
       Is the "hdr" property behaving properly?
    '''

    def setUp(self):
        self.pri = header().default()
        self.new = header().new()

    def tearDown(self):
        del self.pri, self.new

    def test_hdr_property(self):
        pri = self.pri
        new = self.new
        self.assertEqual(pri.hdr, pri._hdr, msg='hdr property not getting _hdr')
        new.hdr = pri.hdr
        self.assertEqual(new._hdr, pri._hdr, msg='hdr property not setting _hdr')
        del new.hdr
        self.assertEqual(new._hdr, None, msg='hdr property not deleting _hdr')

class header_properties_cards_test(unittest.TestCase):

    '''
       Is the "cards" property behaving properly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_cards_property(self):
        pri = self.pri
        self.assertEqual(pri.cards, pri._cards, msg='cards property not getting _cards')

########################################################################
#                                                                      #
#                          header read tests                           #
#                                                                      #
########################################################################

class header_read_fits_keywords_dict_test(unittest.TestCase):

    '''
       Are values in the header read from the dict correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_fits_keywords_dict(self):
        crd = self.crd
        val = crd['SIMPLE']
        self.assertEqual(val, True, msg='SIMPLE keyword read wrong value')
        self.assertIsInstance(val, bool, msg='SIMPLE keyword read wrong type')
        val = crd['BITPIX']
        self.assertEqual(val, 8, msg='BITPIX keyword read wrong value')
        self.assertIsInstance(val, int, msg='BITPIX keyword read wrong type')
        val = crd['BOGUS']
        self.assertEqual(val, None, msg='read of a non-existent keyword did not return None')

class header_read_fits_indexes_dict_test(unittest.TestCase):

    '''
       Are values in the header read from the dict correctly via index?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_fits_indexes_dict(self):
        crd = self.crd
        val = crd[crd.index('SIMPLE')]
        self.assertEqual(val, True, msg='SIMPLE keyword read wrong value')
        self.assertIsInstance(val, bool, msg='SIMPLE keyword read wrong type')
        val = crd[crd.index('BITPIX')]
        self.assertEqual(val, 8, msg='BITPIX keyword read wrong value')
        self.assertIsInstance(val, int, msg='BITPIX keyword read wrong type')
        self.assertEqual(crd[999], None, msg='missing index did not return None')
        self.assertRaises(DARMAError, crd.index, 999)
        self.assertRaises(DARMAError, crd.index, 'BOGUS')

class header_read_fits_keywords_attr_test(unittest.TestCase):

    '''
       Are values in the header read from attributes correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_fits_keywords_attr(self):
        crd = self.crd
        card = getattr(crd, 'SIMPLE')
        self.assertEqual(get_keyword(card), 'SIMPLE', msg='SIMPLE card read wrong keyword')
        self.assertEqual(card.value, True, msg='SIMPLE card read wrong value')
        self.assertIsInstance(card.value, bool, msg='SIMPLE card read wrong type')
        card = getattr(crd, 'BITPIX')
        self.assertEqual(get_keyword(card), 'BITPIX', msg='BITPIX card read wrong keyword')
        self.assertEqual(card.value, 8, msg='BITPIX card read wrong value')
        self.assertIsInstance(card.value, int, msg='BITPIX card read wrong type')
        self.assertRaises(AttributeError, getattr, crd, 'BOGUS')

class header_read_hierarch_keywords_dict_test(unittest.TestCase):

    '''
       Are HIERARCH values in the header read from the dict correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_hierarch_keywords_dict(self):
        crd = self.crd
        val = crd['DARMA Hierarch Card 1']
        self.assertEqual(val, 'one', msg='wrong value for HIERARCH Card 1')
        val = crd['DARMA Hierarch Card 2']
        self.assertEqual(val, 2, msg='wrong value for HIERARCH Card 2')
        val = crd['DARMA Hierarch Card 3']
        self.assertEqual(val, 3.0, msg='wrong value for HIERARCH Card 3')
        val = crd['HIERARCH DARMA Hierarch Card 1']
        self.assertEqual(val, 'one', msg='wrong value for HIERARCH Card 1')
        val = crd['HIERARCH DARMA Hierarch Card 2']
        self.assertEqual(val, 2, msg='wrong value for HIERARCH Card 2')
        val = crd['HIERARCH DARMA Hierarch Card 3']
        self.assertEqual(val, 3.0, msg='wrong value for HIERARCH Card 3')

class header_read_hierarch_keywords_attr_test(unittest.TestCase):

    '''
       Are HIERARCH values in the header read from attributes correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_hierarch_keywords_attr(self):
        crd = self.crd
        card = crd.HIERARCH_DARMA_Hierarch_Card_1
        self.assertEqual(get_keyword(card), 'DARMA Hierarch Card 1', msg='Card 1 read wrong keyword')
        self.assertEqual(card.value, 'one', msg='wrong value for HIERARCH Card 1')
        card = crd.HIERARCH_DARMA_Hierarch_Card_2
        self.assertEqual(get_keyword(card), 'DARMA Hierarch Card 2', msg='Card 2 read wrong keyword')
        self.assertEqual(card.value, 2, msg='wrong value for HIERARCH Card 2')
        card = crd.HIERARCH_DARMA_Hierarch_Card_3
        self.assertEqual(get_keyword(card), 'DARMA Hierarch Card 3', msg='Card 3 read wrong keyword')
        self.assertEqual(card.value, 3.0, msg='wrong value for HIERARCH Card 3')

class header_read_blanks_test(unittest.TestCase):

    '''
       Are BLANK values in the header read correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)
        self.pri = header().default()

    def tearDown(self):
        del self.crd, self.pri

    def test_read_blanks(self):
        '''get all blanks'''
        crd = self.crd
        pri = self.pri
        blanks = crd.get_blank()
        self.assertEqual(len(blanks), len(BLANK), msg='wrong number of blanks')
        for blank in blanks:
            self.assertIsInstance(blank, (str, unicode), msg='wrong blank card type')
        blanks = pri.get_blank()
        self.assertEqual(len(blanks), 0, msg='number of blanks not zero')

class header_read_blank_cards_test(unittest.TestCase):

    '''
       Are all BLANKs in the header read correctly?
    '''

    def setUp(self):
        pass
        #self.crd = header(cardlist=CARDS)
        #self.pri = header().default()

    def tearDown(self):
        pass
        #del self.crd, self.pri

    def test_read_blank_cards(self):
        '''get all blank cards'''
        '''
           Not yet testable.
        '''
        pass
        #crd = self.crd
        #pri = self.pri
        #cards = crd.get_blank_cards()
        #self.assertEqual(len(cards), len(BLANKCARDS), msg='wrong number of blank cards')
        #for card in cards:
        #    self.assertIsInstance(card, fits.Card, msg='wrong blank card type')
        #cards = pri.get_blank_cards()
        #self.assertEqual(len(cards), 0, msg='number of blank cards not zero')

class header_read_comments_test(unittest.TestCase):

    '''
       Are all COMMENTs in the header read correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)
        self.pri = header().default()

    def tearDown(self):
        del self.crd, self.pri

    def test_read_comments(self):
        '''get all comments'''
        crd = self.crd
        pri = self.pri
        comments = crd.get_comment()
        self.assertEqual(len(comments), len(COMMENT+COMMENTCARDS), msg='wrong number of comments')
        for comment in comments:
            self.assertIsInstance(comment, (str, unicode), msg='wrong comment card type')
        comments = pri.get_comment()
        self.assertEqual(len(comments), 0, msg='number of comments not zero')

class header_read_comment_cards_test(unittest.TestCase):

    '''
       Are cards stored in COMMENTs constructed correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)
        self.pri = header().default()

    def tearDown(self):
        del self.crd, self.pri

    def test_read_comment_cards(self):
        '''get all comment cards'''
        crd = self.crd
        pri = self.pri
        cards = crd.get_comment_cards()
        self.assertEqual(len(cards), len(COMMENTCARDS), msg='wrong number of comment cards')
        for card in cards:
            self.assertIsInstance(card, fits.Card, msg='wrong comment card type')
        cards = pri.get_comment_cards()
        self.assertEqual(len(cards), 0, msg='number of comment cards not zero')

class header_read_history_test(unittest.TestCase):

    '''
       Are all HISTORYs in the header read correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)
        self.pri = header().default()

    def tearDown(self):
        del self.crd, self.pri

    def test_read_history(self):
        crd = self.crd
        pri = self.pri
        historys = crd.get_history()
        self.assertEqual(len(historys), len(HISTORY+HISTORYCARDS), msg='wrong number of histories')
        for history in historys:
            self.assertIsInstance(history, (str, unicode), msg='wrong history card type')
        historys = pri.get_history()
        self.assertEqual(len(historys), 0, msg='number of histories not zero')

class header_read_history_cards_test(unittest.TestCase):

    '''
       Are cards stored in HISTORYs read correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)
        self.pri = header().default()

    def tearDown(self):
        del self.crd, self.pri

    def test_read_history_cards(self):
        crd = self.crd
        pri = self.pri
        cards = crd.get_history_cards()
        self.assertEqual(len(cards), len(HISTORYCARDS), msg='wrong numner of history cards')
        for card in cards:
            self.assertIsInstance(card, fits.Card, msg='wrong comment card type')
        cards = pri.get_history_cards()
        self.assertEqual(len(cards), 0, msg='number of history cards not zero')

class header_read_info_test(unittest.TestCase):

    '''
       Is the header information conveyed correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_info(self):
        pri = self.pri
        self.assertIsNone(pri.info(), msg='info() method did not return None')

class header_read_dump_test(unittest.TestCase):

    '''
       Are values in the header dumped correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_dump(self):
        pri = self.pri
        self.assertIsNone(pri.dump(), msg='dump() method did not return None')

class header_read_comment_test(unittest.TestCase):

    '''
       Are keyword comments in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_comment(self):
        '''get comment from a card'''
        pri = self.pri
        self.assertEqual(pri.cards['SIMPLE'].comment, 'conforms to FITS standard', msg='found wrong comment for SIMPLE keyword')
        self.assertEqual(pri.cards['BITPIX'].comment, 'array data type', msg='found wrong comment for BITPIX keyword')
        self.assertEqual(pri.cards['NAXIS'].comment, 'number of array dimensions', msg='found wrong comment for NAXIS keyword')
        # not very nice, but old PyFITS returns None for empty comment,
        # others return empty string
        self.assertFalse(pri.cards['EXTEND'].comment, msg='found comment for EXTEND keyword')

class header_read_value_test(unittest.TestCase):

    '''
       Are keyword values in the header read correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_value(self):
        '''get value from a card, tested previously in many other tests'''
        pass

class header_read_length_test(unittest.TestCase):

    '''
       Is the length of the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.pri, self.crd

    def test_read_length(self):
        pri = self.pri
        crd = self.crd
        self.assertEqual(len(pri), 4, msg='default header length incorrect')
        self.assertEqual(len(crd), len(CARDS), msg='CARDS header length incorrect')

class header_read_contents_test(unittest.TestCase):

    '''
       Is what the header contains read correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_read_contents(self):
        crd = self.crd
        self.assertTrue('SIMPLE' in crd, msg='SIMPLE card not found in default header')
        self.assertTrue('HIERARCH DARMA Hierarch Card 1' in crd, msg='HIERARCH card not found in default header')
        self.assertTrue('DARMA Hierarch Card 1' in crd, msg='HIERARCH card not found in default header')
        self.assertTrue('COMMENT' in crd, msg='COMMENT card not found in default header')
        self.assertTrue('HISTORY' in crd, msg='HISTORY card not found in default header')

class header_read_representation_test(unittest.TestCase):

    '''
       Is the representation of the header conveyed correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_representation(self):
        '''__repr__'''
        pri = self.pri
        self.assertIsInstance(repr(pri), (str, unicode), msg='representation is not a string')

class header_read_string_test(unittest.TestCase):

    '''
       Is the string casting of the header done correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_string(self):
        '''__str__'''
        pri = self.pri
        self.assertIsInstance(str(pri), (str, unicode), msg='result of string casting is not a string')

class header_read_keywords_test(unittest.TestCase):

    '''
       Is the list of keywords in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_keywords(self):
        pri = self.pri
        keywords = pri.keywords()
        self.assertIsInstance(keywords, list, msg='result of keywords() not a list')
        self.assertEqual(len(keywords), len(pri), msg='keywords list is wrong length')
        keys = pri.keys()
        self.assertIsInstance(keys, list, msg='result of keys() not a list')
        self.assertEqual(len(keys), len(pri), msg='keys list is wrong length')

class header_read_values_test(unittest.TestCase):

    '''
       Is the list of values in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_values(self):
        pri = self.pri
        values = pri.values()
        self.assertIsInstance(values, list, msg='result of values() not a list')
        self.assertEqual(len(values), len(pri), msg='values list is wrong length')

class header_read_comment_values_test(unittest.TestCase):

    '''
       is the list of comments in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_comment_values(self):
        ''' list of keyword comments '''
        pri = self.pri
        comments = pri.comments()
        self.assertIsInstance(comments, list, msg='result of comments() not a list')
        self.assertEqual(len(comments), len(pri), msg='comments list is wrong length')

class header_read_items_test(unittest.TestCase):

    '''
       Is the list of items in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_items(self):
        pri = self.pri
        items = pri.items()
        self.assertIsInstance(items, list, msg='result of items() not a list')
        self.assertEqual(len(items), len(pri), msg='items list is wrong length')
        for item in items:
            self.assertEqual(len(item), 3, msg='item tuple is wrong length')
        items = pri.items(comments=False)
        self.assertIsInstance(items, list, msg='result of items() not a list')
        self.assertEqual(len(items), len(pri), msg='items list is wrong length')
        for item in items:
            self.assertEqual(len(item), 2, msg='item tuple is wrong length')

class header_read_cards_test(unittest.TestCase):

    '''
       Is the set of cards in the header read correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_cards(self):
        pri = self.pri
        cards = pri.cards
        # card accessors are of custom form
        #self.assertIsInstance(cards, list, msg='result of cards() not a list')
        self.assertEqual(len(cards), len(pri), msg='cards list is wrong length')

class header_read_iterators_test(unittest.TestCase):

    '''
       Are the iterators in the header formed correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_read_iterators(self):
        pri = self.pri
        # iterkeywords
        iterkeywords = pri.iterkeywords()
        self.assertIsInstance(iterkeywords, collections.Iterator, msg='result of iterkeywords() not an iterator')
        self.assertEqual(len(list(iterkeywords)), len(pri), msg='iterkeywords iterator is wrong length')
        # iterkeys
        iterkeys = pri.iterkeys()
        self.assertIsInstance(iterkeys, collections.Iterator, msg='result of iterkeys() not an iterator')
        self.assertEqual(len(list(iterkeys)), len(pri), msg='keys iterator is wrong length')
        # itervalues
        itervalues = pri.itervalues()
        self.assertIsInstance(itervalues, collections.Iterator, msg='result of itervalues() not an iterator')
        self.assertEqual(len(list(itervalues)), len(pri), msg='keys iterator is wrong length')
        # itercomments
        itercomments = pri.itercomments()
        self.assertIsInstance(itercomments, collections.Iterator, msg='result of itercomments() not an iterator')
        self.assertEqual(len(list(itercomments)), len(pri), msg='itercomments list is wrong length')
        # iteritems
        iteritems = pri.iteritems()
        self.assertIsInstance(iteritems, collections.Iterator, msg='result of iteritems() not an iterator')
        self.assertEqual(len(list(iteritems)), len(pri), msg='iteritems iterator is wrong length')
        for iteritem in iteritems:
            self.assertEqual(len(iteritem), 3, msg='iteritem tuple is wrong length')
        iteritems = pri.iteritems(comments=False)
        self.assertIsInstance(iteritems, collections.Iterator, msg='result of iteritems() not an iterator')
        self.assertEqual(len(list(iteritems)), len(pri), msg='iteritems iterator is wrong length')
        for iteritem in iteritems:
            self.assertEqual(len(iteritem), 2, msg='iteritem tuple is wrong length')
        # itercards
        itercards = pri.itercards()
        self.assertIsInstance(itercards, collections.Iterator, msg='result of itercards() not an iterator')
        self.assertEqual(len(list(itercards)), len(pri), msg='itercards iterator is wrong length')

class header_read_getval_test(unittest.TestCase):

    '''
       Are values in a FITS file header read correctly?
    '''

    def setUp(self):
        build_test_data_sef()
        build_test_data_mef()

    def tearDown(self):
        delete_test_data()

    def test_read_getval(self):
        # default ext=0
        simple = getval(SINGLE1, 'SIMPLE')
        self.assertTrue(simple, msg='returned SIMPLE value is incorrect')
        bitpix = getval(SINGLE1, 'BITPIX')
        self.assertEqual(bitpix, -32, msg='returned BITPIX value is incorrect')
        naxis = getval(SINGLE1, 'NAXIS')
        self.assertEqual(naxis, 2, msg='returned NAXIS value is not True')
        extend = getval(SINGLE1, 'EXTEND')
        self.assertTrue(extend, msg='returned EXTEND value is not True')
        simple = getval(MULTI1, 'SIMPLE')
        self.assertTrue(simple, msg='returned SIMPLE value is incorrect')
        bitpix = getval(MULTI1, 'BITPIX')
        self.assertEqual(bitpix, 8, msg='returned BITPIX value is incorrect')
        naxis = getval(MULTI1, 'NAXIS')
        self.assertEqual(naxis, 0, msg='returned NAXIS value is not True')
        extend = getval(MULTI1, 'EXTEND')
        self.assertTrue(extend, msg='returned EXTEND value is not True')
        # ext >= 0
        bitpix = getval(MULTI1, 'BITPIX', ext=0)
        self.assertEqual(bitpix, 8, msg='returned BITPIX value is incorrect')
        bitpix = getval(MULTI1, 'BITPIX', ext=1)
        self.assertEqual(bitpix, -32, msg='returned BITPIX value is incorrect')
        bitpix = getval(MULTI1, 'BITPIX', ext=2)
        self.assertEqual(bitpix, -32, msg='returned BITPIX value is incorrect')
        bitpix = getval(MULTI1, 'BITPIX', ext=3)
        self.assertEqual(bitpix, -32, msg='returned BITPIX value is incorrect')
        xtension = getval(MULTI1, 'XTENSION', ext=0)
        self.assertEqual(xtension, None, msg='returned BITPIX value is incorrect')
        xtension = getval(MULTI1, 'XTENSION', ext=1)
        self.assertEqual(xtension, 'IMAGE', msg='returned BITPIX value is incorrect')
        xtension = getval(MULTI1, 'XTENSION', ext=2)
        self.assertEqual(xtension, 'IMAGE', msg='returned BITPIX value is incorrect')
        xtension = getval(MULTI1, 'XTENSION', ext=3)
        self.assertEqual(xtension, 'IMAGE', msg='returned BITPIX value is incorrect')

########################################################################
#                                                                      #
#                          header write tests                          #
#                                                                      #
########################################################################

class header_write_fits_keywords_dict_test(unittest.TestCase):

    '''
       Are cards written to the header dict correctly?
    '''

    def setUp(self):
        self.new = header().new()

    def tearDown(self):
        pass

    def test_write_fits_keywords_dict(self):
        # new (empty internal header)
        new = header().new()
        new['SIMPLE'] = (True, 'conforms to FITS standard')
        new['BITPIX'] = (8, 'array data type')
        new['NAXIS'] = (0, 'number of array dimensions')
        new['EXTEND'] = True
        # default (default internal primary header)
        pri = header().default(type='primary')
        for keyword in ['SIMPLE', 'BITPIX', 'NAXIS', 'EXTEND']:
            self.assertEqual(new[keyword], pri[keyword], msg='%s keyword values do not match' % keyword)
            self.assertEqual(new.cards[keyword].comment, pri.cards[keyword].comment, msg='%s keyword comments do not match' % keyword)
            self.assertEqual(getattr(new, keyword).value, getattr(pri, keyword).value, msg='%s attribute values do not match' % keyword)
            self.assertEqual(getattr(new, keyword).comment, getattr(pri, keyword).comment, msg='%s attribute comments do not match' % keyword)
        new.new()
        new['XTENSION'] = ('IMAGE', 'Image extension')
        new['BITPIX'] = (8, 'array data type')
        new['NAXIS'] = (0, 'number of array dimensions')
        new['PCOUNT'] = (0, 'number of parameters')
        new['GCOUNT'] = (1, 'number of groups')
        # default (default internal extension/image header)
        ext = header().default(type='image')
        for keyword in ['XTENSION', 'BITPIX', 'NAXIS', 'PCOUNT', 'GCOUNT']:
            self.assertEqual(new[keyword], ext[keyword], msg='%s keyword values do not match' % keyword)
            self.assertEqual(new.cards[keyword].comment, ext.cards[keyword].comment, msg='%s keyword comments do not match' % keyword)
            self.assertEqual(getattr(new, keyword).value, getattr(ext, keyword).value, msg='%s attribute values do not match' % keyword)
            self.assertEqual(getattr(new, keyword).comment, getattr(ext, keyword).comment, msg='%s attribute comments do not match' % keyword)

class header_write_fits_keywords_attr_test(unittest.TestCase):

    '''
       Are cards written to the header attribute correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_fits_keywords_attr(self):
        ''' writing to attribute is not yet supported '''
        pass

class header_write_hierarch_keywords_dict_test(unittest.TestCase):

    '''
       Are HIERARCH cards written to the header dict correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_write_hierarch_keywords_dict(self):
        pri = self.pri
        pri['HIERARCH DARMA Hierarch Card 1'] = 'one'
        pri['HIERARCH DARMA Hierarch Card 2'] = 2
        pri['HIERARCH DARMA Hierarch Card 3'] = 3.0
        self.assertEqual(pri['DARMA Hierarch Card 1'], 'one', msg='HIERARCH card 1 keyword value incorrect')
        self.assertEqual(pri['DARMA Hierarch Card 2'], 2, msg='HIERARCH card 2 keyword value incorrect')
        self.assertEqual(pri['DARMA Hierarch Card 3'], 3.0, msg='HIERARCH card 3 keyword value incorrect')
        self.assertEqual(pri['HIERARCH DARMA Hierarch Card 1'], 'one', msg='HIERARCH card 1 keyword value incorrect')
        self.assertEqual(pri['HIERARCH DARMA Hierarch Card 2'], 2, msg='HIERARCH card 2 keyword value incorrect')
        self.assertEqual(pri['HIERARCH DARMA Hierarch Card 3'], 3.0, msg='HIERARCH card 3 keyword value incorrect')
        self.assertEqual(getattr(pri, 'HIERARCH_DARMA_Hierarch_Card_1').value, 'one', msg='HIERARCH card 1 attribute value incorrect')
        self.assertEqual(getattr(pri, 'HIERARCH_DARMA_Hierarch_Card_2').value, 2, msg='HIERARCH card 2 attribute value incorrect')
        self.assertEqual(getattr(pri, 'HIERARCH_DARMA_Hierarch_Card_3').value, 3.0, msg='HIERARCH card 3 attribute value incorrect')

class header_write_hierarch_keywords_attr_test(unittest.TestCase):

    '''
       Are HIERARCH cards written to the header attribute correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_hierarch_keywords_attr(self):
        ''' writing to attribute is not yet supported '''
        pass

class header_write_blanks_test(unittest.TestCase):

    '''
       Are BLANK cards written to the header correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_write_blanks(self):
        pri = self.pri
        pri[''] = 'DARMA Blank Card 1'
        pri[''] = 'DARMA Blank Card 2'
        pri[''] = 'DARMA Blank Card 3'
        blanks = pri.get_blank()
        self.assertEqual(len(blanks), 3, msg='incorrect number of added blank crds')
        self.assertEqual(blanks[0], 'DARMA Blank Card 1', msg='BLANK card 1 value is incorrect')
        self.assertEqual(blanks[1], 'DARMA Blank Card 2', msg='BLANK card 2 value is incorrect')
        self.assertEqual(blanks[2], 'DARMA Blank Card 3', msg='BLANK card 3 value is incorrect')

class header_write_comments_test(unittest.TestCase):

    '''
       Are COMMENT cards written to the header correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_write_comments(self):
        pri = self.pri
        pri['COMMENT'] = 'DARMA Comment Card 1'
        pri['COMMENT'] = 'DARMA Comment Card 2'
        pri['COMMENT'] = 'DARMA Comment Card 3'
        comments = pri.get_comment()
        self.assertEqual(len(comments), 3, msg='incorrect number of added comments')
        self.assertEqual(comments[0], 'DARMA Comment Card 1', msg='COMMENT card 1 value is incorrect')
        self.assertEqual(comments[1], 'DARMA Comment Card 2', msg='COMMENT card 2 value is incorrect')
        self.assertEqual(comments[2], 'DARMA Comment Card 3', msg='COMMENT card 3 value is incorrect')

class header_write_history_test(unittest.TestCase):

    '''
       Are HISTORY cards written to the header correctly?
    '''

    def setUp(self):
        self.pri = header().default()

    def tearDown(self):
        del self.pri

    def test_write_history(self):
        pri = self.pri
        pri['HISTORY'] = 'DARMA History Card 1'
        pri['HISTORY'] = 'DARMA History Card 2'
        pri['HISTORY'] = 'DARMA History Card 3'
        histories = pri.get_history()
        self.assertEqual(len(histories), 3, msg='incorrect number of added histories')
        self.assertEqual(histories[0], 'DARMA History Card 1', msg='HISTORY card 1 value is incorrect')
        self.assertEqual(histories[1], 'DARMA History Card 2', msg='HISTORY card 2 value is incorrect')
        self.assertEqual(histories[2], 'DARMA History Card 3', msg='HISTORY card 3 value is incorrect')

class header_write_rename_keyword_test(unittest.TestCase):

    '''
       Are keywords renamed in the header correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_write_rename_keyword(self):
        crd = self.crd
        self.assertRaises(DARMAError, crd.rename_keyword, 'KEYWORD1', 'COMMENT')
        self.assertRaises(DARMAError, crd.rename_keyword, 'COMMENT', 'KEYWORD1')
        self.assertRaises(DARMAError, crd.rename_keyword, 'KEYWORD1', 'HISTORY')
        self.assertRaises(DARMAError, crd.rename_keyword, 'HISTORY', 'KEYWORD1')
        self.assertRaises(DARMAError, crd.rename_keyword, 'KEYWORD1', '')
        self.assertRaises(DARMAError, crd.rename_keyword, '', 'KEYWORD1')
        crd['KEYWORD1'] = 'one'
        crd['KEYWORD2'] = 2
        crd['HIERARCH Keyword 1'] = 1.0
        crd['HIERARCH Keyword 2'] = 'two'
        self.assertEqual(crd['KEYWORD1'], 'one', msg='KEYWORD1 value has wrong value')
        self.assertEqual(crd['KEYWORD2'], 2, msg='KEYWORD2 value has wrong value')
        self.assertEqual(crd['KEYWORD3'], None, msg='KEYWORD3 value has wrong value')
        self.assertEqual(crd['KEYWORD4'], None, msg='KEYWORD4 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 1'], 1.0, msg='HIERARCH Keyword 1 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 2'], 'two', msg='HIERARCH Keyword 2 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 3'], None, msg='HIERARCH Keyword 3 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 4'], None, msg='HIERARCH Keyword 4 value has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, 'one', msg='KEYWORD1 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD2').value, 2, msg='KEYWORD2 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD3')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD4')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_1').value, 1.0, msg='HIERARCH Keyword 1 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_2').value, 'two', msg='HIERARCH Keyword 2 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_3')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_4')
        crd.rename_keyword('KEYWORD1', 'KEYWORD3')
        crd.rename_keyword('KEYWORD2', 'KEYWORD4')
        crd.rename_keyword('HIERARCH Keyword 1', 'HIERARCH Keyword 3')
        crd.rename_keyword('HIERARCH Keyword 2', 'HIERARCH Keyword 4')
        self.assertEqual(crd['KEYWORD1'], None, msg='KEYWORD1 value has wrong value')
        self.assertEqual(crd['KEYWORD2'], None, msg='KEYWORD2 value has wrong value')
        self.assertEqual(crd['KEYWORD3'], 'one', msg='KEYWORD3 value has wrong value')
        self.assertEqual(crd['KEYWORD4'], 2, msg='KEYWORD4 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 1'], None, msg='HIERARCH Keyword 1 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 2'], None, msg='HIERARCH Keyword 2 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 3'], 1.0, msg='HIERARCH Keyword 3 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 4'], 'two', msg='HIERARCH Keyword 4 value has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD1')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD2')
        self.assertEqual(getattr(crd, 'KEYWORD3').value, 'one', msg='KEYWORD3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD4').value, 2, msg='KEYWORD4 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_1')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_2')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_3').value, 1.0, msg='HIERARCH Keyword 3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_4').value, 'two', msg='HIERARCH Keyword 4 attrivute has wrong value')
        self.assertRaises(DARMAError, crd.rename_keyword, 'KEYWORD3', 'KEYWORD4')
        self.assertRaises(DARMAError, crd.rename_keyword, 'KEYWORD4', 'KEYWORD3')
        self.assertRaises(DARMAError, crd.rename_keyword, 'HIERARCH Keyword 3', 'HIERARCH Keyword 4')
        self.assertRaises(DARMAError, crd.rename_keyword, 'HIERARCH Keyword 4', 'HIERARCH Keyword 3')
        self.assertEqual(crd['KEYWORD3'], 'one', msg='KEYWORD4 has been overwritten')
        self.assertEqual(crd['KEYWORD4'], 2,     msg='KEYWORD5 has been overwritten')
        self.assertEqual(crd['HIERARCH Keyword 3'], 1.0, msg='HIERARCH Keyword 4 has been overwritten')
        self.assertEqual(crd['HIERARCH Keyword 4'], 'two',     msg='HIERARCH Keyword 5 has been overwritten')
        self.assertEqual(getattr(crd, 'KEYWORD3').value, 'one', msg='KEYWORD3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD4').value, 2, msg='KEYWORD4 attrivute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_3').value, 1.0, msg='HIERARCH Keyword 3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_4').value, 'two', msg='HIERARCH Keyword 4 attrivute has wrong value')

class header_write_rename_key_test(unittest.TestCase):

    '''
       Are keys renamed in the header correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_write_rename_key(self):
        crd = self.crd
        self.assertRaises(DARMAError, crd.rename_key, 'KEYWORD1', 'COMMENT')
        self.assertRaises(DARMAError, crd.rename_key, 'COMMENT', 'KEYWORD1')
        self.assertRaises(DARMAError, crd.rename_key, 'KEYWORD1', 'HISTORY')
        self.assertRaises(DARMAError, crd.rename_key, 'HISTORY', 'KEYWORD1')
        self.assertRaises(DARMAError, crd.rename_key, 'KEYWORD1', '')
        self.assertRaises(DARMAError, crd.rename_key, '', 'KEYWORD1')
        crd['KEYWORD1'] = 'one'
        crd['KEYWORD2'] = 2
        crd['HIERARCH Keyword 1'] = 1.0
        crd['HIERARCH Keyword 2'] = 'two'
        self.assertEqual(crd['KEYWORD1'], 'one', msg='KEYWORD1 value has wrong value')
        self.assertEqual(crd['KEYWORD2'], 2, msg='KEYWORD2 value has wrong value')
        self.assertEqual(crd['KEYWORD3'], None, msg='KEYWORD3 value has wrong value')
        self.assertEqual(crd['KEYWORD4'], None, msg='KEYWORD4 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 1'], 1.0, msg='HIERARCH Keyword 1 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 2'], 'two', msg='HIERARCH Keyword 2 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 3'], None, msg='HIERARCH Keyword 3 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 4'], None, msg='HIERARCH Keyword 4 value has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, 'one', msg='KEYWORD1 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD2').value, 2, msg='KEYWORD2 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD3')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD4')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_1').value, 1.0, msg='HIERARCH Keyword 1 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_2').value, 'two', msg='HIERARCH Keyword 2 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_3')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_4')
        crd.rename_key('KEYWORD1', 'KEYWORD3')
        crd.rename_key('KEYWORD2', 'KEYWORD4')
        crd.rename_key('HIERARCH Keyword 1', 'HIERARCH Keyword 3')
        crd.rename_key('HIERARCH Keyword 2', 'HIERARCH Keyword 4')
        self.assertEqual(crd['KEYWORD1'], None, msg='KEYWORD1 value has wrong value')
        self.assertEqual(crd['KEYWORD2'], None, msg='KEYWORD2 value has wrong value')
        self.assertEqual(crd['KEYWORD3'], 'one', msg='KEYWORD3 value has wrong value')
        self.assertEqual(crd['KEYWORD4'], 2, msg='KEYWORD4 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 1'], None, msg='HIERARCH Keyword 1 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 2'], None, msg='HIERARCH Keyword 2 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 3'], 1.0, msg='HIERARCH Keyword 3 value has wrong value')
        self.assertEqual(crd['HIERARCH Keyword 4'], 'two', msg='HIERARCH Keyword 4 value has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD1')
        self.assertRaises(AttributeError, getattr, crd, 'KEYWORD2')
        self.assertEqual(getattr(crd, 'KEYWORD3').value, 'one', msg='KEYWORD3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD4').value, 2, msg='KEYWORD4 attrivute has wrong value')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_1')
        self.assertRaises(AttributeError, getattr, crd, 'HIERARCH_Keyword_2')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_3').value, 1.0, msg='HIERARCH Keyword 3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_4').value, 'two', msg='HIERARCH Keyword 4 attrivute has wrong value')
        self.assertRaises(DARMAError, crd.rename_key, 'KEYWORD3', 'KEYWORD4')
        self.assertRaises(DARMAError, crd.rename_key, 'KEYWORD4', 'KEYWORD3')
        self.assertRaises(DARMAError, crd.rename_key, 'HIERARCH Keyword 3', 'HIERARCH Keyword 4')
        self.assertRaises(DARMAError, crd.rename_key, 'HIERARCH Keyword 4', 'HIERARCH Keyword 3')
        self.assertEqual(crd['KEYWORD3'], 'one', msg='KEYWORD4 has been overwritten')
        self.assertEqual(crd['KEYWORD4'], 2,     msg='KEYWORD5 has been overwritten')
        self.assertEqual(crd['HIERARCH Keyword 3'], 1.0, msg='HIERARCH Keyword 4 has been overwritten')
        self.assertEqual(crd['HIERARCH Keyword 4'], 'two',     msg='HIERARCH Keyword 5 has been overwritten')
        self.assertEqual(getattr(crd, 'KEYWORD3').value, 'one', msg='KEYWORD3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'KEYWORD4').value, 2, msg='KEYWORD4 attrivute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_3').value, 1.0, msg='HIERARCH Keyword 3 attribute has wrong value')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_4').value, 'two', msg='HIERARCH Keyword 4 attrivute has wrong value')

class header_write_add_test(unittest.TestCase):

    '''
       Are cards added to the header correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_write_add(self):
        crd = self.crd
        crd.add('KEYWORD1', 'one', 'keyword 1')
        crd['KEY1'] = ('one', 'keyword 1')
        self.assertEqual(crd['KEYWORD1'], crd['KEY1'], msg='added wrong value for KEYWORD1')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, getattr(crd, 'KEY1').value, msg='KEYWORD1 attribute has wrong value')
        self.assertEqual(crd.cards['KEYWORD1'].comment, crd.cards['KEY1'].comment, msg='added wrong comment for KEYWORD1')
        crd.add('KEYWORD2', 2, 'keyword 2')
        crd['KEY2'] = (2, 'keyword 2')
        self.assertEqual(crd['KEYWORD2'], crd['KEY2'], msg='added wrong value for KEYWORD2')
        self.assertEqual(getattr(crd, 'KEYWORD2').value, getattr(crd, 'KEY2').value, msg='KEYWORD2 attribute has wrong value')
        self.assertEqual(crd.cards['KEYWORD2'].comment, crd.cards['KEY2'].comment, msg='added wrong comment for KEYWORD2')
        crd.add_after('KEYWORD1', 'KEYWORD3', 3.0, 'keyword 3')
        index = crd.index('KEYWORD1')
        self.assertEqual(crd['KEYWORD3'], crd[index+1], msg='KEYWORD3 not added after KEYWORD1')
        self.assertEqual(getattr(crd, 'KEYWORD3').value, 3.0, msg='KEYWORD3 attribute has wrong value')
        crd.add('HIERARCH Keyword 1', 1.0, 'HIERARCH keyword 1')
        crd['HIERARCH Key 1'] = (1.0, 'HIERARCH keyword 1')
        self.assertEqual(crd['Keyword 1'], crd['Key 1'], msg='added wrong value for HIERARCH Keyword 1')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_1').value, getattr(crd, 'HIERARCH_Key_1').value, msg='HIERARCH Keyword 1 attribute has wrong value')
        self.assertEqual(crd.cards['Keyword 1'].comment, crd.cards['Key 1'].comment, msg='added wrong comment for HIERARCH Keyword 1')
        crd.add('HIERARCH Keyword 2', 'two', 'HIERARCH keyword 2')
        crd['HIERARCH Key 2'] = ('two', 'HIERARCH keyword 2')
        self.assertEqual(crd['Keyword 2'], crd['Key 2'], msg='added wrong value for HIERARCH Keyword 2')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_2').value, getattr(crd, 'HIERARCH_Key_2').value, msg='HIERARCH Keyword 2 attribute has wrong value')
        self.assertEqual(crd.cards['Keyword 2'].comment, crd.cards['Key 2'].comment, msg='added wrong comment for HIERARCH Keyword 2')
        crd.add_after('HIERARCH Keyword 1', 'HIERARCH Keyword 3', 3, 'HIERARCH keyword 3')
        index = crd.index('HIERARCH Keyword 1')
        self.assertEqual(crd['HIERARCH Keyword 3'], crd[index+1], msg='HIERARCH Keyword 3 not added after HIERARCH Keyword 1')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_3').value, 3, msg='HIERARCH Keyword 3 attribute has wrong value')
        crd.add('', 'Blank 1')
        bindex = crd.index('') + len(crd.get_blank())-1
        self.assertEqual(crd[bindex], 'Blank 1', msg='BLANK card not added to end of header')
        crd.add('COMMENT', 'Comment 1')
        cindex = crd.index('COMMENT') + len(crd.get_comment())-1
        self.assertEqual(crd[cindex], 'Comment 1', msg='COMMENT card not added to end of COMMENT cards')
        self.assertLess(bindex, crd.index('COMMENT'), msg='BLANK card not added before HISTORY cards')
        crd.add('HISTORY', 'History 1')
        index = crd.index('HISTORY') + len(crd.get_history())-1
        self.assertEqual(crd[index], 'History 1', msg='HISTORY card not added to end of HISTORY cards')
        self.assertLess(cindex, crd.index('HISTORY'), msg='COMMENT card not added before HISTORY cards')
        crd.add_after('FLOAT', '', 'Blank 1')
        crd.add_after('FLOAT', 'COMMENT', 'Comment 1')
        crd.add_after('FLOAT', 'HISTORY', 'History 1')
        index = crd.index('FLOAT')
        self.assertEqual(crd.index(''), index+3, msg='BLANK card not added after FLOAT card')
        self.assertEqual(crd.index('COMMENT'), index+2, msg='COMMENT card not added after FLOAT card')
        self.assertEqual(crd.index('HISTORY'), index+1, msg='HISTORY card not added after FLOAT card')

class header_write_append_test(unittest.TestCase):

    '''
       Are cards appended to the header correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_write_append(self):
        crd = self.crd
        crd.append('KEYWORD1', 'one', 'keyword 1')
        self.assertEqual(crd.index('KEYWORD1'), crd.index('')-1, msg='KEYWORD1 not appended to bottom of keywords')
        crd['KEY1'] = ('one', 'keyword 1')
        self.assertEqual(crd['KEYWORD1'], crd['KEY1'], msg='added wrong value for KEYWORD1')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, getattr(crd, 'KEY1').value, msg='KEYWORD1 attribute has wrong value')
        self.assertEqual(crd.cards['KEYWORD1'].comment, crd.cards['KEY1'].comment, msg='added wrong comment for KEYWORD1')
        crd.append('KEYWORD2', 2, 'keyword 2')
        self.assertEqual(crd.index('KEYWORD2'), crd.index('')-1, msg='KEYWORD2 not appended to bottom of keywords')
        crd['KEY2'] = (2, 'keyword 2')
        self.assertEqual(crd['KEYWORD2'], crd['KEY2'], msg='added wrong value for KEYWORD2')
        self.assertEqual(getattr(crd, 'KEYWORD2').value, getattr(crd, 'KEY2').value, msg='KEYWORD2 attribute has wrong value')
        self.assertEqual(crd.cards['KEYWORD2'].comment, crd.cards['KEY2'].comment, msg='added wrong comment for KEYWORD2')
        crd.append('HIERARCH Keyword 1', 1.0, 'HIERARCH keyword 1')
        self.assertEqual(crd.index('HIERARCH Keyword 1'), crd.index('')-1, msg='HIERARCHY Keyword 1 not appended to bottom of keywords')
        crd['HIERARCH Key 1'] = (1.0, 'HIERARCH keyword 1')
        self.assertEqual(crd['Keyword 1'], crd['Key 1'], msg='added wrong value for HIERARCH Keyword 1')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_1').value, getattr(crd, 'HIERARCH_Key_1').value, msg='HIERARCH Keyword 1 attribute has wrong value')
        self.assertEqual(crd.cards['Keyword 1'].comment, crd.cards['Key 1'].comment, msg='added wrong comment for HIERARCH Keyword 1')
        crd.append('HIERARCH Keyword 2', 'two', 'HIERARCH keyword 2')
        self.assertEqual(crd.index('HIERARCH Keyword 2'), crd.index('')-1, msg='HIERARCHY Keyword 2 not appended to bottom of keywords')
        crd['HIERARCH Key 2'] = ('two', 'HIERARCH keyword 2')
        self.assertEqual(crd['Keyword 2'], crd['Key 2'], msg='added wrong value for HIERARCH Keyword 2')
        self.assertEqual(getattr(crd, 'HIERARCH_Keyword_2').value, getattr(crd, 'HIERARCH_Key_2').value, msg='HIERARCH Keyword 2 attribute has wrong value')
        self.assertEqual(crd.cards['Keyword 2'].comment, crd.cards['Key 2'].comment, msg='added wrong comment for HIERARCH Keyword 2')
        crd.append('', 'Blank 1')
        bindex = crd.index('') + len(crd.get_blank())-1
        self.assertEqual(crd[bindex], 'Blank 1', msg='BLANK card not added to end of header')
        crd.append('COMMENT', 'Comment 1')
        cindex = crd.index('COMMENT') + len(crd.get_comment())-1
        self.assertEqual(crd[cindex], 'Comment 1', msg='COMMENT card not added to end of COMMENT cards')
        self.assertLess(bindex, crd.index('COMMENT'), msg='BLANK card not added before HISTORY cards')
        crd.append('HISTORY', 'History 1')
        index = crd.index('HISTORY') + len(crd.get_history())-1
        self.assertEqual(crd[index], 'History 1', msg='HISTORY card not added to end of HISTORY cards')
        self.assertLess(cindex, crd.index('HISTORY'), msg='COMMENT card not added before HISTORY cards')

class header_write_append_force_test(unittest.TestCase):

    '''
       Are cards appended to the end of the header correctly?
    '''

    def setUp(self):
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.crd

    def test_write_append(self):
        crd = self.crd
        crd.append('KEYWORD1', 'one', 'keyword 1', force=True)
        self.assertEqual(get_keyword(crd.cards[-1]), 'KEYWORD1', msg='KEYWORD1 not appended to end of header')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, 'one', msg='KEYWORD1 attribute has wrong value')
        crd.append('KEYWORD2', 2, 'keyword 2', force=True)
        self.assertEqual(get_keyword(crd.cards[-1]), 'KEYWORD2', msg='KEYWORD2 not appended to end of header')
        self.assertEqual(getattr(crd, 'KEYWORD2').value, 2, msg='KEYWORD2 attribute has wrong value')
        crd.append('HIERARCH Keyword 1', 1.0, 'HIERARCH keyword 1', force=True)
        self.assertEqual(get_keyword(crd.cards[-1]), 'HIERARCH Keyword 1', msg='HIERARCH Keyword 1 not appended to end of header')
        self.assertEqual(getattr(crd, 'KEYWORD1').value, 1.0, msg='KEYWORD1 attribute has wrong value')
        crd.append('HIERARCH Keyword 2', 'two', 'HIERARCH keyword 2', force=True)
        self.assertEqual(get_keyword(crd.cards[-1]), 'HIERARCH Keyword 2', msg='HIERARCH Keyword 2 not appended to end of header')
        self.assertEqual(getattr(crd, 'HIERARCH Keyword 2').value, 'two', msg='HIERARCH Keyword 2 attribute has wrong value')
        crd.append('', 'Blank 1', force=True)
        self.assertEqual(crd[-1], 'Blank 1', msg='BLANK not appended to end of header')
        crd.append('COMMENT', 'Comment 1', force=True)
        self.assertEqual(crd[-1], 'Comment 1', msg='COMMENT not appended to end of header')
        crd.append('HISTORY', 'History 1', force=True)
        self.assertEqual(crd[-1], 'History 1', msg='HISTORY not appended to end of header')

class header_write_fromstring_test(unittest.TestCase):

    '''
       Are cards appended from string to the header correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_fromstring(self):
        pass


    # include test to check all cards are written to attributes

class header_write_modify_test(unittest.TestCase):

    '''
       Are cards modified in the header correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_modify(self):
        pass

class header_write_update_test(unittest.TestCase):

    '''
       Are cards updated in the header correctly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_write_update(self):
        pass

class header_write_merge_test(unittest.TestCase):

    '''
       Are two headers merged correctly?
    '''

    def setUp(self):
        self.pri = header().default()
        self.ext = header().default(type='image')
        self.crd = header(cardlist=CARDS)

    def tearDown(self):
        del self.pri, self.ext, self.crd

    def test_write_merge(self):
        pri = self.pri
        ext = self.ext
        crd = self.crd
        pri['KEYWORD1'] = 'one'
        pri['HIERARCH Keyword 1'] = 1
        ext['KEYWORD1'] = 1.0
        ext['KEYWORD2'] = 2
        ext['HIERARCH Keyword 1'] = 'one'
        ext['HIERARCH Keyword 2'] = 2.0
        mer = pri.merge(ext, clobber=False)
        self.assertEqual(mer['KEYWORD1'], 'one', msg='KEYWORD1 not in merged header')
        self.assertEqual(mer['HIERARCH Keyword 1'], 1, msg='HIERARCH Keyword 1 not in merged header')
        self.assertEqual(mer['KEYWORD2'], 2, msg='KEYWORD2 not in merged header')
        self.assertEqual(mer['HIERARCH Keyword 2'], 2.0, msg='HIERARCH Keyword 2 not in merged header')
        self.assertEqual(getattr(mer, 'KEYWORD2').value, 2, msg='KEYWORD2 attribute not in merged header')
        self.assertEqual(getattr(mer, 'HIERARCH_Keyword_2').value, 2.0, msg='HIERARCH_Keyword_2 attribute not in merged header')
        self.assertEqual(mer['XTENSION'], None, msg='XTENSION in merged header')
        self.assertEqual(mer['EXTNAME'], None, msg='EXTNAME in merged header')
        mer = pri.merge(ext)
        self.assertEqual(mer['KEYWORD1'], 1.0, msg='KEYWORD1 not in merged header')
        self.assertEqual(mer['HIERARCH Keyword 1'], 'one', msg='HIERARCH Keyword 1 not in merged header')
        mer = pri.merge(crd)
        self.assertEqual(len(mer.get_blank()), len(BLANK), msg='incorrect number of BLANK cards in merged header')
        self.assertEqual(len(mer.get_comment()), len(COMMENT+COMMENTCARDS), msg='incorrect number of COMMENT cards in merged header')
        self.assertEqual(len(mer.get_history()), len(HISTORY+HISTORYCARDS), msg='incorrect number of HISTORY cards in merged header')

class header_write_merge_into_file_test(unittest.TestCase):

    '''
       Is one header merged correctly into another in a file?
    '''

    def setUp(self):
        build_test_data_sef()
        self.pri = header().default()
        self.sef = header(filename=SINGLE1)

    def tearDown(self):
        delete_test_data()
        del self.pri, self.sef

    def test_write_merge_into_file(self):
        pri = self.pri
        sef = self.sef

########################################################################
#                                                                      #
#                         header delete tests                          #
#                                                                      #
########################################################################

class header_delete_dict_test(unittest.TestCase):

    '''
       Are headers contents deleted properly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_delete_dict(self):
        pass

########################################################################
#                                                                      #
#                         header verify tests                          #
#                                                                      #
########################################################################

class header_verify_header_test(unittest.TestCase):

    '''
       Are header contents verified properly?
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_verify_header(self):
        pass

if __name__ == '__main__':
    unittest.main()
