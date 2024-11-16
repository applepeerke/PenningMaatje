import datetime
import fnmatch
import os
from os import listdir

from src.DL.Config import CF_BACKUP_RETENTION_MONTHS, LEEG, TABLE_PROPERTIES, FILE_NAME, NIET_LEEG
from src.DL.DBDriver.Att import Att
from src.DL.DBInitialize import DBInitialize
from src.DL.IO.AccountIO import AccountIO
from src.DL.Model import Model, FD, ID
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY
from src.GL.Functions import file_staleness_in_days
from src.GL.Result import Result
from src.GL.Validate import normalize_dir

PGM = 'Data_Driver'

BCM = BookingCodeCache()
CM = ConfigManager()
csvm = CsvManager()

model = Model()


def _find_files_for_type(file_type, basedir=os.curdir):
    """
    Return all file paths matching the specified file type in the specified base directory (recursively).
    """
    for path, dirs, files in os.walk(os.path.abspath(basedir)):
        for filename in fnmatch.filter(files, file_type):
            yield os.path.join(path, filename)


class Singleton:
    """ Singleton """

    class DataDriver(object):
        """Implementation of Singleton interface """

        @property
        def result(self):
            return self._result

        @property
        def db(self):
            return self._db

        def __init__(self):
            self._result = Result()
            self._combos = {}
            self._db = None
            self._db_started = False

        def start(self, build=False):
            if self._db_started and not build:
                return

            self._result = DBInitialize().start(build)
            if self._result.OK and Session().db:
                self._db = Session().db
                self._db_started = True

        """ 
        Combo boxes  
        """

        def initialize_combos(self):
            if not self._db_started:
                return
            self._combos[FD.Iban] = AccountIO().get_ibans()
            # From flat files
            self._set_combo_items(FD.Year)
            self._set_combo_items(FD.Month)
            self._set_combo_items(FD.Booking_description_searchable)
            # - Transaction pane (all bookings)
            self._set_combo_items(FD.Booking_code)
            self._set_combo_items(FD.Counter_account_number)
            self._set_combo_items(FD.Transaction_code)
            self._set_combo_items(FD.Booking_type)
            return

        def _set_combo_items(self, combo_name):
            # Get data
            items = []
            if combo_name == FD.Month:
                items = [x for x in range(1, 13, 1)]
            elif combo_name == FD.Booking_code:
                items = [x for x in BCM.get_booking_code_descriptions(include_protected=False)]
            elif combo_name == FD.Booking_description_searchable:
                # Only booking descriptions that are present in TransactionEnriched
                booking_ids = [
                    row[0] for row in self._db.select(Table.BookingCode)
                    if self._db.count(Table.TransactionEnriched, where=[Att(FD.Booking_id, row[0])]) > 0
                ]
                items = sorted([BCM.get_value_from_id(Id, FD.Booking_description) for Id in booking_ids])
            # Set combo
            self._combos[combo_name] = [EMPTY]
            if items:
                self._combos[combo_name].extend(items)
            else:  # From FlatFiles
                self._combos[combo_name].extend(self._get_combo_data(combo_name))

        def get_combo_items(self, name):
            rows = self._combos.get(name, [])
            return rows

        def set_get_combo_items(self, combo_name) -> list:
            self._set_combo_items(combo_name)
            return self.get_combo_items(combo_name)

        def _get_combo_data(self, att_name) -> list:
            # For a ComboBox, field name to select == table name.
            result = self._db.select(
                Table.FlatFiles,
                name=FD.Value,
                where=[Att(FD.Key, value=att_name)],
            )
            result = [r for r in result if r not in (LEEG, NIET_LEEG)]  # Exclude "*Leeg*" and "*NietLeeg"
            return sorted(result, reverse=True) if att_name == FD.Year else sorted(result)

        """ R  """

        def fetch_1_row(self, table_name, where):
            return self._db.fetch_one(table_name, where=where)

        def fetch_value(self, table_name, name, where):
            return self._db.fetch_value(table_name, name=name, where=where)

        def fetch_id(self, table_name, Id) -> int:
            return self._db.fetch_id(table_name, where=[FD.ID, Id])

        def has_rows(self, table_name) -> bool:
            return self.count(table_name) > 0

        def count(self, table_name) -> int:
            """ db may not yeet been started in error condition """
            return self._db.count(table_name) if self._db else 0

        def insert_many(self, table_name, rows, clear=False):
            if clear:
                self._db.clear(table_name)
            self._db.insert_many(table_name, rows, pgm=PGM)

        def select(self, table_name, name, where):
            rows = self._db.select(
                table_name,
                name=name,
                where=where
            )
            return rows

        def fetch_set(self, table_name, where=None, order_by=None, header=True) -> list:
            rows = []
            if header:
                no_id_row = model.get_report_colhdg_names(table_name, include_not_in_db=True)
                row = [ID]
                for name in no_id_row:
                    row.append(name)
                rows.append(row)
            if table_name == Table.Month:
                order_by = [[Att(FD.Year), 'DESC'], [Att(FD.Month), 'ASC']]
            elif table_name == Table.Year:
                order_by = [[Att(FD.Year), 'DESC']]
            elif table_name == Table.TransactionEnriched:
                order_by = [[Att(FD.Date), 'DESC']]
            elif table_name == Table.BookingCode:
                order_by = [[Att(FD.SeqNo), 'ASC'], [Att(FD.Booking_code), 'ASC']]
            elif table_name == Table.SearchTerm:
                order_by = [[Att(FD.Booking_code), 'ASC']]
            rows.extend(self._db.fetch(
                table_name,
                order_by=order_by,
                where=where
            ))
            # derived
            if table_name == Table.SearchTerm:
                # Populate Booking_description from booking_code
                d = model.get_colno_per_att_name(table_name, zero_based=False, include_not_in_db=True)
                s = 1 if header else 0
                for row in rows[s:]:
                    row[d[FD.Booking_description]] = BCM.get_value_from_booking_code(
                        row[d[FD.Booking_code]], FD.Booking_description)
            return rows

        """
        Save user updates
        """

        @staticmethod
        def export_user_tables():
            """ Booking related user tables (CounterAccounts, SearchTerms) - backup whole table """
            session = Session()
            backup_dir = session.backup_dir

            tables_to_backup = \
                [table_name for table_name, changed in session.user_tables_changed.items()
                 if changed is True]
            if not tables_to_backup:
                return

            # - Get date-time subdirectory of the backup folder.
            backup_subdir = normalize_dir(
                f'{backup_dir}{datetime.datetime.now().strftime("%Y%m%d")}', create=True)

            # - Backup
            [session.db.export_table_to_csv(
                table_name,
                f'{backup_subdir}{TABLE_PROPERTIES.get(table_name, {}).get(FILE_NAME, EMPTY)}', include_id=False)
                for table_name in tables_to_backup]

            # - Initialize "made-changes" session flags.
            [session.set_user_table_changed(table_name, value=False)
             for table_name in tables_to_backup]

        def update_fields(self, Id, table_name, fields):
            # Update a field on Id
            self._db.update(table_name, values=fields, where=[Att(FD.ID, Id)], pgm=PGM)

        """
        Clean up backup files
        """

        def delete_stale_files(self, retention_days=None):
            data_dir = Session().backup_dir
            retention_days = retention_days if retention_days is not None \
                else int(CM.get_config_item(CF_BACKUP_RETENTION_MONTHS) or 12) * 30

            # Sort by date (desc)
            path_list = sorted(
                [path for path in _find_files_for_type("*.csv", data_dir)
                 if any(properties[FILE_NAME] == os.path.basename(path) for properties in TABLE_PROPERTIES.values())
                 and file_staleness_in_days(path) >= retention_days],
                reverse=True)

            if len(path_list) > 1:
                d = {}
                # List the files per basename (like "Boekingen.csv")
                for path in path_list:
                    basename = os.path.basename(path)
                    if basename in d:
                        d[basename].append({'path': path, 'staleness': file_staleness_in_days(path)})
                    else:
                        d[basename] = [{'path': path, 'staleness': file_staleness_in_days(path)}]
                count = 0
                for path_list in d.values():
                    path_list = sorted(path_list, key=lambda x: x['staleness'])
                    # Always retain most recent version
                    for path_dict in path_list[1:]:
                        # Remove file
                        os.remove(path_dict['path'])
                        count += 1
                self._result.add_message(
                    f'Er zijn {count} bestanden verwijderd na een bewaarperiode van {retention_days} dagen.')

            # Remove empty folders
            self._delete_empty_subdirs(data_dir)

        @staticmethod
        def _delete_empty_subdirs(data_dir):
            if not data_dir or not os.path.isdir(data_dir):
                return
            try:
                [os.rmdir(f'{data_dir}{dir_name}') for dir_name in listdir(data_dir)
                 if os.path.isdir(f'{data_dir}{dir_name}') and not listdir(f'{data_dir}{dir_name}')]
            except NotImplementedError:
                return

    """ 
    BookingCodes 
    """

    def get_transaction_count(self, table_name, booking_code) -> int:
        if booking_code:
            Id = self._db.fetch_id(table_name, where=[Att(FD.Booking_code, booking_code)])
            return self._db.count(Table.TransactionEnriched, where=[Att(FD.Booking_id, Id)])
        return 0

    # ---------------------------------------------------------------------------------------------------------------------
    # Singleton logic
    # ---------------------------------------------------------------------------------------------------------------------

    # storage for the instance reference
    _instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton._instance is None:
            # Create and remember instance
            Singleton._instance = Singleton.DataDriver()

        # Store instance reference as the only member in the handle
        self.__dict__['__Singleton_instance'] = Singleton._instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self._instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self._instance, attr, value)
