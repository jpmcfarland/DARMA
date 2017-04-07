'''A FITS header object resembling a dictionary.
'''

__version__ = '@(#)$Revision$'

import os

from .common import fits, DARMAError, range, unicode, fits_open, is_hierarch
from .common import _strip_keyword, _get_index, get_history, get_value
from .common import fold_string, add_blank, rename_keyword, update_header
from .common import get_cards, get_keyword, get_cardimage, get_comment
from .common import clear_header, getheader


class header(object):

    '''
       A header object stores the information obtained from a FITS file
       header, a text file containing header cards one per line, a list of
       header card strings, or a list of fits.Card instances.

       The header object also includes value and format validation through
       an on-demand implementation of the Astropy/PyFITS output verification
       mechanism.  This guarantees that the header and its cards will
       always have the proper form.  See:

       http://archive.stsci.edu/fits/fits_standard/

       for FITS standard documentation.
    '''

    _IS_VERIFIED = False

    def __init__(self, filename=None, extension=0, cardlist=None,
                 option='silentfix'):
        '''
           Create a new header object.

           If filename is not None, the header will be read from the
           specified extension (0 is PrimaryHDU, 1 is first ImageHDU, 2
           is second ImageHDU, etc.).

            filename: name of a valid FITS file containing the header
           extension: extension number of the header to be loaded
            cardlist: a list of header cards (80 character strings, NULL
                      terminated), a list of fits.Card instances, or the
                      name of a text file containing the header cards
              option: option used to verify the header (from
                      Astropy/PyFITS) should be one of fix, silentfix,
                      ignore, warn, or exception (ignore disables
                      on-demand verification)

           NOTE: Standard header cards are in the form:

                 keyword = value / comment
        '''

        self.filename = filename or None
        self.extension = extension
        self.cardlist = cardlist
        self.option = option
        self._hdr = None
        self._cards = None

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
           The attributes filename, extension, and cardlist must either be
           set during construction or set manually before this method is
           called.

           The method attempts to load cards from a file if cardlist is a
           string, or directly from cardlist if it is a list.  If cardlist
           is not defined, the header is loaded from the FITS file filename.
           Cards are assumed to be in the format:

           keyword =                value / comment

           Cards should not exceed 80 characters unless they are COMMENT cards.
           Cards less than 80 characters will be padded as needed.

           NOTE: Cards should not contain newlines.
        '''

        if self._hdr is None:
            cardlist = self.cardlist
            if cardlist is not None:
                # XXX make cardlist files multi-extension aware?
                if isinstance(cardlist, (str, unicode)):
                    try:
                        with open(cardlist, 'r') as fd:
                            lines = fd.read()
                    except Exception as e:
                        raise DARMAError('ERROR -- could not load cardlist %s: %s' % (cardlist, e))
                    # ASCII file.
                    if '\n' in lines:
                        header_card_strings = [line for line in lines.split(
                            '\n') if not line.startswith('END     ')]
                    # Raw FITS file.
                    else:
                        size = self.item_size()
                        header_card_strings = [lines[i:i + size]
                                               for i in range(0, len(lines), size) if not lines[i:i + size].startswith('END     ')]
                    header_cards = [fromstring(string) for string in header_card_strings if not (
                        string.startswith(' ') or not len(string))]
                elif isinstance(cardlist, list):
                    header_cards = []  # list of Card instances
                    if len(cardlist):
                        if isinstance(cardlist[0], (str, unicode)):
                            indexes = [0]
                            if self.extension != 0:
                                for i in range(len(cardlist)):
                                    if cardlist[i].startswith('END     '):
                                        indexes.append(i + 1)
                                # remove location of last END card
                                _ = indexes.pop(-1)
                            if self.extension >= len(indexes):
                                raise DARMAError('extension %d is not in cardlist!' % self.extension)
                            for card in cardlist[indexes[self.extension]:]:
                                if not card.startswith('END'):
                                    # cast unicode types as strings
                                    header_cards.append(fromstring(str(card)))
                                else:
                                    break
                        elif isinstance(cardlist[0], fits.Card):
                            header_cards = cardlist
                        else:
                            raise DARMAError('cardlist not in correct format!')
                else:
                    raise DARMAError('source file (or cardlist) not in correct format!')
                self._hdr = fits.Header(cards=header_cards)
            elif self.filename is not None:
                # Initialize variables to allow closing file if error
                hdus, hdu = None, None
                try:
                    hdus = fits_open(self.filename)
                    hdu = hdus[self.extension]
                    # Use _header to get the raw header of the HDU
                    self._hdr = hdu._header
                    hdus.close()
                    del hdu, hdus
                except Exception as e:
                    if hdus:
                        hdus.close()
                        del hdus
                    if hdu:
                        del hdu
                    raise DARMAError('Error loading header from %s: %s' % (self.filename, e))
            else:
                self._hdr = fits.Header()
        else:
            if not isinstance(self._hdr, fits.Header):
                raise DARMAError('%s must be a %s instance!' % (self._hdr, fits.Header))
        # Set the initial _cards attribute from the verified header property
        self._cards = get_cards(self.hdr)

    def _set_attributes(self):
        '''
           Set attribute values from cards in header
        '''

        if self._hdr is not None:
            allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
            for card in get_cards(self._hdr):
                attr = get_keyword(card).replace('-', '_')
                if attr not in ['COMMENT', 'HISTORY', ''] and not hasattr(self, attr):
                    for char in attr.upper():
                        if char not in allowed_chars:
                            attr = attr.replace(char, '_')
                    if is_hierarch(card):
                        attr = 'HIERARCH_%s' % attr
                    setattr(self, attr, card)

    def _get_hdr(self):
        '''
           header 'getter' method
        '''
        if self._hdr is None:
            self.load()
        self.verify(option=self.option)

        return self._hdr

    def _set_hdr(self, hdr):
        '''
           header 'setter' method
        '''

        self._hdr = hdr
        self._IS_VERIFIED = False

    def _del_hdr(self):
        '''
           header 'deleter' method
        '''

        del self._hdr, self.cards
        self._hdr = None

    hdr = property(_get_hdr, _set_hdr, _del_hdr,
                   'Attribute to store the header')

    def _get_cards(self):
        '''
           cards 'getter' method
        '''

        if self._hdr is None:
            self._cards = get_cards(fits.Header())
        else:
            self._cards = get_cards(self.hdr)
        return self._cards

    def _set_cards(self, cards):
        '''
           cards 'setter' method
        '''

        # cards only ever set from header within _get_cards()
        pass

    def _del_cards(self):
        '''
           cards 'deleter' method
        '''

        del self._cards
        self._cards = get_cards(fits.Header())

    cards = property(_get_cards, _set_cards, _del_cards,
                     'Attribute to store the list of cards for the header')

    def _get_blank(self):
        '''
           blank 'getter' method
        '''

        return self.get_blank()

    def _del_blank(self):
        '''
           blank 'deleter' method
        '''

        del self['']

    # Name the BLANK cards property to avoid clashes with a BLANK keyword.
    BLANK__ = property(_get_blank, None, _del_blank,
                       'Attribute to return the list of BLANK cards')

    def _get_comment(self):
        '''
           comment 'getter' method
        '''

        return self.get_comment()

    def _del_comment(self):
        '''
           comment 'deleter' method
        '''

        del self['COMMENT']

    COMMENT = property(_get_comment, None, _del_comment,
                       'Attribute to return the list of COMMENT cards')

    def _get_history(self):
        '''
           history 'getter' method
        '''

        return self.get_history()

    def _del_history(self):
        '''
           history 'deleter' method
        '''

        del self['HISTORY']

    HISTORY = property(_get_history, None, _del_history,
                       'Attribute to return the list of HISTORY cards')

    def __del__(self):
        '''
           Cleanup headers before destruction
        '''

        del self.hdr  # also deletes self.cards

    def save(self, filename, raw=True, mode='clobber', dataless=False):
        '''
           Save header to a text file.  The contents of filename will be
           overwritten if mode='clobber'.

           filename: mandatory name of the file to be written
                raw: write file as a raw, FITS-compatible file in binary
                     mode with 2880 byte blocks (if False, write a text
                     file)
               mode: clobber (default) overwrites the file and append
                     appends a new header onto the existing file
           dataless: if true, remove NAXISn from output and set BITPIX
                     to 8 and NAXIS to 0 (prevents data size warnings
                     when loading this dataless header from file)
        '''

        modes = ['clobber', 'append']

        if mode not in modes:
            raise DARMAError('mode \'%s\' not supported!  Use one of %s instead.' % (mode, modes))

        if mode == 'clobber':
            mode = {True: 'wb', False:  'w'}
        if mode == 'append':
            mode = {True: 'ab', False:  'a'}

        hdr = self.copy()
        if hdr.filename is None:
            hdr.filename = filename

        linelen = hdr.item_size()
        blksize = hdr.block_size()

        if dataless:
            for n in range(1, 999):
                keyword = 'NAXIS%d' % n
                if keyword in hdr:
                    del hdr[keyword]
                else:
                    break
            hdr['BITPIX'] = 8
            hdr['NAXIS'] = 0

        if raw:
            cardlist = [get_cardimage(card).encode() for card in hdr.itercards()]
            cardlist.append(str.encode('END%s' % (' ' * (linelen - 3))))
            while len(cardlist) * linelen % blksize:
                cardlist.append(str.encode(' ' * linelen))
        else:
            cardlist = ['%s\n' % get_cardimage(card) for card in hdr.itercards()]
            cardlist.append('END%s\n' % (' ' * (linelen - 3)))
        with open(filename, mode[raw]) as fd:
            fd.writelines(cardlist)

    def verify(self, option='silentfix'):
        '''
           Verify the card order and validity of card values in the current
           header.

           option: option used to verify the header (from PyFITS) should be
                   one of fix, silentfix, ignore, warn, or exception
                   (ignore disables on-demand verification)

           NOTE: As this is a dataless header, the BITPIX, NAXIS, and NAXISn
                 values are preserved from the original source, but are only
                 for informational purposes.  Once this header is paired with
                 data, these values will be overwritten with data-specific
                 values and may not match the original values.
        '''

        if self.option == 'ignore':
            self._IS_VERIFIED = True
            self._set_attributes()
            return
        if self._hdr is not None and not self._IS_VERIFIED:
            hdr = self._hdr
            cards = get_cards(hdr)
            # Primary header keywords.
            extend = None
            if 'EXTEND' in hdr:
                extend = cards['EXTEND']
            simple = get_value(hdr, 'SIMPLE')
            # Extension header keywords.
            xtension = get_value(hdr, 'XTENSION')
            # Common keywords.
            bitpix, naxis = None, None
            if 'BITPIX' in hdr:
                bitpix = cards['BITPIX']
            if 'NAXIS' in hdr:
                naxis = cards['NAXIS']
            # Add cards required for PyFITS verification (they will be
            # removed later as necessary).
            ADDED_SIMPLE, ADDED_BITPIX, ADDED_NAXIS = False, False, False
            if simple is None and xtension is None:
                update_header(hdr, 'SIMPLE', True, 'conforms to FITS standard')
                simple = True
                ADDED_SIMPLE = True
            if bitpix is None:
                update_header(hdr, 'BITPIX', 8, 'array data type')
                bitpix = cards['BITPIX']
                ADDED_BITPIX = True
            if naxis is None:
                update_header(hdr, 'NAXIS', 0, 'number of array dimensions')
                naxis = cards['NAXIS']
                ADDED_NAXIS = True
            naxisn = []
            for n in range(1, 999):
                if 'NAXIS%d' % n in hdr:
                    naxisn.append(cards['NAXIS%d' % n])
                else:
                    break
            # Load header into appropriate HDU.
            if simple is not None:
                hdu = fits.PrimaryHDU(header=hdr)
            elif xtension == 'IMAGE':
                hdu = fits.ImageHDU(header=hdr)
            elif xtension == 'BINTABLE':
                hdu = fits.BinTableHDU(header=hdr)
            elif xtension == 'TABLE':
                hdu = fits.TableHDU(header=hdr)
            else:
                raise DARMAError('Invalid header!  No SIMPLE or XTENSION keywords.')
            # Fix any bad keywords PyFITS won't prior to verification.
            for card in list(get_cards(hdu.header)):
                keyword = get_keyword(card)
                value = card.value
                comment = card.comment
                if keyword.count(' ') and not is_hierarch(card):
                    if option == 'fix':
                        key = keyword.replace(' ', '_')
                        print('WARNING -- renaming invalid keyword %s to %s' % (keyword, key))
                        if key in hdu.header:
                            update_header(hdu.header, key, value, comment)
                            # del hdu.header[keyword] # unnecessary?
                        else:
                            rename_keyword(hdu.header, keyword, key)
                    elif option == 'silentfix':
                        key = keyword.replace(' ', '_')
                        if key in hdu.header:
                            update_header(hdu.header, key, value, comment)
                            # del hdu.header[keyword] # unnecessary?
                        else:
                            rename_keyword(hdu.header, keyword, key)
                    elif option == 'warn':
                        print('WARNING -- found invalid keyword %s' % keyword)
                    elif option == 'exception':
                        raise DARMAError('Found invalid keyword %s' % keyword)
            # Verify header within the HDU and copy back.
            hdu.verify(option=option)
            hdr = hdu._header
            del hdu
            # Remove temporary cards and add changeable values back.
            if ADDED_SIMPLE:
                hdr.__delitem__('SIMPLE')
            if ADDED_BITPIX:
                hdr.__delitem__('BITPIX')
            else:
                update_header(hdr, get_keyword(bitpix), bitpix.value, bitpix.comment)
            if ADDED_NAXIS:
                hdr.__delitem__('NAXIS')
            else:
                update_header(hdr, get_keyword(naxis), naxis.value, naxis.comment)
            n = ''
            if len(naxisn):
                card = naxisn[0]
                update_header(hdr, get_keyword(card), card.value, card.comment, after='NAXIS')
                n = 1
                for card in naxisn[1:]:
                    update_header(hdr, get_keyword(card), card.value, card.comment, after='NAXIS%d' % n)
                    n += 1
            if extend is not None:
                update_header(hdr, get_keyword(extend), extend.value, extend.comment, after='NAXIS%s' % n)
            self._hdr = hdr
            self._IS_VERIFIED = True
        # FIXME find out why this is necessary
        if option == 'silentfix' and self._hdr is not None:
            for keyword in self._hdr.keys():
                try:
                    value = self._hdr[keyword]
                except ValueError as e:
                    self._hdr.__delitem__(keyword)
        # FIXME
        self._set_attributes()

    def as_eclipse_header(self):
        '''
           Return a proper Eclipse header from this header object.
        '''

        from eclipse import header as e_header
        e_hdr = e_header.header().new()
        del e_header
        for card in self:
            if card.value is True:
                value = 'T'
            elif card.value is False:
                value = 'F'
            elif isinstance(card.value, (str, unicode)) and len(card.value) > 69:
                value = card.value[:69]
            else:
                value = card.value
            e_hdr.append(get_keyword(card), value, card.comment)
        e_hdr.append('END', '', '')
        return e_hdr

    def index(self, keyword):
        '''
           Return the integer index of the keyword in this header.

             keyword: a string keyword value
        '''

        return _get_index(self.hdr, keyword)

    def info(self):
        '''
           Show general information on this header.
        '''

        # Acquire attributes.
        length = len(self)
        comments = len(self.get_comment())
        history = len(self.get_history())
        item_size = self.item_size()
        blksize = self.block_size()
        data_size = length * item_size
        disk_size = data_size
        while disk_size % blksize:
            disk_size += item_size
        # Print them out.
        print('         class: %s' % self.__class__)
        print('  total length: %s cards' % length)
        print('     (comment): %s cards' % comments)
        print('     (history): %s cards' % history)
        print('      itemsize: %s bytes' % item_size)
        print('     data size: %s bytes' % data_size)
        print('  size on disk: %s bytes' % disk_size)

    def item_size(self):
        '''
           Length of a header item (hard-coded to 80 characters)
        '''

        return 80

    def block_size(self):
        '''
           Length of a header data block written to a file (hard-coded to 2880
           bytes or 36 80-byte header items)
        '''

        return 2880

    def get_blank(self):
        '''
           Get all blank cards as a list of string texts.
        '''

        return [card.value for card in self.itercards() if get_keyword(card) == '']

    def get_blank_cards(self):
        '''
           Get all blank card values as a list of header cards where
           applicable (i.e., if no proper header cards exist in the
           blank card values, the returned card list is empty).
        '''

        blanks = self.get_blank()
        cards = []
        for blank in blanks:
            try:
                card = fromstring(blank, verify='exception')
                cards.append(card)
            except:
                pass
        return cards

    def get_comment(self):
        '''
           Get all comments as a list of string texts.
        '''

        return get_comment(self.hdr)

    def get_comment_cards(self):
        '''
           Get all comments as a list of header cards where applicable
           (i.e., if no proper header cards exist in the comments, the
           returned card list is empty).
        '''

        comments = self.get_comment()
        cards = []
        for comment in comments:
            try:
                card = fromstring(comment, verify='exception')
                cards.append(card)
            except:
                pass
        return cards

    def get_history(self):
        '''
           Get all histories as a list of string texts.
        '''

        return get_history(self.hdr)

    def get_history_cards(self):
        '''
           Get all histories as a list of header cards where applicable
           (i.e., if no proper header cards exist in the histories, the
           returned card list is empty).
        '''

        historys = self.get_history()
        cards = []
        for history in historys:
            try:
                card = fromstring(history, verify='exception')
                cards.append(card)
            except:
                pass
        return cards

    def add_blank(self, value='', before=None, after=None):
        '''
           Add a blank card.

            value: Text to be added (folds at 72 characters)
           before: keyword to place blank before
            after: keyword to place blank after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            # cards are added in reverse order
            values.reverse()
        for value in values:
            add_blank(self._hdr, value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def add_comment(self, value, before=None, after=None):
        '''
           Add a COMMENT card.

            value: comment text to be added (folds at 72 characters)
           before: keyword to place comment before
            after: keyword to place comment after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            # cards are added in reverse order
            values.reverse()
        for value in values:
            self._hdr.add_comment(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def add_history(self, value, before=None, after=None):
        '''
           Add a HISTORY card.

            value: history text to be added (folds at 72 characters)
           before: keyword to place history before
            after: keyword to place history after
        '''

        values = fold_string(value, num=72).split('\n')
        if after:
            # cards are added in reverse order
            values.reverse()
        for value in values:
            self._hdr.add_history(value=value, before=before, after=after)
        self._IS_VERIFIED = False

    def rename_keyword(self, oldkeyword, newkeyword):
        '''
           Rename a card's keyword in the header.

           oldkeyword: old keyword, can be a name or index.
           newkeyword: new keyword, must be a string.
        '''

        if oldkeyword in ['COMMENT', 'HISTORY', '']:
            raise DARMAError('Cannot rename existing %s keyword!' % oldkeyword)
        if newkeyword in ['COMMENT', 'HISTORY', '']:
            raise DARMAError('Cannot rename to %s keyword!' % newkeyword)
        try:
            card = getattr(self, oldkeyword.replace(' ', '_'))
            rename_keyword(self._hdr, oldkeyword, newkeyword)
            setattr(self, newkeyword.replace(' ', '_'), card)
            delattr(self, oldkeyword.replace(' ', '_'))
            self._IS_VERIFIED = False
        except Exception as e:
            raise DARMAError('Error renaming %s in header: %s' % (oldkeyword, e))

    def rename_key(self, oldkey, newkey):
        '''
           Synonym for rename_keyowrd()

           Rename a card's keyword in the header.

           oldkey: old keyword, can be a name or index.
           newkey: new keyword, must be a string.
        '''

        self.rename_keyword(oldkey, newkey)

    def dump(self):
        '''
           Dump the contents of the header to the screen (less the END
           card and padding blank cards).
        '''

        for card in self.cards:
            print(get_cardimage(card))

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
                    valid.

                   > h = darma.header.header()
                   > h = h.new()
                   > h['SIMPLE'] = True
                   > h['BITPIX'] = 8
                   > h['NAXIS'] = 0
                   > h.cards
                   SIMPLE  =                    T / conforms to FITS standard
                   BITPIX  =                    8 / array data type
                   NAXIS   =                    0 / number of array dimensions
        '''

        # FIXME
        # FIXME look into returning a new header leaving this one intact
        # FIXME

        self.hdr = fits.Header()
        # Set the initial _cards attribute from the verified header property
        self._cards = get_cards(self.hdr)
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
            self.hdr = fits.PrimaryHDU().header
        elif type is 'image':
            self.hdr = fits.ImageHDU().header
        else:
            raise DARMAError('type MUST be either "primary" or "image"!')
        if not isinstance(self._hdr, fits.Header):
            raise DARMAError('Error creating default header')
        # Set the initial _cards attribute from the verified header property
        self._cards = get_cards(self.hdr)
        return self

    def add(self, keyword, value, comment=None):
        '''
           Synonym for append().
        '''

        self.append(keyword, value, comment)

    def add_after(self, after, keyword, value, comment=None):
        '''
           Add a new keyword-value-comment tuple after an existing keyword.

               after: existing keyword to add after
             keyword: keyword string
               value: value
             comment: comment string
        '''

        try:
            if keyword == 'COMMENT':
                self.add_comment(value, after=after)
            elif keyword == 'HISTORY':
                self.add_history(value, after=after)
            elif keyword == '':
                self.add_blank(value, after=after)
            else:
                self.update(keyword, value, comment=comment, after=after)
        except Exception as e:
            raise DARMAError('Error adding %s to header: %s' % (repr((keyword, value, comment)), e))

    def append(self, keyword, value, comment=None, force=False):
        '''
           Append a new keyword-value-comment card to the end of the
           header.  If the keyword exists, it is overwritten.

             keyword: keyword string
               value: value
             comment: comment string
               force: force appending to end of header

           NOTE: By default, Astropy/PyFITS group BLANK, COMMENT and
                 then HISTORY cards at the end of a header, appending
                 normal card at the bottom, before these special cards.

                 Force overrides this behavior and appends any card to
                 the end of the header.
        '''

        last_keyword = None
        if force:
            last_keyword = len(self.cards) - 1
        try:
            if keyword == 'COMMENT':
                self.add_comment(value, after=last_keyword)
            elif keyword == 'HISTORY':
                self.add_history(value, after=last_keyword)
            elif keyword == '':
                self.add_blank(value, after=last_keyword)
            else:
                if keyword in self:
                    del self[keyword]
                self.update(keyword, value, comment=comment, after=last_keyword)
        except Exception as e:
            raise DARMAError('Error adding %s to header: %s' % (repr((keyword, value, comment)), e))

    def fromstring(self, cardstring):
        '''
           Append a new standard card from a 80 character card string
           overwriting when the same named card.keyword exists:

           'SIMPLE  =                    T / conforms to FITS standard...'

           A standard card has the form of no more than 8 capital letters,
           numbers, or underscores, a padding of spaces, = at the 9th column,
           a space followed by a value, a ' / ', then the comment.  A standard
           card string will have exactly 80 columns.

           An attempt is made to standardize the cardstring by padding
           appropriately and truncating the comment when necessary.  No
           attempt is made to correct the keyword and value beyond
           capitalizing the keyword.
        '''

        card = fromstring(cardstring, verify=self.option)
        keyword = get_keyword(card)
        if keyword in self._hdr and keyword not in ['', 'COMMENT', 'HISTORY']:
            del self[keyword]
        self.append(get_keyword(card), card.value, comment=card.comment)

    def modify(self, keyword, value, comment=None):
        '''
           Modify the value and/or comment of an existing keyword.  If
           the keyword does not exist, it is appended to the end of the
           header.

           Synonym for update without the before and after options.
        '''

        try:
            self.update(keyword, value, comment=comment)
        except Exception as e:
            raise DARMAError('Error updating %s in header: %s' % (repr((key, value, comment)), e))

    def update(self, keyword, value, comment=None, before=None, after=None):
        '''
           Update a header keyword.  If the keyword doews not exists, it
           will be appended.
        '''

        if keyword in ['COMMENT', 'HISTORY', '']:
            raise DARMAError('Cannot update %s keyword!' % keyword)
        try:
            update_header(self._hdr, keyword, value, comment=comment,
                          before=before, after=after)
            self._IS_VERIFIED = False
        except Exception as e:
            raise DARMAError('Error updating %s in header: %s' % (repr((keyword, value, comment)), e))

    def copy(self):
        '''
           Make a copy of the header.

           Returns a new header object containing the same values as this
           header object.
        '''

        result = header()
        result.hdr = self.hdr.copy()
        result.option = self.option
        if not isinstance(result.hdr, fits.Header):
            raise DARMAError('Error copying header!')
        return result

    def merge(self, other, clobber=True):
        '''
           Merge this header with another header.  Returns a new header
           combining the values of this header with those of another
           header.  Header cards from other are added to a copy of self.

               other: header to merge into this one
             clobber: overwrite existing keywords in this header
        '''

        result = self.copy()
        # Temporary keyword to act as a marker for the last keyword.  Do not
        # remove as the add_blank method requires this to work properly.
        result.append('_DUMMY_', '')
        for card in other.cards:
            keyword = get_keyword(card)
            if keyword == 'COMMENT':
                result.add_comment(card.value, before='_DUMMY_')
            elif keyword == 'HISTORY':
                result.add_history(card.value, before='_DUMMY_')
            elif keyword == '':
                result.add_blank(card.value, before='_DUMMY_')
            elif keyword not in result._hdr or clobber:
                if is_hierarch(card):
                    keyword = 'HIERARCH ' + keyword
                result.update(keyword, card.value, comment=card.comment, before='_DUMMY_')
        # Remove temporary keyword.
        del result['_DUMMY_']
        result.verify()
        return result

    def merge_into_file(self, filename, clobber=True):
        '''
           Merge this header directly into the primary header of an existing
           file.

             filename: name of file in which to merge this header
              clobber: overwrite existing keywords in file
        '''

        orig_hdr = header(cardlist=list(get_cards(getheader(filename, 0))), option=self.option)
        self_hdr = self.copy()
        naxis_keywords = ['NAXIS%d' % val for val in range(1, self_hdr['NAXIS'] + 1)]
        ignored_keywords = ['SIMPLE', 'BITPIX', 'NAXIS'] + naxis_keywords
        for keyword in ignored_keywords:
            if keyword in self_hdr._hdr:
                del self_hdr._hdr[keyword]
        new_hdr = orig_hdr.merge(self_hdr, clobber=clobber)
        del self_hdr
        # XXX PyFITS/Astropy have a bug in Python 3 that corrupts larger FITS
        # XXX files upon writing when opened in 'update' mode and the file
        # XXX size changes.  Write a new file to work around this bug.
        if abs(len(orig_hdr) - len(new_hdr)) < 36:
            hdus = fits_open(filename, mode='update', memmap=True)
            hdus[0].header = new_hdr.hdr
            hdus[0].update_header()
            hdus.close(output_verify=self.option)
        else:
            with fits_open(filename, mode='update', memmap=True) as hdus:
                hdus[0].header = new_hdr.hdr
                hdus[0].update_header()
                hdus.writeto(filename+'.new', output_verify=self.option)
            os.remove(filename)
            os.rename(filename+'.new', filename)
        # XXX TODO EMH PyFits in the module NA_pyfits.py does something nasty.
        # Under certain circumstances the signal handler is redefined to
        # ignore Ctrl-C keystrokes, the next two lines mean to reset the signal
        # handler to its original state, which is omitted in PyFits.
        import signal
        signal.signal(signal.SIGINT, signal.default_int_handler)

    def __len__(self):
        '''
           Number of header cards (excludes the END card).
        '''

        return len(get_cards(self.hdr))

    def __getitem__(self, keyword):
        '''
           Get a keyword value in its native datatype.
        '''

        keyword = _strip_keyword(keyword)
        if self._hdr is not None:
            value = get_value(self.hdr, keyword, default=None)
        else:
            value = None
        if isinstance(value, fits.Undefined):
            return 'Undefined'
        else:
            # Allow very long strings to be returned intact.
            if isinstance(value, (str, unicode)) and value.count('CONTINUE'):
                while value.count('CONTINUE'):
                    value = '%s%s' % (value[:value.find('CONTINUE') - 3], value[value.find('CONTINUE') + 11:])
                value = value[1:-2]
            return value

    def __setitem__(self, keyword, value):
        '''
           Add an item from value=value or value=(value, comment),
           overwriting if it exists.
        '''

        # Check if incoming keyword is nonstandard (i.e., should be HIERARCH).
        allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ '
        standard = True
        for char in keyword.upper():
            if char not in allowed_chars:
                standard = False
                break
        if (len(keyword) > 8 or not standard) and not keyword.startswith('HIERARCH '):
            keyword = 'HIERARCH %s' % keyword
        comment = None
        if isinstance(value, tuple):
            value, comment = value
        if keyword == 'COMMENT':
            self.add_comment(value)
        elif keyword == 'HISTORY':
            self.add_history(value)
        elif keyword == '':
            self.add_blank(value)
        else:
            self.update(keyword, value, comment)
        card = get_cards(self._hdr)[_strip_keyword(keyword)]
        # XXX explore setting COMMENT, HISTORY, and BLANK cards to the
        # XXX corresponding attribute
        if get_keyword(card) not in ['COMMENT', 'HISTORY', '']:
            attr = get_keyword(card).replace('-', '_')
            for char in attr.upper():
                if char not in allowed_chars:
                    attr = attr.replace(char, '_')
            if is_hierarch(card):
                attr = 'HIERARCH_%s' % attr
            setattr(self, attr, card)
        self._IS_VERIFIED = False

    def __delitem__(self, keyword):
        '''
           Delete card(s) with the name keyword.
        '''

        self._hdr.__delitem__(keyword)
        self._IS_VERIFIED = False

        if hasattr(self, keyword):
            delattr(self, keyword)

    # def __getattribute__(self, name):

    #    '''
    #       x.__getattribute__('name') <==> x.name
    #    '''

    #    return object.__getattribute__(self, name)

    # def __setattr__(self, name, value):

    #    '''
    #       x.__setattr__('name', value) <==> x.name = value
    #    '''

    #    if name.upper() == name:
    #        self[name] = value
    #    else:
    #        object.__setattr__(self, name, value)

    # def __delattr__(self, name):

    #    '''
    #       x.__delattr__('name') <==> del x.name
    #    '''

    #    if hasattr(self, keyword):
    #        delattr(self, keyword)
    #    if keyword in self._hdr:
    #        self._hdr.__delitem__(keyword)
    #    self._IS_VERIFIED = False

    def __contains__(self, keyword):
        '''
           Returns existence of keyword in header.
           x.__contains__(y) <==> y in x
        '''

        return self.hdr.__contains__(_strip_keyword(keyword))

    def __repr__(self):
        '''
           x.__repr__() <==> repr(x)
        '''

        return_string = str(self.__class__) + '\n'
        if self._hdr is None:
            return return_string[:-1]
        if len(self.cards):
            repr_list = []
            for card in self.itercards():
                if get_keyword(card) != '' and card.value != '':
                    repr_list.append(get_cardimage(card))
            if len(repr_list):
                repr_list.append('END%s' % (' ' * (self.item_size() - 3)))
            if len(repr_list) > 23:
                for repr in repr_list[:10]:
                    return_string += repr + '\n'
                return_string += '.\n.\n.\n'
                for repr in repr_list[-10:]:
                    return_string += repr + '\n'
            else:
                for repr in repr_list:
                    return_string += repr + '\n'
        return return_string[:-1]

    def __str__(self):
        '''
           x.__str__() <==> str(x)
        '''

        return_string = ''
        if self._hdr is None:
            return return_string
        if len(self.cards):
            block_size = self.block_size()
            for card in self.itercards():
                return_string += get_cardimage(card)
            return_string += 'END'
            remainder = len(return_string) % block_size
            if remainder != 0:
                return_string += ' ' * (block_size - remainder)
        return return_string

    def __iter__(self):
        '''
           x.__iter__() <==> iter(x)

           Iterate over the keywords in this header.
        '''

        if self._hdr is not None:
            return self.hdr.__iter__()
        return iter([])

    def keys(self):
        '''
           H.keys() -> a list of keywords of H
        '''

        return list(self.hdr.keys())

    def keywords(self):
        '''
           H.keywords() -> a list of keywords of H

           Synonym for keys()
        '''

        return self.keys()

    def values(self):
        '''
           H.values() -> a list of values of H
        '''

        return [card.value for card in self.cards]

    def items(self, comments=True):
        '''
           H.items() -> a list of (keyword, value, comment) or
           (keyword, value) items of H

             comments: include comments in item tuple
        '''

        if comments:
            return [(get_keyword(card), card.value, card.comment) for card in self.cards]
        else:
            return list(self.hdr.items())

    def comments(self):
        '''
           H.comments() -> a list of comments of H
        '''

        return [card.comment for card in self.cards]

    def iterkeys(self):
        '''
           H.iterkeys() -> an iterator over the keywords of H

           Synonym for __iter__()
        '''

        return self.__iter__()

    def iterkeywords(self):
        '''
           H.iterkeywords() -> an iterator over the keywords of H

           Synonym for __iter__()
        '''

        return self.__iter__()

    def itervalues(self):
        '''
           H.itervalues() -> an iterator over the values of H
        '''

        return iter(self.values())

    def iteritems(self, comments=True):
        '''
           H.iteritems() -> an iterator over the (keyword, value, comment)
           or (keyword, value) items of H

             comments: include comments in item tuple
        '''

        return iter(self.items(comments=comments))

    def itercards(self):
        '''
           H.itercards() -> an iterator over the cards in H
        '''

        return iter(get_cards(self.hdr))

    def itercomments(self):
        '''
           H.itercomments() -> an iterator over the comments of H
        '''

        return iter(self.comments())

    def get_all_headers(self):
        '''
           The sole purpose of this method is to call the factory function
           get_headers that creates a list of headers from the headers in
           the file that the current header is loaded from (self.filename).
           If the file is single-extension or the filename is not specified,
           this is a list of one header, a copy of the current header.  If
           the file is multi-extension, this is a list of one primary header
           and N extension headers, where N is the number of extensions.
        '''

        if self.filename is None:
            return [self.copy()]
        if not os.path.exists(self.filename):
            raise DARMAError('File not found: %s' % self.filename)

        return get_headers(self.filename)

#-----------------------------------------------------------------------


def getval(filename, keyword, default=None, ext=0, use_fits=False):
    '''
       Get a keyword value from an extension of a FITS image, single- or
       multi-extension.

         filename: filename to get the keyword value from
          keyword: keyword string
          default: the value to return when the keyword is missing
              ext: extension number
         use_fits: use FITS-handler's getval function instead of simple
                   Python file access method

       NOTE: The FITS-handler's methods tend to be slower for extension
             0/1 access, but may be faster for extension > 1 access.
    '''

    if use_fits:
        return fits.getval(filename, keyword, ext=ext) or default
    else:
        if ext >= 0:
            with open(filename, 'rb') as fd:
                for i in range(ext + 1):
                    blocks = b''
                    while b'END     ' not in blocks:
                        # FITS standard puts headers at the start of
                        # blocks of a fixed size.  The first character
                        # is guaranteed to be that of a keyword and must
                        # start with an upper case letter, '_', or '-'.
                        block = fd.read(2880)
                        if len(block) == 2880:
                            if block[0] in b'ABCDEFGHIJKLMNOPQRSTUVWXYZ-_':
                                blocks += block
                        else:
                            break
            for i in range(0, len(blocks), 80):
                cardstr = str(blocks[i:i + 80].decode())
                if cardstr.startswith(keyword):
                    return fromstring(cardstr).value
    return default


def get_headers(filename=None, cardlist=None):
    """The sole purpose of this factory function is to return a list of
    headers from the headers in the FITS file specified in filename or
    the ASCII file specified in cardlist.  If the FITS file is single-
    extension, this is a list of one header.  If the FITS file is multi-
    extension, this is a list of N+1 headers, where N is the number of
    extensions.  For the cardlist, the list length is equal to the
    number of END cards or 1, whichever is less.

    If both filename and cardlist are specified, the headers found in
    filename preceed those found in cardlist.

    N.B. If there are multiple headers in a cardlist, each MUST be
         ended with an END card.  If there is no END card found, it
         is assumed that there is only one header in the cardlist.

    Parameters
    ----------
    filename : str
        name of a valid FITS file, single- or multi-extension
    cardlist : list, str
        a list of header cards (80 character strings, NULL terminated),
        a list of fits.Card instances, or the name of a text file
        containing the header cards

    Returns
    -------
    list
        a list of DARMA header instances, one per header found in the
        input

    """

    headers = []
    if filename is not None:
        hdus = fits_open(filename, memmap=True)
        headers = [header(cardlist=[card for card in get_cards(hdu.header)]) for hdu in hdus]
        hdus.close()
    if cardlist is not None:
        lines = []
        if isinstance(cardlist, (str, unicode)):
            with open(cardlist) as fd:
                lines.extend([line.strip('\n') for line in fd.readlines()])
        elif isinstance(cardlist, list):
            for card in cardlist:
                if isinstance(card, (str, unicode)):
                    lines.append(card)
                elif isinstance(card, fits.Header):
                    lines.append(str(card))
                else:
                    raise DARMAError('expecting card %s to be a string or a fits.Card instance, got %s' % type(card))
        else:
            raise DARMAError('expecting cardlist argument to be a list or str, got %s' % type(cardlist))
        cardslists = []
        count = 0
        cards = []
        for line in lines:
            if not line.startswith('END'):
                cards.append(line)
            else:
                cards.append(line)
                cardslists.append(cards)
                cards = []
                count += 1
        if count == 0:
            cardslists.append(cards)
        for cards in cardslists:
            try:
                headers.append(header(cardlist=cards))
            except DARMAError as e:
                Message('failed to load header from constructed cardlist: %s' % e)

    return headers


def update_header_in_file(filename, keywords=[], values=[], comments=[], ext=0, cards=[], option='silentfix', empty=False):
    '''
       This is a utility function to update a header of a file "in place".

       When the FITS file is very large, rewriting the whole thing to update
       some header items is very inefficient.  This function updates the
       header directly in the file.  If there is appropriate space for new
       header items, this occurs with the minimum of disk I/O.

         filename: name of FITS file containing the header to update
         keywords: matched list of header keywords
           values: matched list of values
         comments: matched list of comments (optional)
              ext: extension to update
            cards: replace keywords, values, comments with a list of
                   fits.Card instances (overrides components if set)
           option: option used to verify the header (from Astropy/PyFITS)
                   should be one of fix, silentfix, ignore, warn, or
                   exception
            empty: first empty the header of any optional keywords

       NOTE: This function assumes that any existing keyword values will
             be overwritten.
    '''

    card_tuples = []
    if cards:
        for card in cards:
            card_tuples.append((get_keyword(card), card.value, card.comment))
    else:
        if not len(comments) and len(keywords):
            comments = [None] * len(keywords)
        if len(values) != len(keywords):
            raise DARMAError('Input keywords and values lists of different length!')
        if len(comments) != len(keywords):
            raise DARMAError('Input keywords and comments lists of different length!')
        for keyword, value, comment in zip(keywords, values, comments):
            card_tuples.append((keyword, value, comment))
    # Disable memmaping to avoid FS performance hit.
    with fits_open(filename, mode='update', memmap=False) as hdus:
        hdu = hdus[ext]
        hdr = hdu.header
        if empty:
            required = ['SIMPLE', 'BITPIX', 'NAXIS', 'XTENSION']
            # Create a copy of hdr.keys() because the original hdr is updated
            # in the loop itself.
            existing = [a for a in hdr.keys()]
            for key in existing:
                if key not in required and not key.startswith('NAXIS'):
                    if key in hdr:
                        del hdr[key]
        for keyword, value, comment in card_tuples:
            if keyword == '':
                hdr.add_blank(value)
            if keyword == 'COMMENT':
                hdr.add_comment(value)
            if keyword == 'HISTORY':
                hdr.add_history(value)
            else:
                update_header(hdr, keyword, value, comment)
        hdu.update_header()
        # XXX PyFITS/Astropy have a bug in Python 3 that corrupts larger FITS
        # XXX files upon writing when opened in 'update' mode and the file
        # XXX size changes.  Write a new file to work around this bug.
        hdus.writeto(filename+'.new', output_verify=option)
    os.remove(filename)
    os.rename(filename+'.new', filename)
    # XXX TODO EMH PyFits in the module NA_pyfits.py does something nasty.
    # Under certain circumstances the signal handler is redefined to
    # ignore Ctrl-C keystrokes, the next two lines mean to reset the signal
    # handler to its original state, which is omitted in PyFits.
    import signal
    signal.signal(signal.SIGINT, signal.default_int_handler)


def _is_card_length(card_string):
    '''
       str <= 80 characters
    '''

    return isinstance(card_string, (str, unicode)) and len(card_string) <= 80


def _has_equals(card_string):
    '''
       '=' in str
    '''

    return '=' in card_string


def _has_spaces(keyword_string):
    '''
       ' ' in str
    '''

    return ' ' in keyword_string


def _has_only_allowed_chars(keyword_string):
    '''
       keyword contains only 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
    '''
    allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
    for char in keyword_string:
        if char not in allowed_chars:
            return False
    return True


def _is_standard_form(card_string):
    '''
       AKEYWORD=                value / comment
       keyword is all caps, numeric, '-', or '_'
       '=' at index 8
       optional ' / ' after value followed by comment
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not _has_equals(card_string):
        msg += 'not a string containing \'=\', '
    if card_string.split('=') == 2:
        keyword, value_comment = card_string.split('=')
        if not _has_only_allowed_chars(keyword.strip()):
            msg += 'keyword contains disallowed characters, '
        compressed_value_comment = ''.join(value_comment.split())
        if compressed_value_comment == '':
            msg += 'no value (or comment) found, '
    if not ('=' in card_string and card_string.index('=') == 8):
        msg += '\'=\' not at index 8 (9th character), '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def _is_hierarch_form(card_string):
    '''
       HIERARCH keyword with spaces = value
       begins with 'HIERARCH '
       contains '=' between keyword and value
       comment ignored
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not card_string.upper().startswith('HIERARCH '):
        msg += 'does not start with \'HIERARCH \', '
    if not _has_equals(card_string):
        msg += 'not a string containing \'=\', '
    if card_string.split('=') == 2:
        keyword, value = card_string.split('=')
        compressed_keyword = ''.join(keyword.strip().split())
        if not _has_only_allowed_chars(compressed_keyword):
            msg += 'keyword contains disallowed characters, '
        if not _has_spaces(keyword):
            msg += 'keyword has no spaces, '
        compressed_value = ''.join(value.split())
        if compressed_value == '':
            msg += 'no value found, '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def _is_blank_form(card_string):
    '''
       begins with '        ' followed by anything
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not card_string.startswith('        '):
        msg += 'not enough leading spaces for a BLANK card, '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def _is_comment_form(card_string):
    '''
       begins with 'COMMENT ' followed by anything
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not card_string.upper().startswith('COMMENT '):
        msg += 'does not start with \'COMMENT \', '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def _is_history_form(card_string):
    '''
       begins with 'HISTORY ' followed by anything
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not card_string.upper().startswith('HISTORY '):
        msg += 'does not start with \'HISTORY \', '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def _is_continue_form(card_string):
    '''
       begins with 'CONTINUE ' followed by anything
    '''
    msg = ''
    if not _is_card_length(card_string):
        msg += 'not a string of length <= 80 characters, '
    if not card_string.upper().startswith('CONTINUE '):
        msg += 'does not start with \'CONTINUE \', '
    msg = msg[:-2]
    if msg:
        return False, msg
    return True, msg


def fromstring(cardstring, verify='silentfix'):
    '''
       Return a new card from a <=80 character card string:

       "KEYWORD =           'value   ' / standard FITS card comment    "
       "HIERAERCH ESO card = 'value'                                   "
       "        blank card                                             "
       "COMMENT card                                                   "
       "HISTORY card                                                   "
       "CONTINUE 'card'                                                "

       A standard card has the form of no more than 8 capital letters,
       numbers, or underscores, a padding of spaces, = at the 9th column,
       a space followed by a value, a ' / ', then the comment.  A
       standard card string will have exactly 80 columns (padded by the
       parser if necessary).  Other types of cards are shown above below
       the standard card.

       Astonishingly, no version of either PyFITS or Astropy raises an
       exception upon parsing the cardstring or verifying the resultant
       card with option 'exception' when not following one of these
       forms!  At best, a warning is given.  Therefore, this function
       attempts to determine poor formatting and raises an exception
       when the cardstring does not match the criteria for any known card
       format.
    '''

    # valid cards have:
    # 1. '=' at index 8 or          # standard KEYWORD card
    std, stdmsg = _is_standard_form(cardstring)
    # 2. begin with 'HIERARCH ' or  # HIERARCH keyword card
    hei, heimsg = _is_hierarch_form(cardstring)
    # 3. begin with '        ' or   # BLANK card
    bla, blamsg = _is_blank_form(cardstring)
    # 4. begin with 'COMMENT ' or   # COMMENT card
    com, commsg = _is_comment_form(cardstring)
    # 5. begin with 'HISTORY ' or   # HISTORY card
    his, hismsg = _is_history_form(cardstring)
    # 6. begin with 'CONTINUE'      # CONTINUE card
    con, conmsg = _is_continue_form(cardstring)
    if not (std or hei or bla or com or his or con):
        msglist = [stdmsg, heimsg, blamsg, commsg, hismsg, conmsg]
        msglist = [msg for msg in msglist if msg]
        raise DARMAError('ERROR -- Incorrectly formatted cardstring (%s): %s' % (cardstring, ', '.join(msglist)))
    card = fits.Card().fromstring(cardstring)
    card.verify(option=verify)

    return card
