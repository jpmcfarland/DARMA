'''A FITS header object resembling a dictionary.
'''

__version__ = '@(#)$Revision$'

import pyfits, os

from common import DARMAError

class header(object):

    '''
       The header object stores the information obtained from a FITS file
       header, a text file containing header cards one per line, or an
       existing PyFITS CardList.

       The header object also includes value and format validation through an
       on-demand imlementation of the PyFITS output verification mechanism.
       This guarantees that the header and its cards will always have the
       proper form.  See:

       http://archive.stsci.edu/fits/fits_standard/

       for FITS standard documentation.
    '''

    _IS_VERIFIED = False

    def __init__(self, filename=None, extension=0, card_list=None, *args,
                 **kwargs):

        '''
           Create a new header object.

           If filename is not None, the header will be read from the
           specified extension (0 is PrimaryHDU, 1 is first ImageHDU, 2 is
           second ImageHDU, etc.).

            filename: name of a valid FITS file containing the header
           card_list: a list of header cards (80 character strings, NULL
                      terminated), a pyfits.CardList instance, or the name of
                      a text file containing the header cards

           NOTE: The header cards in the form: key = value / comment
        '''

        self.filename   = filename or None
        self.extension  = extension
        self._card_list = card_list
        self._hdr       = None

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError, 'Filename: %s not found!' % self.filename

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
                    card_list = [line.strip('\n') for line in fd.readlines()]
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
        self.verify()

    def _get_header(self):

        '''
           Attribute to store the header.

           'getter' method.
        '''

        self.load()
        return self._hdr

    def _set_header(self, hdr):

        '''
           'setter' method.
        '''

        self._hdr = hdr
        self._IS_VERIFIED = False

    def _del_header(self):

        '''
           'deleter' method.
        '''

        self._hdr = None
        self._IS_VERIFIED = False

    hdr = property(_get_header, _set_header, _del_header)

    def _get_card_list(self):

        '''
           Attrubute to store the card list from the current header.

           'getter' method.
        '''

        if self.hdr is not None:
            self._card_list = self.hdr.ascard
        else:
            self._card_list = None
        return self._card_list

    def _set_card_list(self, card_list):

        '''
           'setter' method.
        '''

        self._card_list = card_list
        self._IS_VERIFIED = False

    def _del_card_list(self):

        '''
           'deleter' method.
        '''

        del self._card_list

    card_list = property(_get_card_list, _set_card_list, _del_card_list)

    def save(self, filename, raw=True):

        '''
           Save header to a text file.  The contents of filename will be
           overwritten.

           filename: mandatory name of the file to be written
                raw: write file as a raw, FITS-compatible file in binary mode
                     with 2880 byte blocks (if False, write a text file)
        '''

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

           NOTE: As this is a dataless header, the BITPIX, NAXIS, and NAXISn
                 values are preserved from the original source, but are only
                 for informational purposes.  Once this header is paired with
                 data, these values will be overwritten with data-specific
                 values and may not match the original values.
        '''

        if self._hdr is not None and not self._IS_VERIFIED:
            hdr = self._hdr
            # Save changeable values.
            bitpix = hdr.ascard['BITPIX']
            naxis = hdr.ascard['NAXIS']
            naxisn = []
            for n in range(1,999):
                try:
                    naxisn.append(hdr.ascard['NAXIS%d' % n])
                except:
                    break
            # Load header into appropriate HDU.
            if hdr.get('SIMPLE') is not None:
                hdu = pyfits.PrimaryHDU(header=hdr)
            elif hdr.get('XTENSION') is not None:
                hdu = pyfits.ImageHDU(header=hdr)
            else:
                raise DARMAError, 'Invalid header!  No SIMPLE or XTENSION keywords.'
            # Verify header within the HDU and copy back.
            hdu.verify(option=option)
            hdr = hdu.header
            del hdu
            # Add changeable values back.
            hdr.update(bitpix.key, bitpix.value, bitpix.comment)
            hdr.update(naxis.key, naxis.value, naxis.comment)
            n = 0
            for card in naxisn:
                if n == 0:
                    n=''
                hdr.update(card.key, card.value, card.comment, after='NAXIS%s' % n)
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
        #return len(str(self.header.ascard[0]))

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

    def set_blank(self, value='', before=None, after=None):

        '''
           Add a blank card.

            value: Text to be added.
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        self.hdr.add_blank(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def set_comment(self, value, before=None, after=None):

        '''
           Add a COMMENT card.

            value: comment text to be added.
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        self.hdr.add_comment(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def set_history(self, value, before=None, after=None):

        '''
           Add a HISTORY card.

            value: history text to be added.
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        self.hdr.add_history(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def rename_key(self, oldkey, newkey, force=0):

        '''
           Rename a card's keyword in the header.

           oldkey: old keyword, can be a name or index.
           newkey: new keyword, must be a string.
            force: if new key name already exist, force to have duplicate name.
        '''

        self.hdr.rename_key(oldkey=oldkey, newkey=newkey, force=force)
        self._IS_VERIFIED = False

    def dump(self):

        '''
           Dump the contents of the header as cards (header item objects).
           Cards can be accessed individually as in a dictionary:

           >>> hdr.dump()['BITPIX']          #get the entire card
           BITPIX  =                   16 / number of bits per data pixel
           >>> hdr.dump()['BITPIX'].key      #get just the card key
           'BITPIX'
           >>> hdr.dump()['BITPIX'].value    #get just the card value
           16
           >>> hdr.dump()['BITPIX'].comment  #get just the card comment
           'number of bits per data pixel'

           NOTE: The card_list attribute holds the same information this method
                 returns.
        '''

        return self.card_list

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

    def add(self, key, val, comment=None):

        '''
           Synonym for append().
        '''

        self.append(key, val, comment)

    def add_after(self, after_key, key, val, comment=None):

        '''
           Add a new key-value-comment tuple after an existing key.
        '''

        try:
            self.hdr.update(key, val, comment=comment, after=after_key)
            self._IS_VERIFIED = False
        except Exception, e:
            raise DARMAError, 'Error adding %s to header: %s' % (`(key, val, comment)`, e)

    def append(self, key, val, comment=None):

        '''
           Append a new key-value-comment tuple to the end of the header.  If
           the key exists, it is overwritten.
        '''

        try:
            if self.hdr.has_key(key):
                del self.hdr[key]
            self.hdr.update(key, val, comment=comment)
            self._IS_VERIFIED = False
        except Exception, e:
            raise DARMAError, 'Error adding %s to header: %s' % (`(key, val, comment)`, e)

    def modify(self, key, val, comment=None):

        '''
           Modify the value and/or comment of an existing key.  If the key does
           not exist, it is appended to the end of the header.
        '''

        try:
            self.hdr.update(key, val, comment=comment)
            self._IS_VERIFIED = False
        except Exception, e:
            raise DARMAError, 'Error modifying %s in header: %s' % (`(key, val, comment)`, e)

    def copy(self):

        '''
           Make a copy of the header.

           Returns a new header object containing the same values as this
           header object.
        '''

        result = header()
        result.hdr = self.hdr.copy()
        if not result.hdr:
            raise DARMAError, 'Error copying header!'
        return result

    def merge(self, other, clobber=True):

        '''
           Merge this header with another header

           Returns a new header combining the values of this header with those
           of another header.  header cards (keyword objects) from other are
           added to self.  If a card.key already exists in self, it is not
           overwritten unless clobber is True.
        '''

        result = self.copy()
        for card in other.card_list:
            if not result.hdr.has_key(card.key) or clobber:
                result.hdr.update(card.key, card.value, comment=card.comment)
        self._IS_VERIFIED = False
        if not result.hdr:
            raise DARMAError, 'Error merging headers'
        return result

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
            return self.hdr.ascard[key].comment
        except:
            return None

    def get_value(self, key):

        '''
           Get a keyword value in its native datatype.
        '''

        value = self.hdr.get(key, default=None)
        if isinstance(value, pyfits.Undefined):
            return 'Undefined'
        else:
            return value

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
           Add an item from val=value or val=(value, comment), overwriting if
           it exists.
        '''

        comment = None
        if isinstance(value, tuple):
            value, comment = value
        if self.get_value(key) == None:
            self.add(key, value, comment)
        else:
            self.modify(key, value, comment)
        self._IS_VERIFIED = False

    def __delitem__(self, key):

        '''
           Delete card(s) with the name key.
        '''

        self.hdr.__delitem__(key)
        self._IS_VERIFIED = False

