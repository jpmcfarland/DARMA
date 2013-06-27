'''Implements the table object with methods to manipulate a FITS table.
'''

__version__ = '@(#)$Revision$'

import pyfits, math, os

from common import Array
from common import DARMAError, _HAS_NUMPY, pyfits_open
from header import header

datatypes = {
             'ascii'  : pyfits.TableHDU,
             'binary' : pyfits.BinTableHDU,
            }

fits_format = {
               'bool'       : 'L',
               'int16'      : 'I',
               'int32'      : 'J',
               'int64'      : 'K',
               'string8'    : 'A',
               'float32'    : 'E',
               'float64'    : 'D',
               'complex64'  : 'C',
               'complex128' : 'M',
              }

class columns(object):

    '''
       A container object housing a list of columns, a table.
    '''

    def __init__(self, filename=None, name=None, datatype='binary',
                 readonly=1, memmap=0):

        '''
              filename: The name of a FITS file
                  name: Name of the table to be loaded from filename
              datatype: Type of table: binary or ASCII
              readonly: Indicate that the FITS file is readonly
                memmap: use memory mapping for data access (using
                        memmapping currently does nt work properly)

           NOTE: When reading in columns, the datatype option makes no
                 difference.  When creating new columns, it determines
                 the datatype of the output FITS file.
        '''

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError, 'DARMA table functionality not possible: cannot import module numpy'

        self.filename   = filename
        self._name      = name
        self.datatype   = datatype
        self.readonly   = readonly
        self.memmap     = memmap
        self.table      = None

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError, 'Filename: %s not found!' % self.filename

    def load(self):

        '''
           Proxy for load_columns()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        return self.load_columns()

    def load_columns(self):

        '''
           Load a list of columns (a table) from the given filename.  If there
           is no filename, table is set to None.
        '''

        if self.table is None:
            if self.filename is not None:
                try:
                    self.hdus = pyfits_open(self.filename, memmap=self.memmap)
                    self.table = self.hdus[self._name]
                    self.header = header(card_list=self.table.header.ascardlist())
                except Exception, e:
                    raise DARMAError, 'Error loading table from %s: %s' % (self.filename, e)
            for name in self.names:
                if not hasattr(self, name):
                    setattr(self, name, name)

    def __getattribute__(self, name):

        '''
           x.__getattribute__('name') <==> x.name

           For a column name, this returns the data of one column if
           that column's name requested.
        '''

        if object.__getattribute__(self, name) in [name, name.replace('_', ' ')]:
            return self.table.data.field(name)
        else:
            return object.__getattribute__(self, name)

    def __getitem__(self, name):

        '''
           x.__getitem__(y) <==> x[y]

           For a column name, return the data stored in the column
           named name.
        '''

        if self.table is not None:
            attrname = name.replace(' ', '_')
            if name in self.names:
                return getattr(self, attrname)

    def __setattr__(self, name, value):

        '''
           x.__setattr__('name', value) <==> x.name = value

           For a column name, this sets the data of one column if
           that column's name requested.
        '''
        attrname = name.replace(' ', '_')
        if hasattr(self, attrname) and object.__getattribute__(self, attrname) == name:
            self.table.data.field(name)[:] = value
            self.table.update()
        else:
            object.__setattr__(self, attrname, value)

    def __setitem__(self, name, value):

        '''
           x.__setitem__(y) <==> x[y]

           For a column name, set the data in the column named name.
        '''

        if self.table is not None:
            attrname = name.replace(' ', '_')
            if hasattr(self, attrname):
                self.__setattr__(attrname, value)
            else:
                self.table.column.add_col(pyfits.Column(name, fits_format[value.dtype.name], array=value))
                setattr(self, attrname, name)

    def __delattr__(self, name):

        '''
           x.__delattr__('name') <==> del x.name

           For a column name, delete the data in the column named name.
        '''

        if self.table is not None and name in self.names:
            self.table.columns.del_col(name)
            self.table.update()
        object.__delattr__(self, name)

    def __delitem__(self, name):

        '''
           x.__delitem__(y) <==> x[y]

           For a column name, delete the data in the column named name.
        '''

        if self.table is not None:
            if hasattr(self, name):
                if name in self.names:
                    self.table.columns.del_col(name)
                delattr(self, name)

    def __del__(self):

        '''
           x.__del__() <==> del(x)

           Remove the table and close the HDUList.
        '''

        if self.table is not None:
            if hasattr(self.table, 'data'):
                del self.table.data
        self.table = None
        self.hdus.close()

    def _get_names(self):

        '''
           List of names of columns in the table.

           getter function
        '''

        if not self.table:
            self.load()
        if not self.table:
            return []
        return self.table.columns.names

    names = property(_get_names, None, None, 'List of names of columns in the table.')

    def _get_name(self):

        '''
           Name of the table holding the columns.

           getter function
        '''

        if not self.table:
            self.load()
        if self.table is not None:
            return self.table.name
        return ''

    def _set_name(self, value):

        '''
           Name of the table holding the columns.

           setter function
        '''

        if not self.table:
            self.load()
        self.table.name = value
        self.table.update()
        self.header['EXTNAME'] = self.table.header.get('EXTNAME')

    name = property(_get_name, _set_name, None, 'Name of the table holding the columns.')

    def info(self):

        '''
           Display helpful info about the columns.
        '''

        print 'Table "%s" holds the following columns:' % self.table.name
        cols = self.table.columns
        print '%30s %10s %10s' % ('Name', 'Format', 'Unit')
        print '-'*52
        for name, format, unit in zip(cols.names, cols.formats, cols.units):
            print '%30s %10s %10s' % (name, format, unit)

    def __repr__(self):

        '''
           x.__repr__() <==> repr(x)

           Print the list of column names.
        '''

        return '%s' % self.names

    def __str__(self):

        '''
           x.__str__() <==> str(x)

           Print the list of column names.
        '''

        return '%s' % self.names

    def __contains__(self, name):

        '''
           x.__contains__(y) <==> y in x

           Column name list of columns.
        '''

        return name in self.names

    def __iter__(self):

        '''
           x.__iter__() <==> iter(x)

           Iterate over column names.
        '''

        return iter(self.table.columns.names)

class tables(list):

    '''
    '''

    def __init__(self, filename=None, table_ids=[], indexes=[],
                 datatype='binary', readonly=1, memmap=0):

        '''
             filename: The name of a FITS file
            table_ids: Optional list of table names to load
              indexes: Optional list of table indexes to load (ignored if
                       table_ids is defined)
             datatype: Type of table: binary or ASCII
             readonly: Indicate that the FITS file is readonly
               memmap: use memory mapping for data access (using
                       memmapping currently does nt work properly)

           NOTE: When reading in tables, the datatype option makes no
                 difference.  When creating new tables, it determines
                 the datatype of the output FITS file.
        '''

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError, 'DARMA table functionality not possible: cannot import module numpy'

        self.filename  = filename
        self.table_ids = table_ids
        self.indexes   = indexes
        self.datatype  = datatype
        self.readonly  = readonly
        self.memmap    = memmap
        self._tables   = []
        self._names    = []
        self._dict     = {}

        if self.filename is not None:
            if not os.path.exists(self.filename):
                raise DARMAError, 'Filename: %s not found!' % self.filename

    def load(self):

        '''
           Proxy for load_tables()

           THIS SHOULD ONLY BE CALLED BY THE 'getter' METHOD.
        '''

        return self.load_tables()

    def load_tables(self):

        '''
           Load a list of tables from the given filename.  If there
           is no filename, tables is set to None.
        '''

        if self._tables == []:
            if self.filename is not None:
                try:
                    hdus = pyfits_open(self.filename, memmap=self.memmap)
                    if self.table_ids:
                        hdu_names = [hdu.name for hdu in hdus][1:]
                        table_names = [id for id in self.table_ids if id in hdu_names]
                    elif self.indexes:
                        hdu_indexes = range(1, len(hdus))
                        table_names = [hdus[idx].name for idx in self.indexes if idx in hdu_indexes]
                    else:
                        table_names = [hdu.name for hdu in hdus][1:]
                    self._tables = []
                    for table_name in table_names:
                        cols = columns(filename=self.filename,
                                       name=table_name,
                                       datatype=self.datatype,
                                       readonly=self.readonly,
                                       memmap=self.memmap)
                        self._tables.append(cols)
                    hdus.close()
                except Exception, e:
                    raise DARMAError, 'Error loading tables from %s: %s' % (self.filename, e)

            self._names = [cols.name for cols in self._tables]

            for cols in self._tables:
                self._dict[cols.name] = cols
                attrname = cols.name.replace(' ', '_')
                if not hasattr(self, attrname):
                    setattr(self, attrname, cols)

    def _get_tables(self):

        '''
        '''

        if self._tables == []:
            self.load()
        return self._tables

    def _set_tables(self, value):

        '''
        '''

        if type(value) == list:
            for val in value:
                if type(val) != columns:
                    raise DARMAError, 'Cannot set tables to object of type: %s' % type(val)
            self._tables = value
        else:
            raise DARMAError, 'Cannot set tables to object of type: %s' % type(value)

    def _del_tables(self):

        '''
        '''

        self._tables = []

    tables = property(_get_tables, _set_tables, _del_tables)

    def _get_names(self):

        '''
        '''

        if self._tables == []:
            self.load()
        return self._names

    def _set_names(self, value):

        '''
        '''

        self._names = value

    def _del_names(self):

        '''
        '''

        self._names = []

    names = property(_get_names, _set_names, _del_names)

    def __getitem__(self, name):

        '''
        '''

        if name in self.names:
            return self._dict[name]
        elif type(name) == int:
            return self._dict[self.names[name]]
        else:
            return None

    def __setitem__(self, name, value):

        '''
        '''

        if name not in self.names:
            self.names.append(name)
        self._dict[name] = value
        attrname = name.replace(' ', '_')
        if not hasattr(self, attrname):
            setattr(self, attrname, value)

    def __delitem__(self, name):

        '''
        '''

        if name in self.names:
            name = self.names.pop(self.names.index(name))
        else:
            name = self.names.pop(name)
        del self._dict[name]
        if hasattr(self, name):
            delattr(self, name)

    def __delattr__(self, name):

        '''
        '''

        if name in self.names:
            name = self.names.pop(self.names.index(name))
            del self._dict[name]
        list.__delattr__(self, name)

    def __repr__(self):

        '''
        '''

        return '%s' % self.names

    def __str__(self):

        '''
        '''

        return '%s' % self.names

    def __contains__(self, name):

        '''
        '''

        return name in self.names

    def __iter__(self):

        '''
           x.__iter__() <==> iter(x)

           Iterate over column names.
        '''

        return iter(self.names)

    def info(self):

        '''
        '''

        n = 0
        print ' %s\t%20s\t%15s\t%12s' % ('No.', 'Name', 'Type', 'Shape')
        for name in self.names:
            print ' % 2d\t%20s\t%15s\t%12s' % (n, name, self._dict[name].__class__.__name__, self._dict[name].shape())
            n += 1

    def __del__(self):

        '''
           Make sure all the HDUs are closed properly.
        '''

        for name in self.names:
            delattr(self, name)

