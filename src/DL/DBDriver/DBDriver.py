#!/usr/bin/python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
# DBDriver.py
#
# Author      : Peter Heijligers
# Description : SQLite driver
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2017-09-18 PHe First creation
# 2022-08-14 PHe Revision, python 2.7 -> 3.10
# ---------------------------------------------------------------------------------------------------------------------
import csv
import sqlite3 as lite
import sys

from .Audit import *
from .Const import *
from .Enums import *
from .Functions import *


# noinspection SqlInjection
class DBDriver(object):

    def __init__(self, db_path):
        if not db_path:
            self._raise(f'DB path is required.')

        self._db_path = db_path
        if not db_path.endswith('.db'):
            db_path = f'{db_path}.db'
        self._con_name = os.path.basename(db_path)
        self._db_name, file_extension = os.path.splitext(self._con_name)
        self._con = None
        self._cur = None
        self._transaction_mode = True

        self._table_defs = {}
        self._cache = {}
        self._current_table_name = None
        self._index = 0

        self._FFD_FFD = {
            1: Att(FF_TableName),
            2: Att(FF_AttName),
            3: Att(FF_AttType),
            4: Att(FF_AttLength, type=AttType.Int),
            5: Att(FF_Derived, type=AttType.Bool)
        }
        self._audit = Audit()
        self._db_connect()
        self._set_ffd_table_def()

    # DB connect

    def _db_connect(self, memory=False):
        try:
            self._con = lite.connect(MEMORY if memory else self._db_path, isolation_level='DEFERRED')
            self._con.text_factory = str
            self._cur = self._con.cursor()
            self._con.execute('PRAGMA journal_mode = WAL')
        except OSError as e:
            self._raise(f'DB could not be created in: "{self._db_path}". Reason: {e}')

    def _set_ffd_table_def(self):
        """
        1. Create table FFD if it does not exist
        2. Add FFD table definition - without audit data - in memory (needed for CRUD on FFD)
        """
        if not self.file_exists(FFD):
            self.create_table(FFD, table_def=self._FFD_FFD, audit=AUDIT_CREATION_PRIVATE)
        self._table_defs[FFD] = self._FFD_FFD

    def _get_ffd_table_def(self, table_name) -> dict:
        # Retrieve table definition from FFD table.
        # Store definition, as a dictionary, in dictionary "table_name".
        #
        # rows example:
        # Id Table_name Att_Name    Att_Type
        # -- ---------- ----------- --------
        # 34 Companies  Name        TEXT
        # 35 Companies  Description TEXT
        #
        if not table_name:
            return {}
        sql_stmt = f'SELECT * FROM {FFD} WHERE {FFD_TableName}={quote(table_name)}'
        try:
            with self._con:
                rows = []
                self._cur.execute(sql_stmt)
                while True:
                    row = self._cur.fetchone()
                    if not row:
                        break
                    rows.append(row)
                rows = self._tuples_to_list(rows, FetchMode.Set)
            # In case of a specified definition (e.g. imported file) the FFD definition does not need to exist.
            # The FFD however must exist.
            if not rows:
                if table_name == FFD:
                    self._raise(f'Table {table_name} definition not found in {FFD} table', 'set_current_table')
                else:
                    return {}
            i = 1
            table_def = {}
            for row in rows:
                table_def[i] = Att(
                    name=row[2],
                    type=row[3],
                    length=row[4],
                    derived=row[5])
                i += 1
            return table_def

        except Exception as e:
            self._raise(f'{sql_stmt} {e.args[0]}', 'set_current_table')

    # Validate

    def test_ffd(self):
        """ Create FFD if it has been dropped, used in unit test """
        self._set_ffd_table_def()

    def file_exists(self, table_name) -> bool:
        """
        Does physical file exist?
        """
        if not table_name:
            return True
        description = self.get_table_description(table_name, check_only=True)
        return True if description else False

    def get_table_description(self, table_name, check_only=False) -> list:
        if not table_name:
            return []
        sql_stmt = f'SELECT * FROM {table_name}'
        try:
            with self._con:
                data = self._cur.execute(sql_stmt)
                return data.description
        except Exception as e:
            self._rollback()
            if not check_only:
                self._raise(f'{sql_stmt}. {e.args[0]}', 'get_table_description')
            return []

    def get_schema_att_names(self, table_name):
        return [n[0] for n in self.get_table_description(table_name, check_only=True)]

    def list_table_names(self) -> list:
        self._execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [table[0] for table in self._cur]

    # Cache

    def _cache_table(self, table_name, table_def=None, audit_type=None):
        """
        Should be called after every CRUD action, also for non-model files.
        table_def: is used only for create and csv-import
        audit_type: is used only for csv-import.
        """
        self._current_table_name = table_name

        # a. If hardcoded table_def specified (create table), always replace row-def.
        force_cache = False
        if table_def:
            # Re-order
            self._index = 0
            self._table_defs[table_name] = {
                self._add_index(): att for _, att in table_def.items() if att.in_db is True
            }
            force_cache = True
        # b. Get table_def from FFD.
        elif table_name not in self._table_defs:
            self._table_defs[table_name] = self._get_ffd_table_def(table_name)
            force_cache = True

        # Return if cached already.
        if table_name in self._cache and not force_cache:
            return

        # Populate the cache.
        self._cache[table_name] = {
            COL_NAMES: [], COL_TYPES: [], COL_LENGTHS: [], COL_DERIVEDS: [], COL_SANITIZABLES: [], COL_AUDIT_NAMES: []}
        for col_no, col in self._table_defs[table_name].items():
            col_type = col.type.upper()
            self._cache[table_name][COL_NAMES].append(col.name.title())
            self._cache[table_name][COL_TYPES].append(col_type)
            self._cache[table_name][COL_LENGTHS].append(str(col.length))
            self._cache[table_name][COL_DERIVEDS].append(col.derived)
            if col_type in AttType.sanitize_types:
                self._cache[table_name][COL_SANITIZABLES].append(col_no - 1)  # 0-based

        # Retrieve audit names from schema (except when creating a table via importing a csv)
        # NB. file may not exist yet. In that case if no definition too, no audit data.
        schema_names = self.get_schema_att_names(table_name)
        audit_names = get_audit_names_from_schema_names(schema_names) \
            if not audit_type else AUDIT_DEF.get(audit_type, [])
        self._cache[table_name][COL_AUDIT_NAMES] = audit_names

    def _add_index(self):
        self._index += 1
        return self._index

    def _cached_list(self, name):
        return self._cache[self._current_table_name][name]

    def _cached_item(self, name, item):
        return self._cache[self._current_table_name][name][item]

    # Physical table

    def create_table(self, table_name, table_def, **kwargs):
        """
        Create a table (and its FFD definition)
        1. Check new definition.
        2. Create new table.
        """
        if not table_name or not table_def:
            return
        pgm = kwargs.get(PGM) or __name__

        method = 'create_table'

        # if table already exists, skip.
        if self.file_exists(table_name):
            if table_name not in self._table_defs:
                # (set the definitions if they do not exist yet)
                self._cache_table(table_name, table_def)
            return

        # 1. Validate table definition
        self._validate_table_def(table_name, table_def)

        # 2. Set cache to target table
        self._cache_table(table_name, table_def, audit_type=kwargs.get(AUDIT, AUDIT_ALL))

        # 3. Create new table
        sql_stmt = self._get_create_table_stmt(table_name, table_def)

        try:
            # a. Create table
            self._execute(sql_stmt)
            # b. Add table definition to FFD (except if it is FFD ;-)
            if table_name != FFD:
                # - Set cache to FFD
                self._cache_table(FFD)
                for att_no, att in table_def.items():
                    sql_stmt = self._get_insert_stmt(
                        FFD,
                        [table_name,
                         att.name,
                         att.type,
                         att.length,
                         att.derived],
                        pgm=pgm
                    )
                    self._execute(sql_stmt)
        except (IOError, DBException) as e:
            self._raise(f'{sql_stmt}. {e.args[0]}', method)

        # 4. Reset cache from FFD to target table
        self._cache_table(table_name, table_def)

        # 5. Create indexes
        ix_dict = kwargs.get(INDEX_DEF) or {}
        for ix_name, ix_keys in ix_dict.items():
            self.add_index(table_name, ix_name, ix_keys)

    def _validate_table_def(self, table_name, table_def: dict):
        for att_no, att in table_def.items():
            if not isinstance(att, Att):
                self._raise(
                    f'Attribute is not an instance of Attribute. Table_name={table_name}', '_validate_table_def')
            if not hasattr(AttType, att.type.title()):
                self._raise(f'Invalid attribute type {att.type}. Table_name={table_name}', '_validate_table_def')

    def _get_create_table_stmt(self, table_name, table_def) -> str:
        sql_stmt = f'CREATE TABLE {table_name} ({ID} INTEGER PRIMARY KEY'
        # Append audit attributes
        table_def = self._audit.add_audit_def(self._cached_list(COL_AUDIT_NAMES), table_def)
        # Attributes to SQL values
        for att_no, att in table_def.items():
            if att_no == 0 and att.name == ID:
                continue
            att_length = f'({str(att.length)})' if att.length > 0 else EMPTY
            sql_stmt = f'{sql_stmt}, {att.name} {att.type}{att_length}'
        # Close
        sql_stmt = f'{sql_stmt})'
        return sql_stmt

    def drop_table(self, table_name):
        if not table_name:
            return
        method = 'drop_table'

        if not self.file_exists(table_name):
            return

        sql_stmt = f'DROP TABLE {table_name}'
        try:
            # Delete table
            self._execute(sql_stmt)
            # Delete table definition from FFD (except when FFD itself has been dropped ;-)
            if table_name != FFD:
                self._execute(f'DELETE FROM {FFD} WHERE TableName="{table_name}"')
            # Delete table definition from memory
            self._table_defs.pop(table_name, EMPTY)
            self._cache.pop(table_name, EMPTY)
        except (IOError, DBException) as e:
            self._raise(f'{sql_stmt}. {e.args[0]}', method)

    def add_index(self, table_name, index_name, keys, unique=False):
        if not table_name or not index_name:
            return
        unq = 'UNIQUE ' if unique else EMPTY
        sql_stmt = f'CREATE {unq} INDEX IF NOT EXISTS {index_name} ON {table_name} ({", ".join(keys)})'
        self._execute(sql_stmt)

    def drop_index(self, index_name):
        if not index_name:
            return
        sql_stmt = f'DROP INDEX IF EXISTS {index_name}'
        self._execute(sql_stmt)

    # Audit

    def get_audit_type(self, table_name):
        return get_audit_type_from_schema(self.get_schema_att_names(table_name))

    @staticmethod
    def _get_audit_values(mode, **kwargs) -> list:
        pgm = kwargs.get(PGM) or __name__
        many = kwargs.get(MANY) or False
        if mode == TransactionMode.U:
            return [quote(ZERO), quote(EMPTY), quote(EMPTY),
                    quote(datetime.datetime.now().isoformat()), quote(pgm), quote(getpass.getuser())]
        elif mode == TransactionMode.C:
            if many:
                return ["?", "?", "?", "?", "?", "?"]
            else:
                return [quote(datetime.datetime.now().isoformat()), quote(pgm), quote(getpass.getuser()),
                        quote(ZERO), quote(EMPTY), quote(EMPTY)]

    def _add_derived_defaults(self, rows) -> list:
        """ Insert many """
        rows_out = []
        extension = []

        # Derived values: defaults at the end of the row
        for i in range(len(self._cached_list(COL_TYPES))):
            if self._cached_item(COL_DERIVEDS, i) in (True, TRUE):  # True
                if self._cached_item(COL_TYPES, i) == AttType.Bool:
                    extension.append(False)
                elif self._cached_item(COL_TYPES, i) in AttType.numeric_types:
                    extension.append(ZERO)
                else:
                    extension.append(EMPTY)

        if not extension:
            return rows
        for row in rows:
            row.extend(extension)
            rows_out.append(row)
        return rows_out

    # C - Create

    def insert(self, table_name, row, **kwargs) -> int:
        if not table_name or not row:
            return 0

        self._cache_table(table_name)

        sql_stmt = self._get_insert_stmt(table_name, row, **kwargs)
        self._execute(sql_stmt)

        # Return the Id
        return self._cur.lastrowid

    def _get_insert_stmt(self, table_name, row, **kwargs) -> str:
        expected_count = len(self._cache[self._current_table_name][COL_NAMES])
        if len(row) != expected_count:
            self._raise(f'Row size is {len(row)}, but expected is {expected_count}.')
        has_id = kwargs.get(HAS_ID) is True
        many = kwargs.get(MANY) is True
        pgm = kwargs.get(PGM) or __name__

        method = 'get_insert_stmt'
        # Attribute names
        id_text = f'{ID}, ' if has_id else EMPTY
        sql_stmt = f'INSERT INTO {table_name} ({id_text}{", ".join(self._cached_list(COL_NAMES))}'
        audit_names = self._cached_list(COL_AUDIT_NAMES)
        audit_clause = f', {", ".join(audit_names)}' if audit_names else EMPTY
        sql_stmt = f'{sql_stmt}{audit_clause}) VALUES('

        # Attribute values
        sql_values = []
        try:
            j = 0  # Col index
            row = self._sanitize_row(row)
            for i in range(len(row)):
                value = row[i]

                # During an import, row may contain an Id.
                is_ID = False
                if i == 0 and has_id:
                    is_ID = True

                if many:
                    new_value = value  # ?
                elif self._cached_item(COL_TYPES, j) == AttType.Bool:
                    new_value = DB_TRUE if value in (True, '1') else DB_FALSE
                elif is_ID or self._cached_item(COL_TYPES, j) in AttType.numeric_types:
                    new_value = str(value) if value else ZERO
                else:
                    new_value = quote(value)

                if not is_ID:
                    j += 1
                # Add the new value
                sql_values.append(f'{quote_none(new_value)}')

            # Audit values
            audit_values = self._audit.get_audit_values(audit_names, many=many, pgm=pgm)
            for a in audit_values:
                sql_values.append(f'{quote_none(a)}')

            # Attribute values - all
            sql_stmt = f'{sql_stmt}{", ".join(sql_values)})'

        except IndexError as e:
            self._raise(f'{sql_stmt}. Values:"{", ".join(sql_values)}" {e.args[0]}', method)
        return sql_stmt

    def check_then_insert(self, table_name, row, **kwargs) -> int:
        if not table_name or not row:
            return 0
        Id = self.fetch_id(table_name, **kwargs)
        return self.insert(table_name, row, **kwargs) if Id == 0 else Id

    def updert(self, table_name, atts, **kwargs) -> int:
        if not table_name or not atts:
            return 0

        pgm = kwargs[PGM] or __name__
        row = self.fetch_one(table_name, **kwargs)

        # Insert
        if not row:
            return self.insert(table_name, [att.value for att in atts], pgm=pgm)

        # Update
        # - Check if any value is unequal.
        if self._is_row_changed(row, atts):
            self.update(table_name, [Att(att.name, value=att.value) for att in atts], **kwargs)
        return row[0]

    def _is_row_changed(self, row, atts):
        return any(
            str(sanitize_text(att.value) if att.type in AttType.sanitize_types else att.value)
            != str(row[self._db_colno_from_cache(att.name)])
            for att in atts
        )

    def insert_many(self, table_name, rows, **kwargs) -> bool:
        if not table_name or not rows:
            return True

        method = 'insert_many'
        self._cache_table(table_name)

        # Sanitize rows
        sanitized_rows = rows if len(self._cached_list(COL_SANITIZABLES)) == 0 \
            else [self._sanitize_row(row) for row in rows]

        if not self._cached_list(COL_NAMES):
            return True

        kwargs[MANY] = True

        # Statement
        row = ['?' for _ in self._cached_list(COL_NAMES)]
        if kwargs.get(HAS_ID) is True:
            row.append('?')

        sql_stmt = self._get_insert_stmt(table_name, row, **kwargs)

        # Execute
        try:
            audit_names = self._cached_list(COL_AUDIT_NAMES)
            rows = self._add_derived_defaults(sanitized_rows)
            pgm = kwargs.get(PGM, __name__)
            rows = self._audit.add_audit_values(audit_names, rows, pgm)
            self._cur.executemany(sql_stmt, rows)
            self._commit()
        except Exception as e:
            self._con.rollback()
            self._raise(f'{sql_stmt}. {e.args[0]}', method)
        return True

    # R - Read

    def fetch(self, table_name, **kwargs) -> list:
        if not table_name:
            return []

        self._cache_table(table_name)

        # Defaults
        if not kwargs.get(MODE):
            kwargs[MODE] = FetchMode.Set

        mode = kwargs[MODE]
        where = self._get_where_clause(**kwargs)
        order_by = self._get_order_by_clause(kwargs.get('order_by'))
        sql_stmt = f'SELECT * FROM {table_name}{where}{order_by}'

        rows = []

        try:
            with self._con:
                self._cur.execute(sql_stmt)
                if mode == FetchMode.WholeTable:
                    rows = self._cur.fetchall()
                else:
                    while True:
                        row = self._cur.fetchone()
                        if row is None:
                            break
                        rows.append(row)
                        if mode == FetchMode.First:
                            break
        except Exception as e:
            self._raise(f'{sql_stmt}. {e.args[0]}', 'fetch')
        return self._tuples_to_list(rows, mode)

    def fetch_id(self, table_name, **kwargs) -> int:
        if not table_name:
            return 0
        row = self.fetch_one(table_name, **kwargs)
        return row[0] if row else 0

    def fetch_one(self, table_name, **kwargs) -> list:
        if not table_name:
            return []
        self._check_kwargs(['where'], **kwargs)

        # Check for duplicates
        if kwargs.get('strict') is True:
            kwargs[MODE] = FetchMode.Set
            row = self.fetch(table_name, **kwargs)
            if len(row) > 1:
                self._raise('Multiple rows found in strict mode', 'fetch_one')

        kwargs[MODE] = FetchMode.First
        return self.fetch(table_name, **kwargs)

    def fetch_value(self, table_name, **kwargs) -> str or None:
        """ Use select which supports filtering rows too """
        if not table_name:
            return None
        self._check_kwargs([NAME], **kwargs)
        kwargs[MODE] = FetchMode.First
        values = self.select(table_name, **kwargs)
        return values[0] if values else None

    def fetch_values(self, table_name, **kwargs) -> list:
        """ Use select which supports filtering rows too """
        if not table_name:
            return []
        self._check_kwargs([NAMES], **kwargs)
        kwargs[MODE] = FetchMode.First
        return self.select(table_name, **kwargs)

    def fetch_max(self, table_name, name, **kwargs) -> int or None:
        if not table_name or not name or not self.file_exists(table_name):
            return None
        return self._fetch_calc(f'SELECT MAX({name}) FROM ', table_name, **kwargs)

    def fetch_min(self, table_name, name, **kwargs) -> int or None:
        if not table_name or not name or not self.file_exists(table_name):
            return None
        return self._fetch_calc(f'SELECT MIN({name}) FROM ', table_name, **kwargs)

    def count(self, table_name, **kwargs) -> int:
        if not table_name or not self.file_exists(table_name):
            return 0
        self._cache_table(table_name)
        return self._fetch_calc(f'SELECT COUNT(*) FROM ', table_name, **kwargs)

    def _fetch_calc(self, prefix, table_name, **kwargs):
        where = self._get_where_clause(**kwargs)
        sql_stmt = f'{prefix}{str(table_name)}{str(where)}'
        try:
            with self._con:
                self._cur.execute(sql_stmt)
                counted = self._cur.fetchone()
                return counted[0]
        except Exception as e:
            self._raise(f'{sql_stmt}. {e.args[0]}', 'fetch_calc')

    def select(self, table_name, **kwargs) -> list:
        """
        Get one or more columns or cells from a file.
        Or, if not "name" or "names" is specified, it is a normal fetch.

        Mode "Set" (default):
            A. If "name" specified, return 1 column as a list of strings.
            B. If "names" specified, return n columns as a list of lists.

        Mode "First":
            C. If "name" specified, return 1 cell as a list.
            D. If "names" specified, return n cells as a list.

        Example A - Only column 2:  ['myRow1Col2', 'myRow2Col2',...]
        Example B - Column 2 and 4: [['myRow1Col2', 'myRow1Col4'], ['myRow2Col2', 'myRow2Col4'],...]
        Example C - Only cell 2:  ['myRow1Col2']
        Example D - Cell 2 and 4: ['myRow1Col2', 'myRow1Col4']
        """
        if not table_name:
            return []
        # Validate
        names = kwargs.pop(NAMES, EMPTY)
        name = kwargs.pop(NAME, EMPTY)

        mode = kwargs.get(MODE) or FetchMode.Set

        if names:
            if mode == FetchMode.First:
                row = self.fetch_one(table_name, **kwargs)
                out_rows = [self._get_value_from_db_row(att_name, row) for att_name in names]
            else:
                rows = self.fetch(table_name, **kwargs)
                out_rows = [[self._get_value_from_db_row(att_name, row) for att_name in names] if names
                            else self._get_value_from_db_row(name, row) for row in rows]
        elif name:
            if mode == FetchMode.First:
                row = self.fetch_one(table_name, **kwargs)
                out_rows = [self._get_value_from_db_row(name, row)]
            else:
                rows = self.fetch(table_name, **kwargs)
                out_rows = [self._get_value_from_db_row(name, row) for row in rows]
        else:
            if mode == FetchMode.First:
                out_rows = [self.fetch_one(table_name, **kwargs)]
            else:
                out_rows = self.fetch(table_name, **kwargs)

        return out_rows

    def _get_value_from_db_row(self, att_name, db_row):
        """ DB-row has an Id and may be shorter than model-row when it has "in_db=False" attributes. """
        if not db_row:
            return None
        if att_name == ID:
            return db_row[0]
        else:
            c = self._db_colno_from_cache(att_name)
            return db_row[c] if c else None

    def _db_colno_from_cache(self, att_name) -> int or None:
        """ 1-based """
        for col_number, att in self._table_defs[self._current_table_name].items():
            if att.name == att_name:
                return int(col_number)
        self._raise(
            f'Table "{self._current_table_name}" attribute "{att_name}" not found in cache.', '_colno_from_cache')

    # U - Update

    def update(self, table_name, values: list, **kwargs) -> bool:
        if not table_name or not values:
            return False

        self._cache_table(table_name)

        for att in values:
            if att.name.title() not in self._cached_list(COL_NAMES):
                self._raise(f'"{att.name}" is not a column in {table_name}', 'update')

        mutMode = TransactionMode.U
        att_clause = EMPTY
        first = True
        for att in values:
            if first:
                first = False
            else:
                att_clause = f'{att_clause}, '

            att_type = self._get_attribute_type(att.name)
            if att_type == AttType.Int:
                att.value = str(att.value)

            # Sanitize
            elif att_type in AttType.sanitize_types:
                att.value = sanitize_text(att.value)

            att_clause = f'{att_clause}{att.name}={quote(att.value)}'

        # Add audit data
        audit_names = self._cached_list(COL_AUDIT_NAMES)
        pgm = kwargs.get(PGM) or __name__
        for att in self._audit.get_audit_atts(audit_names, mutMode, pgm):
            if not att.value == NC:
                att_clause = f'{att_clause}, {att.name}={quote(att.value)}'

        where = self._get_where_clause(**kwargs)
        sql_stmt = f'UPDATE {str(table_name)} SET {str(att_clause)}{str(where)}'
        self._execute(sql_stmt)
        return True

    # D - Delete

    def delete(self, table_name, **kwargs) -> int:
        if not table_name:
            return 0

        count_B = self.count(table_name)
        count_A = count_B  # After
        if count_B > 0:
            if not kwargs.get(WHERE):
                kwargs[INCLUDE_DELETED] = True
            where = self._get_where_clause(**kwargs)
            self._execute(f'DELETE FROM {table_name}{where}')
            count_A = self.count(table_name)
        return count_B - count_A

    def clear(self, table_name) -> int:
        count_B = self.count(table_name)
        if not table_name:
            return False
        self._execute(f'DELETE FROM {table_name}')
        count_A = self.count(table_name)
        return count_B - count_A

    def reclaim_resources(self):
        self._execute(f'VACUUM')

    # General

    def set_transaction(self, mode: bool):
        """ For bulk inserts the transaction mode may be temporary turned off """
        try:
            # Set transaction mode ON
            if mode is True:
                self._con.execute('PRAGMA synchronous = FULL')
                self._con.execute('PRAGMA journal_mode = ON')
            # Set transaction mode OFF
            elif mode is False:
                self._con.execute('PRAGMA synchronous = OFF')
                self._con.execute('PRAGMA journal_mode = OFF')
            self._transaction_mode = mode
        except Exception as e:
            self._raise(f'{e.args[0]}', 'set_transaction')

    def _commit(self):
        if self._transaction_mode:
            self._con.commit()

    def _rollback(self):
        if self._transaction_mode:
            self._con.rollback()

    def _get_where_clause(self, **kwargs) -> str:
        """
        Construct where-clause from attributes
        """
        where = kwargs.get(WHERE)
        include_deleted = kwargs.get(INCLUDE_DELETED) is True

        where_clause = EMPTY
        first = True

        # Only fetch records that are not logically deleted
        if not include_deleted and DELETED in self._cached_list(COL_NAMES):
            where_clause = f' WHERE {DELETED}={quote(DB_FALSE)}'
            first = False

        # Validate input
        if not where:
            return where_clause

        # Processing
        for att in where:
            # Check type
            if not isinstance(att, Att):
                self._raise(f'"{str(att)}" is not an Attribute', 'get_where')

            where_clause = f'{where_clause} WHERE ' if first else f'{where_clause} AND '
            first = False

            # attName="attValue"
            where_clause = f'{where_clause}{att.name}{str(att.relation)}'
            if att.type in AttType.numeric_types:
                where_clause = f'{where_clause}{str(att.value) or ZERO}'
            elif att.type == AttType.Bool:
                if att.value is True:
                    where_clause = f'{where_clause}{DB_TRUE}'
                else:
                    where_clause = f'{where_clause}{DB_FALSE}'
            else:
                # To escape single quotes, Replace ' by ''
                value = quote(str(att.value).replace("'", "''"))
                where_clause = f'{where_clause}{value}'
        return where_clause

    def _get_order_by_clause(self, order_by=None) -> str:
        """
        Construct order_by-clause from attributes
        :param order_by: List of [attribute, ASC|DESC] lists
        :return: "ORDER BY name ASC|DESC, name ASC|DESC..."
        """
        method = 'get_order_by'
        if not order_by:
            return EMPTY

        order_by_clause = EMPTY
        first = True
        for order_by_item in order_by:
            if not isinstance(order_by_item, list) or len(order_by_item) != 2:
                self._raise(f'"{str(order_by_item)}" is not a valid order by item', method)
            att = order_by_item[0]
            order = order_by_item[1]

            # Check
            if not isinstance(att, Att):
                self._raise(f'"{str(att)}" is not an Attribute', method)

            if not hasattr(OrderType, order):
                self._raise(f'"{str(order)}" is not an Order type', method)

            # Okay
            if first:
                first = False
                order_by_clause = f'{order_by_clause} ORDER BY '
            else:
                order_by_clause = f'{order_by_clause}, '
            order_by_clause = f'{order_by_clause}{att.name} {order}'

        return order_by_clause

    # Backup / Restore

    @staticmethod
    def _write_script(data_path, data):
        f = open(data_path, 'w')
        with f:
            f.write(data)

    @staticmethod
    def _read_data(data_path):
        f = open(data_path, 'r')
        with f:
            data = f.read()
            return data

    def backup_table(self, table_name, path, pgm=__name__) -> bool:
        if not table_name or not path \
                or not self.file_exists(table_name) or self.count(table_name) == 0:
            return False

        # Get table definition
        self._cache_table(table_name)

        try:
            # Get table rows from current connection
            rows = self.fetch(table_name, mode=FetchMode.WholeTable)
            table_def = self._table_defs[table_name]
            # Connect to memory
            self._db_connect(memory=True)

            with self._con:

                # Create the table in memory (with audit data)
                sql_stmt = self._get_create_table_stmt(table_name, table_def)
                self._cur.execute(sql_stmt)
                row = ['?' for _ in self._cached_list(COL_NAMES)]
                row.append('?')  # For Id
                sql_stmt = self._get_insert_stmt(table_name, row, many=True, has_id=True, add_id=True, pgm=pgm)
                self._cur.executemany(sql_stmt, rows)

                # Convert table to sql script
                script_data = '\n'.join(self._con.iterdump())
                self._write_script(path, script_data)

                # Drop table in memory
                self._cur.execute(f'DROP TABLE {table_name}')

        except Exception as e:
            self._raise(f'{sql_stmt}. {e.args[0]}', 'backup_table')
        finally:
            # Reconnect to db
            self._db_connect()
            return True

    def restore_table(self, table_name, path) -> bool:
        if not table_name or not path:
            return False

        self._cache_table(table_name)

        try:
            # Connect to memory
            self._db_connect(memory=True)

            # Get and execute Restore script
            with self._con:
                sql = self._read_data(path)

            # Connect to db
            self._db_connect()

            with self._con:
                # Drop table
                self.drop_table(table_name)
                # Restore table
                self._cur.executescript(sql)

        except Exception as e:
            self._raise(f'{table_name}. {e.args[0]}', 'restore_table')
        finally:
            # Reconnect to db
            self._db_connect()
            return True

    # Import / Export

    def import_csv_table(self, table_name, table_def, path, **kwargs) -> bool:
        if not table_name or not path or not table_def:
            return False
        """
        Import csv file into a table.
        """

        # Check input
        if not os.path.isfile(path):
            self._raise(f'File "{path}" does not exist', 'import_csv_table')

        audit_type = kwargs.get(AUDIT, AUDIT_NONE)
        empty_rows = kwargs.get(EMPTY_ROWS, False)
        self._cache_table(table_name, table_def, audit_type)

        # (Re)create the table
        self.drop_table(table_name)
        self.create_table(table_name, table_def)

        # Import the rows
        try:
            rows = self._get_csv_rows(data_path=path, empty_rows=empty_rows)
            if len(rows) > 1:
                # By default, add the Id (if the csv has one)
                kwargs[HAS_ID] = True if rows[0][0].lower() == 'id' else False
                self.insert_many(table_name, rows[1:], **kwargs)
                return True
        except (csv.Error, IOError):
            self._raise(f'File "{path}" could not be imported', 'import_csv_table')

    def _get_csv_rows(self, data_path=None, empty_rows=False) -> list:
        method = 'get_rows'

        # Validate path
        if not os.path.isfile(data_path):
            self._raise(f'File "{data_path}" does not exist.', method)
        try:
            with open(data_path, encoding='utf-8-sig') as csvFile:
                csv_reader = csv.reader(csvFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                return [row for row in csv_reader if empty_rows or any(cell != EMPTY for cell in row)]
        except (UnicodeDecodeError, csv.Error) as e:
            self._raise(f'csv error in "{data_path}": "{e}"', method)

    def _write_csv_rows(self, rows, data_path=None):
        try:
            with open(data_path, 'w') as csvFile:
                csv_writer = csv.writer(
                    csvFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                [csv_writer.writerow(row) for row in rows]
        except csv.Error as e:
            self._raise(f'{e}', 'write_rows')

    def _import_error(self, method, table_name, row, index):
        self._raise(f'Error at {table_name} row {str(index)}, row is "{str(row)}"', method)

    def export_table_to_csv(self, table_name, path, audit_data=False, where=None, include_id=True) -> int:
        if not table_name or not path:
            return 0

        self._cache_table(table_name)

        rows = self.fetch(table_name, mode=FetchMode.Set, where=where)
        if not rows:
            return 0

        # Optionally filter out audit data
        if not audit_data:
            audit_names = self._cached_list(COL_AUDIT_NAMES)
            rows = self._audit.remove_audit(audit_names, rows, include_id=include_id)

        header = ['Id'] if include_id else []
        header.extend(self._cached_list(COL_NAMES))
        out_rows = [header]
        out_rows.extend(rows)
        self._write_csv_rows(out_rows, data_path=path)
        return len(rows)

    # Routines

    def _sanitize_row(self, row) -> list:
        if len(self._cached_list(COL_SANITIZABLES)) > 0:
            for c in self._cached_list(COL_SANITIZABLES):
                row[c] = sanitize_text(row[c])
        return row

    def _get_attribute_type(self, att_name) -> str:
        for i in range(len(self._cached_list(COL_NAMES))):
            if att_name.title() == self._cached_item(COL_NAMES, i):
                return self._cached_item(COL_TYPES, i)
        self._raise(f'attribute {att_name} does not exist in {self._current_table_name}', '_get_attribute_type')

    def _execute(self, sql_stmt):
        with self._con:
            try:
                self._cur.execute(sql_stmt)
                self._commit()
            except Exception as e:
                self._rollback()
                self._raise(f'{sql_stmt}. {e.args[0]}', '_execute')

    @staticmethod
    def _tuples_to_list(db_rows, mode):
        rows = []
        if db_rows and db_rows[0]:
            rows = [list(db_row) for db_row in db_rows]
            if mode == FetchMode.First:
                return rows[0]
        return rows

    # Exceptions

    @staticmethod
    def _raise(message, method_name=None):
        prefix = f'{__name__}.{method_name}: ' if method_name else f'{__name__}: '
        if DATABASE_IS_LOCKED in message:
            print(f'DBDriver ABNORMALLY ended. {DATABASE_IS_LOCKED}.')
            sys.exit(0)
        raise DBException(f'{prefix}{message}.')

    def _check_kwargs(self, att_names, **kwargs):
        [self._raise_required(att_name) for att_name in att_names if att_name not in kwargs]
        if NAME in kwargs and not isinstance(kwargs[NAME], str):
            self._raise(f'Parameter "name" must be a string')
        elif NAMES in kwargs and not isinstance(kwargs[NAMES], list):
            self._raise(f'Parameter "names" must be a list')

    def _raise_required(self, att_name):
        self._raise(f'Parameter "{att_name}" is required')
