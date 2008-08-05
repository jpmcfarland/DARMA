'''A FITS header object resembling a dictionary.
'''

__version__ = '@(#)$Revision$'

import pyfits, os

if not hasattr(pyfits, '_Hierarch') and hasattr(pyfits, 'NP_pyfits') and hasattr(pyfits.NP_pyfits, '_Hierarch'):
    pyfits._Hierarch = pyfits.NP_pyfits._Hierarch

from common import DARMAError, fold_string

class header(object):

    '''
       A header object stores the information obtained from a FITS file
       header, a text file containing header cards one per line, a list of
       header cards, or an existing PyFITS CardList.

       The header object also includes value and format validation through
       an on-demand implementation of the PyFITS output verification
       mechanism.  This guarantees that the header and its cards will
       always have the proper form.  See:

       http://archive.stsci.edu/fits/fits_standard/

       for FITS standard documentation.
    '''

    _IS_VERIFIED = False

    def __init__(self, filename=None, extension=0, card_list=None,
                 option='silentfix', *args, **kwargs):

        '''
           Create a new header object.

           If filename is not None, the header will be read from the
           specified extension (0 is PrimaryHDU, 1 is first ImageHDU, 2
           is second ImageHDU, etc.).

            filename: name of a valid FITS file containing the header
           card_list: a list of header cards (80 character strings, NULL
                      terminated), a pyfits.CardList instance, or the name
                      of a text file containing the header cards
              option: option used to verify the header (from PyFITS) should
                      be one of fix, silentfix, ignore, warn, or exception

           NOTE: The header cards in the form: key = value / comment
        '''

        self.filename   = filename or None
        self.extension  = extension
        self._card_list = card_list
        self.option     = option
        self._hdr       = None

        # Load header, verify header, and populate header attributes.
        self.load_header()

    def load(self):

        '''
           Synonym for load_header()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        self.load_header()

    def load_header(self):

        '''
           Load a header from a FITS file, or an ordinary text file or list.
           The attributes filename, extension, and card_list must either be
           set during construction or set manually before this method is
           called.

           The method attempts to load cards from a file if card_list is a
           string, or directly from card_list if it is a list.  If card_list
           is not defined, the header is loaded from the FITS file filename.
           Cards are assumed to be in the format:

           KEYWORD =                value / comment

           Cards should not exceed 80 characters unless they are COMMENT cards.
           Cards less than 80 characters will be padded as needed.

           NOTE: Cards should not contain newlines.
        '''

        if self._hdr is None:
            card_list = self._card_list
            if card_list is not None:
                if type(card_list) == str:
                    fd = file(card_list, 'r')
                    card_list = [line.strip('\n') for line in fd.readlines() if not line.startswith('END')]
                    fd.close()
                if type(card_list) == list:
                    header_cards = pyfits.CardList()
                    for card in card_list:
                        header_cards.append(pyfits.Card().fromstring(card))
                elif type(card_list) == pyfits.CardList:
                    header_cards = card_list
                else:
                    raise DARMAError, 'card_list (or source file) not in correct format!'
                self._hdr = pyfits.Header(cards=header_cards)
            elif self.filename is not None:
                try:
                    self._hdr = pyfits.getheader(self.filename, self.extension)
                except Exception, e:
                    raise DARMAError, 'Error loading header from %s: %s' % (self.filename, e)
            else:
                self._hdr = None
        else:
            if not isinstance(self._hdr, pyfits.Header):
                raise DARMAError, '%s must be a %s instance!' % (self._hdr, pyfits.Header)
        self.verify(option=self.option)

        if self._hdr is not None:
            allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
            for card in self._hdr.ascardlist():
                if card.key not in ['COMMENT', 'HISTORY', ''] and not hasattr(self, card.key):
                    attr = card.key.replace('-', '_')
                    for char in attr.upper():
                        if char not in allowed_chars:
                            attr = attr.replace(char, '_')
                    if isinstance(card, pyfits._Hierarch):
                        attr = 'HIERARCH_%s' % attr
                    setattr(self, attr, card)

    def _get_header(self):

        '''
           header 'getter' method
        '''

        self.load()
        return self._hdr

    def _set_header(self, hdr):

        '''
           header 'setter' method
        '''

        self._hdr = hdr
        self._IS_VERIFIED = False

    def _del_header(self):

        '''
           header 'deleter' method
        '''

        self._hdr = None
        self._IS_VERIFIED = False

    hdr = property(_get_header, _set_header, _del_header,
                   'Attribute to store the header')

    def _get_card_list(self):

        '''
           card_list 'getter' method
        '''

        if self.hdr is not None:
            self._card_list = self.hdr.ascardlist()
        else:
            self._card_list = None
        return self._card_list

    def _set_card_list(self, card_list):

        '''
           card_list 'setter' method
        '''

        self._card_list = card_list
        self._IS_VERIFIED = False

    def _del_card_list(self):

        '''
           card_list 'deleter' method
        '''

        del self._card_list

    card_list = property(_get_card_list, _set_card_list, _del_card_list,
                         'Attribute to store the list of cards for the header')

    def save(self, filename, raw=True):

        '''
           Save header to a text file.  The contents of filename will be
           overwritten.

           filename: mandatory name of the file to be written
                raw: write file as a raw, FITS-compatible file in binary mode
                     with 2880 byte blocks (if False, write a text file)
        '''

        if self.filename is None:
            self.filename = filename

        linelen = self.item_size()
        blksize = self.block_size()

        mode = {True : 'wb', False :  'w'}
        crlf = {True :   '', False : '\n'}
        fd = file(filename, mode[raw])
        cardlist = ['%s%s' % (str(card), crlf[raw]) for card in self.card_list]
        cardlist.append('END%s%s' % (' '*(linelen-3), crlf[raw]))
        if raw:
            while len(cardlist)*linelen%blksize:
                cardlist.append(' '*linelen)
        fd.writelines(cardlist)
        fd.close()

    def verify(self, option='silentfix'):

        '''
           Verify the card order and validity of card values in the current
           header.

           option: option used to verify the header (from PyFITS) should be
                   one of fix, silentfix, ignore, warn, or exception

           NOTE: As this is a dataless header, the BITPIX, NAXIS, and NAXISn
                 values are preserved from the original source, but are only
                 for informational purposes.  Once this header is paired with
                 data, these values will be overwritten with data-specific
                 values and may not match the original values.
        '''

        if self._hdr is not None and not self._IS_VERIFIED:
            hdr = self._hdr
            # Save changeable values.
            bitpix = hdr.ascardlist()['BITPIX']
            naxis = hdr.ascardlist()['NAXIS']
            naxisn = []
            for n in range(1,999):
                if hdr.get('NAXIS%d' % n) is not None:
                    naxisn.append(hdr.ascardlist()['NAXIS%d' % n])
                else:
                    break
            extend = hdr.get('EXTEND')
            if extend is not None:
                extend = hdr.ascardlist()['EXTEND']
            # Load header into appropriate HDU.
            if hdr.get('SIMPLE') is not None:
                hdu = pyfits.PrimaryHDU(header=hdr)
            elif hdr.get('XTENSION') is not None:
                hdu = pyfits.ImageHDU(header=hdr)
            else:
                raise DARMAError, 'Invalid header!  No SIMPLE or XTENSION keywords.'
            # Fix any bad keywords PyFITS won't prior to verification.
            for card in hdu.header.ascardlist():
                if card.key.count(' ') and not isinstance(card, pyfits._Hierarch):
                    new_key = card.key.replace(' ', '_')
                    if option != 'silentfix':
                        print 'WARNING -- renaming invalid key %s to %s' % (card.key, new_key)
                    hdu.header.rename_key(card.key, new_key)
            # Verify header within the HDU and copy back.
            hdu.verify(option=option)
            hdr = hdu.header
            del hdu
            # Add changeable values back.
            hdr.update(bitpix.key, bitpix.value, bitpix.comment)
            hdr.update(naxis.key, naxis.value, naxis.comment)
            n = ''
            if len(naxisn):
                card = naxisn[0]
                hdr.update(card.key, card.value, card.comment, after='NAXIS')
                n = 1
                for card in naxisn[1:]:
                    hdr.update(card.key, card.value, card.comment, after='NAXIS%d' % n)
                    n += 1
            if extend is not None:
                hdr.update(extend.key, extend.value, extend.comment, after='NAXIS%s' % n)
            self._hdr = hdr
            self._IS_VERIFIED = True

    def as_eclipse_header(self):

        '''
           Return a proper Eclipse header from this header object.
        '''

        from eclipse import header as e_header
        e_hdr = e_header.header().new()
        del e_header
        for card in self.card_list:
            if card.value is True:
                value = 'T'
            elif card.value is False:
                value = 'F'
            elif isinstance(card.value, str) and len(card.value) > 69:
                value = card.value[:69]
            else:
                value = card.value
            e_hdr.append(card.key, value, card.comment)
        e_hdr.append('END', '', '')
        return e_hdr

    def info(self):

        '''
           Show general information on this header.
        '''

        # Acquire attributes.
        length    = len(self)
        comments  = len(self.get_comment())
        history   = len(self.get_history())
        item_size = self.item_size()
        blksize   = self.block_size()
        data_size = length * item_size
        disk_size = data_size
        while disk_size%blksize:
            disk_size += item_size
        # Print them out.
        print '         class: %s'       %  self.__class__
        print '  total length: %s cards' %  length
        print '     (comment): %s cards' %  comments
        print '     (history): %s cards' %  history
        print '      itemsize: %s bytes' %  item_size
        print '     data size: %s bytes' %  data_size
        print '  size on disk: %s bytes' %  disk_size

    def item_size(self):

        '''
           Length of a header item (hard-coded to 80 characters)
        '''

        return 80
        #return len(str(self.header.ascardlist()[0]))

    def block_size(self):

        '''
           Length of a header data block written to a file (hard-coded to 2880
           bytes or 36 80-byte header items)
        '''

        return 2880
        #return self.item_size*36

    def get_comment(self):

        '''
           Get all comments as a list of string texts.
        '''

        return self.hdr.get_comment()

    def get_history(self):

        '''
           Get all histories as a list of string texts.
        '''

        return self.hdr.get_history()

    def add_blank(self, value='', before=None, after=None):

        '''
           Add a blank card.

            value: Text to be added (folds at 72 characters)
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            values.reverse()
        for value in values:
            self.hdr.add_blank(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def add_comment(self, value, before=None, after=None):

        '''
           Add a COMMENT card.

            value: comment text to be added (folds at 72 characters)
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            values.reverse()
        for value in values:
            self.hdr.add_comment(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def add_history(self, value, before=None, after=None):

        '''
           Add a HISTORY card.

            value: history text to be added (folds at 72 characters)
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            values.reverse()
        for value in values:
            self.hdr.add_history(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def rename_key(self, oldkey, newkey, force=True):

        '''
           Rename a card's keyword in the header.

           oldkey: old keyword, can be a name or index.
           newkey: new keyword, must be a string.
            force: if new key name already exist, force to have duplicate name.
        '''

        if oldkey in ['COMMENT', 'HISTORY', '']:
            raise DARMAError, 'Cannot rename %s key!' % oldkey
        if newkey in ['COMMENT', 'HISTORY', '']:
            raise DARMAError, 'Cannot rename %s key!' % newkey
        try:
            self.hdr.rename_key(oldkey, newkey, force=force)
            self._IS_VERIFIED = False
        except Exception, e:
            raise DARMAError, 'Error renaming %s in header: %s' % (oldkey, e)

    def dump(self):

        '''
           Dump the contents of the header to the screen.
        '''

        print self.card_list

    def new(self):

        '''
           Create a new empty header object.

           Make this header into a new empty header (no keywords).

           It is preferable to use default() to create a new header as the
           minimum keywords (see WARNING below) required to make a valid
           header will be provided automatically in the new header.  Also,
           these minimum values will be overwritten automatically when the
           header is paired with data anyway.


           WARNING: A minimum of SIMPLE or XTENSION, in addition to BITPIX and
                    NAXIS must be appended to this header object before it is
                    valid.  Unfortunately, on-demand verification makes this a
                    little tricky:

                   > h = darma.header.header()
                   > h = h.new()
                   > h['SIMPLE'] = True
                   > h._IS_VERIFIED = True  #prevents automatic verification
                   > h['BITPIX'] = 8
                   > h._IS_VERIFIED = True  #prevents automatic verification
                   > h['NAXIS'] = 0
                   > h.card_list
                   SIMPLE  =                    T / conforms to FITS standard
                   BITPIX  =                    8 / array data type
                   NAXIS   =                    0 / number of array dimensions
        '''

        self.hdr = pyfits.Header()
        self._IS_VERIFIED = True
        if not self.hdr:
            raise DARMAError, 'Error creating new header'
        return self

    def default(self, type='primary'):

        '''
           Create a default header object.

           type: type of header (primary or image)

           Make this header into a default header.

           A default header defines the keywords SIMPLE for a primary header,
           XTENSION for an image extension header, BITPIX, NAXIS (END will be
           added upon pairing with data when written to a file and cannot be
           added manually).  Also, the random groups PCOUNT and GCOUNT
           keywords will be added for image-type headers upon automatic
           verification.

           NOTE: primary-type headers are always the first and sometimes only
                 type of header in a FITS file.  image-type headers always
                 have a primary-type header at the begining of the FITS file
                 and cannot be the only header in the FITS file.
        '''

        if type is 'primary':
            self.hdr = pyfits.PrimaryHDU().header
        elif type is 'image':
            self.hdr = pyfits.ImageHDU().header
        else:
            raise DARMAError, 'type MUST be either "primary" or "image"!'
        self._IS_VERIFIED = False
        if not self.hdr:
            raise DARMAError, 'Error creating default header'
        return self

    def add(self, key, value, comment=None):

        '''
           Synonym for append().
        '''

        self.append(key, value, comment)

    def add_after(self, after, key, value, comment=None):

        '''
           Add a new key-value-comment tuple after an existing key.
        '''

        try:
            if key == 'COMMENT':
                result.add_comment(value, after=after)
            elif key == 'HISTORY':
                result.add_history(value, after=after)
            elif key == '':
                result.add_blank(value, after=after)
            else:
                self.update(key, value, comment=comment, after=after)
        except Exception, e:
            raise DARMAError, 'Error adding %s to header: %s' % (`(key, value, comment)`, e)

    def append(self, key, value, comment=None):

        '''
           Append a new key-value-comment card to the end of the header.  If
           the key exists, it is overwritten.
        '''

        # PyFITS does not consider terminal history, comment, or blank cards
        # when appending and will always add a new keyword before them.  Use
        # the numeric index to override this.
        last_key = len(self.card_list)-1
        try:
            if key == 'COMMENT':
                self.add_comment(value, after=last_key)
            elif key == 'HISTORY':
                self.add_history(value, after=last_key)
            elif key == '':
                self.add_blank(value, after=last_key)
            else:
                if self.has_key(key):
                    del self[key]
                self.update(key, value, comment=comment, after=last_key)
        except Exception, e:
            raise DARMAError, 'Error adding %s to header: %s' % (`(key, value, comment)`, e)

    def modify(self, key, value, comment=None):

        '''
           Modify the value and/or comment of an existing key.  If the key does
           not exist, it is appended to the end of the header.

           Synonym for update without the before and after options.
        '''

        try:
            self.update(key, value, comment=comment)
        except Exception, e:
            raise DARMAError, 'Error updating %s in header: %s' % (`(key, value, comment)`, e)

    def update(self, key, value, comment=None, before=None, after=None):

        '''
           Update a header keyword.  If the keyword doews not exists, it
           will be appended.
        '''

        if key in ['COMMENT', 'HISTORY', '']:
            raise DARMAError, 'Cannot update %s key!' % key
        try:
            self.hdr.update(key, value, comment=comment, before=before,
                            after=after)
            self._IS_VERIFIED = False
        except Exception, e:
            raise DARMAError, 'Error updating %s in header: %s' % (`(key, value, comment)`, e)

    def copy(self):

        '''
           Make a copy of the header.

           Returns a new header object containing the same values as this
           header object.
        '''

        result = header()
        if self.hdr is not None:
            result.hdr = self.hdr.copy()
            result.option = self.option
            if not result.hdr:
                raise DARMAError, 'Error copying header!'
        return result

    def merge(self, other, clobber=True):

        '''
           Merge this header with another header

           Returns a new header combining the values of this header with those
           of another header.  Header cards (keyword objects) from other are
           added to self.  If a card.key already exists in self, it is not
           overwritten unless clobber is True.
        '''

        result = self.copy()
        # Temporary keyword to act as a marker for the last keyword.  Do not
        # remove as the add_blank method requires this to work properly.
        result.append('_DUMMY_', '')
        for card in other.card_list:
            if card.key == 'COMMENT':
                result.add_comment(card.value, before='_DUMMY_')
                result._IS_VERIFIED = True
            elif card.key == 'HISTORY':
                result.add_history(card.value, before='_DUMMY_')
                result._IS_VERIFIED = True
            elif card.key == '':
                result.add_blank(card.value, before='_DUMMY_')
                result._IS_VERIFIED = True
            elif not result.hdr.has_key(card.key) or clobber:
                if isinstance(card, pyfits._Hierarch):
                    key = 'HIERARCH '+card.key
                else:
                    key = card.key
                result.update(key, card.value, comment=card.comment, before='_DUMMY_')
                result._IS_VERIFIED = True
        # Remove temporary keyword.
        del result['_DUMMY_']
        # Make sure unnecessary extension keywords are removed.  This is a
        # primary header, not an extension.
        ext_keys = ['EXTEND', 'XTENSION', 'EXTNAME', 'EXTVER', 'PCOUNT',
                    'GCOUNT']
        for key in ext_keys:
            if result[key] is not None:
                if key == 'EXTNAME':
                    result.rename_key('EXTNAME', '_EXTNAME')
                if key == 'EXTVER':
                    result.rename_key('EXTVER', '_EXTVER')
                else:
                    del result[key]
                result._IS_VERIFIED = True
        # Allow new header to be verified all at once.
        result._IS_VERIFIED = False
        if not result.hdr:
            raise DARMAError, 'Error merging headers'
        return result

    def merge_into_file(self, filename, clobber=True):

        '''
           Merge this header directly into a file containing another header.

           Merge this header into the FITS file named filename, overwriting
           where necessary if clobber is true.
        '''

        hdu = pyfits.open(filename, mode='update', memmap=1)
        orig_hdr = header(card_list=hdu[0].header.ascardlist(), option=self.option)
        self_hdr = self.copy()
        naxis_keys = ['NAXIS%d' % val for val in range(1, self_hdr['NAXIS']+1)]
        ignored_keys =  ['SIMPLE', 'BITPIX', 'NAXIS'] + naxis_keys
        for key in ignored_keys:
            del self_hdr.hdr[key]
        new_hdr = orig_hdr.merge(self_hdr, clobber=clobber)
        del self_hdr
        if new_hdr['ECLIPSE'] == 1:
            del new_hdr['ECLIPSE']
        if new_hdr['ORIGIN'] == 'eclipse':
            del new_hdr['ORIGIN']

        hdu[0].header = new_hdr.hdr
        hdu[0].update_header()
        self.hdr = hdu[0].header
        hdu.close(output_verify=self.option)

    def get_valstr(self, key):

        '''
           Return a keyword value as a string. DEPRECATED
        '''

        return str(self.get_value(key))

    def get_commentstr(self, key):

        '''
           Return a keyword comment as a string.
        '''

        try:
            return self.card_list[key].comment
        except:
            return None

    def get_value(self, key):

        '''
           Get a keyword value in its native datatype.
        '''

        if self.hdr is not None:
            value = self.hdr.get(key, default=None)
        else:
            value = None
        if isinstance(value, pyfits.Undefined):
            return 'Undefined'
        else:
            # Allow very long strings to be returned intact.
            if type(value) == str and value.count('CONTINUE'):
                while value.count('CONTINUE'):
                    value = '%s%s' % (value[:value.find('CONTINUE')-3], value[value.find('CONTINUE')+11:])
                value = value[1:-2]
            return value

    def has_key(self, key):

        '''
           Return the evaluation of the existance of a keyword in the header.
        '''

        return self.hdr.has_key(key) is 1

    def __len__(self):

        '''
           Number of header cards (excludes the END card).
        '''

        return len(self.hdr.items())

    def __getitem__(self, key):

        '''
           Get a keyword value in its native datatype.
        '''

        return self.get_value(key)

    def __setitem__(self, key, value):

        '''
           Add an item from value=value or value=(value, comment), overwriting if
           it exists.
        '''

        # Check if incoming key is nonstandard (i.e., should be HIERARCH).
        allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ '
        standard = True
        for char in key.upper():
            if char not in allowed_chars:
                standard = False
                break
        if (key.count(' ') or len(key) > 8 or not standard) and \
           not key.upper().startswith('HIERARCH'):
            key = 'HIERARCH %s' % key

        comment = None
        if isinstance(value, tuple):
            value, comment = value
        if key == 'COMMENT':
            self.add_comment(value)
        elif key == 'HISTORY':
            self.add_history(value)
        elif key == '':
            self.add_blank(value)
        elif self.has_key(key):
            self.modify(key, value, comment)
        else:
            self.add(key, value, comment)

        card = self.card_list[key]
        if card.key not in ['COMMENT', 'HISTORY', '']:
            attr = card.key.replace('-', '_').replace(' ', '_')
            for char in attr.upper():
                if char not in allowed_chars:
                    attr = attr.replace(char, '_')
            if isinstance(card, pyfits._Hierarch):
                attr = 'HIERARCH_%s' % attr
            setattr(self, attr, card)

    def __delitem__(self, key):

        '''
           Delete card(s) with the name key.
        '''

        self.hdr.__delitem__(key)
        self._IS_VERIFIED = False

        if hasattr(self, key):
            delattr(self, key)

    def __contains__(self, key):

        '''
           Returns existence of keyword key in header.
           x.__contains__(y) <==> y in x
        '''

        return self.has_key(key)

#-----------------------------------------------------------------------

def get_headers(filename):

    '''
       The sole purpose of this factory function is to create a list of
       headers from the headers in the FITS file filename.  If the file is
       single-extension, this is a list of one header.  If the file is
       multi-extension, this is a list of one primary header and N
       extension headers, where N is the number of extensions.

       filename: name of a valid FITS file, single- or multi-extension
    '''

    hdus = pyfits.open(filename)
    headers = [header(card_list=hdu.header.ascardlist()) for hdu in hdus]
    hdus.close()

    return headers

