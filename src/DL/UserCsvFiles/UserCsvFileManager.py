#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import os
import shutil
from os import listdir

from src.DL.Config import CF_IMPORT_PATH_BOOKING_CODES, CF_IMPORT_PATH, TABLE_PROPERTIES, FILE_NAME
from src.DL.DBDriver.AttType import AttType
from src.DL.DBDriver.Audit import Program_mutation
from src.DL.IO.AccountIO import AccountIO
from src.DL.IO.AnnualAccountIO import AnnualAccountIO
from src.DL.IO.BookingIO import BookingIO
from src.DL.IO.CounterAccountIO import CounterAccountIO
from src.DL.IO.OpeningBalanceIO import OpeningBalanceIO
from src.DL.IO.SearchTermIO import SearchTermIO
from src.DL.Lexicon import CONFIG, BOOKING_CODE
from src.DL.Objects.Account import Account
from src.DL.Objects.Booking import Booking
from src.DL.Objects.CounterAccount import CounterAccount
from src.DL.Objects.OpeningBalance import OpeningBalance
from src.DL.Objects.SearchTerm import SearchTerm
from src.DL.Report import *
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.UserCsvFiles.Cache.SearchTermCache import Singleton as SearchTermCache
from src.GL.BusinessLayer.ConfigManager import ConfigManager, get_label
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import USER_MUTATIONS_FILE_NAME, EXT_CSV, MUTATION_PGM_TE, \
    MUTATION_PGM_BC, COMMA_SOURCE
from src.GL.Enums import Color, MessageSeverity, ResultCode
from src.GL.Functions import is_valid_file, toFloat
from src.GL.Result import Result
from src.GL.Validate import isCsvText, normalize_dir, isInt, toBool
from src.VL.Data.Constants.Const import LABEL_WORK_WITH_BOOKINGS, PROTECTED_BOOKINGS

PGM = 'UserCsvFileManager'

model = Model()
CM = ConfigManager()
csvm = CsvManager()
BCM = BookingCodeCache()

c_booking_id = model.get_column_number(Table.TransactionEnriched, FD.Booking_id)
c_booking_code = model.get_column_number(Table.TransactionEnriched, FD.Booking_code)
c_remarks = model.get_column_number(Table.TransactionEnriched, FD.Remarks)
c_counter_account_id = model.get_column_number(Table.TransactionEnriched, FD.Counter_account_id)


def get_backup_dirs() -> list:
    """ return: Backup/restore dirs on date (recent first)"""
    return sorted(
        [d for d in listdir(Session().backup_dir) if os.path.isdir(f'{Session().backup_dir}{d}')], reverse=True) \
        if Session().backup_dir \
        else []


class UserCsvFileManager(object):

    @property
    def result(self):
        return self._result

    def __init__(self):
        self._result = Result()
        self._session = Session()
        self._error_title = EMPTY
        self._bookings_ok = False
        self._booking_codes = set()
        self._existing_booking_codes = set()
        self._backup_sub_dirs = get_backup_dirs()

        self._user_mutations_path = f'{self._session.backup_dir}{USER_MUTATIONS_FILE_NAME}{EXT_CSV}' \
            if self._session.backup_dir else EMPTY
        self._d = {}
        self._prefix = EMPTY
        self._line_no = 0
        self._atts = None
        self._index = 0

        # IO
        self._account_io = AccountIO()
        self._counter_account_io = CounterAccountIO()
        self._booking_io = BookingIO()
        self._search_term_io = SearchTermIO()
        self._annual_account_io = AnnualAccountIO()
        self._opening_balance_io = OpeningBalanceIO()

    def validate_csv_files(self, full_check=False) -> Result:
        """
        Validate backup or resource .csv files.
            "Rekeningen.csv",
            "Boekingscodes.csv",
            "Tegenrekeningen.csv",
            "Zoektermen.csv",
            "Jaarrekening.csv",
            "Beginsaldi.csv"
        This is done before import (input validation) and in consistency check.
        They are not required to exist, ask paths via dialogue.
        Coulance when starting the app Strict when importing the files.
        Strict mode: Detail rows are validated too.
        """
        self._result = Result()
        self._error_title = f'{Color.ORANGE}{LABEL_WORK_WITH_BOOKINGS} (zie tab {CONFIG}) ' \
                            f'is nog niet mogelijk.{Color.NC}\n'

        # A. Shallow check.
        # Check/set config. If user csv file exists, always check the headers (even if not working with bookings).
        for table_name in model.csv_tables:
            if not self.set_csv_path_in_config(table_name):
                return self._result

        # B. Deep check on booking related csv files.
        # If no valid file exists (in backup folder), copy it from "<app_dir>/resources" to user Data folder.

        #   1. First bookings, they occur in the other files.
        self._booking_codes = set()
        self.validate_csv_file(Table.BookingCode, full_check)

        #   2. Then the related csv files
        if self._result.OK:
            self._bookings_ok = True
            [self.validate_csv_file(t, full_check) for t in model.booking_code_related_tables]

        # C. CleanUp rows with non-existent booking codes in user csv file
        if self._result.OK:
            [self._rename_and_clean_booking_code_in_user_csv_file(
                Table.TransactionEnriched, self._user_mutations_path, c_booking_code, from_name=nec, to_name=EMPTY,
                delete_empty=True)
                for nec in self._get_non_existent_booking_codes_from_user_csv()]
        return self._result

    def validate_csv_file(self, table_name, full_check=False, existing_booking_codes: set = None):
        """
        For backup/restore purpose existing bookings can be provided.
        Assumption for now is that the app- and local user csv files are trusted input.
        """
        if existing_booking_codes:
            self._existing_booking_codes = existing_booking_codes

        cf_code = TABLE_PROPERTIES[table_name][CF_IMPORT_PATH]

        # A. Check existence, set the valid path in config.
        if not self.set_csv_path_in_config(table_name):
            self._result.add_message(
                f'{self._error_title}Reden: Er is geen geldig bestand gevonden voor het importeren van '
                f'"{get_label(cf_code)}".', severity=MessageSeverity.Error)
            return

        # No header, then no full check.
        if table_name == Table.AnnualAccount:
            return

        path = CM.get_config_item(cf_code)
        self._prefix = f'Fout in bestand "{path}":\n'

        # B. Check header
        if not self.is_valid_csv_header(table_name, path):
            return  # Fatal error occurred

        if not full_check:
            return

        # C. Detail rows
        rows = csvm.get_rows(data_path=path)

        # Invalid characters?
        self._line_no = 0
        if not all([self._is_sane_row(row) for row in rows]):
            return

        # Unexpected type?
        self._line_no = 0
        self._atts = model.get_atts(table_name)
        if not all([
            [self._check_type(r, c, value) for c, value in enumerate(row) if value != EMPTY]
            for r, row in enumerate(rows)]):
            return

        # Invalid booking code?
        for i in range(len(rows)):
            booking_code = rows[i][model.get_column_number(table_name, FD.Booking_code, zero_based=True)]
            if booking_code:
                if table_name == Table.BookingCode and booking_code in self._existing_booking_codes:
                    raise GeneralException(
                        f'Bestand {os.path.basename(path)} kan niet geimporteerd worden.\n'
                        f'De {BOOKING_CODE} moet uniek zijn. "{booking_code}" in regel {i + 2} is een dubbel.\n'
                        f'De folder is "{os.path.dirname(path)}".')
                self._existing_booking_codes.add(booking_code)
            # Booking
            if table_name == Table.BookingCode:
                self._booking_codes.add(booking_code)
            # Counter account, SearchTerm
            elif table_name in (Table.CounterAccount, Table.SearchTerm):
                self._validate_booking_code(path, booking_code, i)
            else:
                raise GeneralException(f'Tabel "{table_name}" wordt niet ondersteund.')

        # Completion
        if self._result.OK:
            self._result.add_message(
                f'{len(rows)} {Table.description.get(table_name, table_name)} gecontroleerd.',
                severity=MessageSeverity.Info)

    def _is_sane_row(self, row) -> bool:
        self._line_no += 1
        char = EMPTY
        pos = 0
        for j in range(len(row)):
            if not isCsvText(row[j]):
                for k in range(len(row[j])):
                    if not isCsvText(row[j][k]):
                        char = row[j][k]
                        pos = k
                        break
                self._result.add_message(
                    f'{self._prefix}Waarde "{row[j]}" in regel {self._line_no} kolom {j} positie {pos} '
                    f'bevat ongeldig teken "{char}".',
                    severity=MessageSeverity.Error)
                return False
        return True

    def _check_type(self, line_no, col_no, value) -> bool:
        expected_type = self._atts[col_no + 1]
        if expected_type == AttType.Int and not value.isInt() \
                or expected_type == AttType.Float and not value.maybeFloat() \
                or expected_type == AttType.Bool and not value.isBool():
            self._result.add_message(
                f'{self._prefix}Waarde "{value}" in regel {line_no + 1} kolom {col_no + 1} is ongeldig.',
                severity=MessageSeverity.Error)
            return False
        return True

    def _validate_booking_code(self, path, booking_code, row_no):
        maingroup = BCM.get_value_from_booking_code(booking_code, FD.Booking_maingroup)
        if booking_code and booking_code not in self._existing_booking_codes \
                and maingroup not in PROTECTED_BOOKINGS:
            self._result.add_message(
                f'{Color.RED}Fout in bestand{Color.NC} "{path}:\n'
                f'Boeking "{booking_code}" in regel {row_no} kolom 1 moet bestaan in '
                f'"{CM.get_config_item(CF_IMPORT_PATH_BOOKING_CODES)}".',
                severity=MessageSeverity.Error)

    def is_valid_csv_header(self, table_name, path, message_prefix=EMPTY, has_id=False) -> bool:
        """
        Generally usage.
        Empty file or no file is considered to have a (potential) valid header.
        """
        header_row = csvm.get_first_row(data_path=path)
        if not header_row:
            return True

        model_def = {no: att for no, att in model.get_model_definition(table_name).items()
                     if not att.derived and att.in_db}  # Without derived (Booking), and must be in db

        addition = 1 if has_id else 0
        prefix = message_prefix or f'Fout in bestand "{path}":\n'
        if len(header_row) + addition < len(model_def):
            self._result.add_message(
                f'{prefix}Header is {len(header_row)} lang maar moet {len(model_def) + addition} lang zijn.',
                severity=MessageSeverity.Error)
            return False

        self._index = addition
        return all([self._is_header_title(att, header_row, no, prefix) for no, att in model_def.items()])

    def _is_header_title(self, att, header_row, no, prefix):
        if att.colhdg_report.lower() != header_row[self._index].lower():
            self._result.add_message(
                f'{prefix}Rij 1 kolom {no} is "{header_row[self._index]}" '
                f'maar moet "{att.colhdg_report}" zijn.',
                severity=MessageSeverity.Error)
        self._index += 1
        return self._result.OK

    """
    UPDATE Csv files
    """

    def rename_and_clean_booking_in_user_csv_files(self, from_name, to_name) -> Result:
        """
        After rename/delete a booking in db, the csv files in the most recent backup are updated too.
        """
        # Validate
        if not self._backup_sub_dirs:
            return Result()  # OK. Nothing to do.

        # A. Booking.csv, SearchTerm.csv, ...
        #   Get most recent restore folder
        restore_dir = normalize_dir(f'{Session().backup_dir}{self._backup_sub_dirs[0]}')
        for table_name in model.csv_tables:
            self._rename_and_clean_booking_code_in_user_csv_file(
                table_name,
                path=f'{restore_dir}{table_name}{EXT_CSV}',
                col_no=model.get_column_number(table_name, FD.Booking_id),
                from_name=from_name,
                to_name=to_name)

        # B. User_mutations.csv
        result_ok = self._rename_and_clean_booking_code_in_user_csv_file(
            Table.TransactionEnriched, self._user_mutations_path, c_booking_code, from_name, to_name)
        return Result() if result_ok else Result(ResultCode.Canceled)

    def _get_non_existent_booking_codes_from_user_csv(self) -> set:
        # booking_codes = self._booking_io.fetch_booking_codes()  # including empty
        return {
            row[c_booking_code] for row in csvm.get_rows(data_path=self._user_mutations_path)
            if row[c_booking_code] not in self._booking_codes
        }

    def _rename_and_clean_booking_code_in_user_csv_file(
            self, table_name, path, col_no, from_name, to_name, delete_empty=False) -> bool:
        """ Delete rows with empty booking and rename Booking code """
        rows = csvm.get_rows(data_path=path, include_header_row=False)
        # Update
        out_rows = []
        for row in rows:
            skip = False
            # Skip rows with empty booking
            if delete_empty and not row[col_no]:
                skip = True
                # If TE, only skip if no user data is present at all.
                if table_name == Table.TransactionEnriched and row[c_remarks]:
                    skip = False
            if skip:
                continue
            # Update
            if row[col_no] == from_name:
                row[col_no] = to_name
            out_rows.append(row)
        self._write_rows(path, table_name, out_rows)
        return True

    """
    IMPORT TABLES
    """

    def import_user_defined_csv_files(self, restore_paths=None):
        """
        Import the user definition files 1:1 to the database (only if they exist).
        Not UserMutations.csv! This is only loaded in UserMutationsCache.
        - Accounts,
        - BookingCodes,
        - CounterAccounts,
        - Search terms
        - OpeningBalances
        """
        # Import and cache.
        # A. first booking...
        self._import_rows(Table.BookingCode, restore_paths)
        BCM.initialize(force=True)

        # B. then booking dependent and other ones.
        [self._import_rows(table_name, restore_paths)
         for table_name in model.csv_tables if table_name != Table.BookingCode]

        # Initialize caches
        CounterAccountCache().initialize(force=True)  # CounterAccounts
        SearchTermCache().initialize(force=True)  # SearchTerms
        BookingCodeCache().initialize(force=True)  # BookingCodes

    def _import_rows(self, table_name, restore_paths):
        """
        Avoid duplicates. Files are validated earlier.
        Strict amount validation to prevent db pollution.
        """
        # Get the validated path, else the basic path.
        path = CM.get_config_item(TABLE_PROPERTIES[table_name][CF_IMPORT_PATH])
        if restore_paths:
            path = restore_paths.get(table_name, path)
        rows = csvm.get_rows(data_path=path, include_header_row=True)
        if not rows:
            return

        # AnnualAccount: Insert transformed amount-rows
        if table_name == Table.AnnualAccount:
            self._annual_account_io.validate(path, rows)
            self._annual_account_io.insert_many()
        else:
            header = rows[0]
            for row in rows[1:]:
                try:
                    d = dict(zip(map(lambda x: x.title(), header), row))
                    if table_name == Table.Account:
                        self._account_io.insert(
                            Account(
                                bban=d[FD.Bban.title()],
                                iban=d[FD.Iban.title()],
                                description=d[FD.Description.title()]
                            )
                        )
                    elif table_name == Table.CounterAccount:
                        self._counter_account_io.insert(
                            CounterAccount(
                                counter_account_number=d[FD.Counter_account_number.title()],
                                account_name=d[FD.Name.title()],
                                first_comment=d[FD.FirstComment.title()],
                                booking_code=d[FD.Booking_code.title()]
                            )
                        )
                    elif table_name == Table.SearchTerm:
                        self._search_term_io.insert(
                            SearchTerm(
                                search_term=d[FD.SearchTerm.title()],
                                booking_code=d[FD.Booking_code.title()])
                        )
                    elif table_name == Table.BookingCode:
                        self._booking_io.insert(
                            Booking(
                                booking_type=d[FD.Booking_type.title()],
                                booking_maingroup=d[FD.Booking_maingroup.title()],
                                booking_subgroup=d[FD.Booking_subgroup.title()],
                                booking_code=d[FD.Booking_code.title()],
                                seqno=d[FD.SeqNo],
                                protected=toBool(d[FD.Protected])
                            ))
                    elif table_name == Table.OpeningBalance:
                        comma_source = self._get_comma_source(table_name, rows)
                        self._opening_balance_io.insert(
                            OpeningBalance(
                                year=d[FD.Year.title()],
                                opening_balance=toFloat(
                                    value=d[FD.Opening_balance.title()],
                                    comma_source=comma_source))
                        )
                    else:
                        raise GeneralException(f'{PGM} unsupported table "{table_name}"')
                except KeyError as e:
                    raise GeneralException(f'{PGM} key error in csv file for table "{table_name}": {e}')

            # Booking: Also add protected bookings
            if table_name == Table.BookingCode:
                # Get last seqno of existing type + 1
                seqnos = {type: self._booking_io.get_last_seqno_for_type(type) + 1
                          for type in PROTECTED_BOOKINGS.values()}
                [self._booking_io.chkins(Booking(
                    booking_type=type,
                    booking_maingroup=maingroup,
                    booking_subgroup=EMPTY,
                    booking_code=BCM.get_protected_booking_code(maingroup),
                    seqno=seqnos[type],
                    protected=True
                ))
                    for maingroup, type in PROTECTED_BOOKINGS.items()]

    def set_csv_path_in_config(self, table_name) -> bool:
        """
        Get user csv file from
        a. ../Backup, else from
        b. ../<app_dir>/resources
        """
        file_name = TABLE_PROPERTIES[table_name][FILE_NAME]
        path = self._get_most_recent_path_name(table_name)
        # If not yet present, try to copy csv file from ../<app_dir>/resources folder.
        if path and not os.path.exists(path):
            shutil.copyfile(src=f'{self._session.resources_dir}{file_name}', dst=path)

        # Set the path (or empty) in config
        cf_code = TABLE_PROPERTIES[table_name][CF_IMPORT_PATH]
        if cf_code not in CM.config_dict:
            self._result.add_message(f'{PGM}: Missing config item {cf_code}', MessageSeverity.Error)
            return False

        CM.set_config_item(cf_code, path)
        return True if path else False

    @staticmethod
    def _get_comma_source(table_name, rows) -> str:
        df = model.get_model_definition(table_name)
        if not df or len(rows) < 2 or not any(att.type == AttType.Float for att in df.values()):
            return COMMA_SOURCE
        floats = [c - 1 for c, att in df.items() if att.type == AttType.Float]
        c = floats[0]  # First amount column
        return ',' if all(',' in row[c] for row in rows[1:] if row[c] != EMPTY) else '.'

    def _get_most_recent_path_name(self, table_name) -> str:
        """
        Get user csv file name from
        A. ../Backup, else from
        B. ../<app_dir>/resources
        """
        path = EMPTY
        file_name = TABLE_PROPERTIES[table_name][FILE_NAME]

        # a. Try to get the most recent path from Backup first.
        for subdir in self._backup_sub_dirs:
            if file_name in listdir(f'{self._session.backup_dir}{subdir}'):
                dirname = normalize_dir(f'{self._session.backup_dir}{subdir}')
                path = f'{dirname}{file_name}'
                break

        # b. Try the path in ../Data/resources.
        if not path:
            dst_resources_dir = normalize_dir(f'{self._session.resources_dir}', create=True)
            if dst_resources_dir:
                path = f'{dst_resources_dir}{file_name}'

        # c. Try ../<app_dir>/resources folder to ../Data/resources.
        if path and not os.path.exists(path):
            src = f'{self._session.resources_dir}{file_name}'
            if src and is_valid_file(src):
                path = src

        return path

    """
    Backup
    """

    def export_transaction_user_updates(self) -> bool:
        """
        Backup Booking code, Remarks. Merge with existing backup.
        Precondition: Db rows are in the same format as Csv rows (incl. Id).
        """
        table_name = Table.TransactionEnriched

        # A. Validation
        # - Get rows with direct user mutations (Booking, Remarks)
        db_rows = self._session.db.select(table_name, where=[Att(Program_mutation, MUTATION_PGM_TE)])
        # - Get rows with indirect user mutations (Booking table maintenance)
        db_rows.extend(self._session.db.select(table_name, where=[Att(Program_mutation, MUTATION_PGM_BC)]))
        if not db_rows \
                or not self.is_valid_csv_header(table_name, path=self._user_mutations_path, has_id=True):
            return False

        # B. Get user_mutations.csv content from disk
        csv_rows = csvm.get_rows(data_path=self._user_mutations_path)
        if csv_rows and db_rows and len(csv_rows[0]) < len(db_rows[0]):
            raise GeneralException(
                f'{PGM}: csv_rows have {len(csv_rows[0])} columns while db rows have {len(db_rows[0])}.')

        # C. Merge (in a dict on logical key. First csv, then updert with db)
        self._d = {}
        [self._update_with_lk(row) for row in csv_rows]
        [self._update_with_lk(row) for row in db_rows]

        # D. Convert booking Id to name
        #   (Rows from the csv files are booking-codes, in the TE it is an Id.)
        for key, row in self._d.items():
            self._d[key] = self._ids_to_codes(row)

        # E. Write csv
        self._write_rows(self._user_mutations_path, table_name, rows=[row for row in self._d.values()])
        return True

    def _update_with_lk(self, row):
        lk = model.get_logical_ID_from_row(Table.TransactionEnriched, row)
        self._d[lk] = row

    @staticmethod
    def _write_rows(path, table_name, rows):
        csvm.write_rows(
            rows=rows,
            col_names=model.get_report_colhdg_names(table_name),
            open_mode='w',
            data_path=path)

    @staticmethod
    def _ids_to_codes(row) -> list:
        """
        Export: Convert Ids to booking_codes in the row.
        At this point (merge of csv with db) the cell may contain a booking code or an Id.
        """
        cell = row[c_booking_id]
        if cell and isInt(cell):
            row[c_booking_code] = BCM.get_value_from_id(cell, FD.Booking_code)
        return row
