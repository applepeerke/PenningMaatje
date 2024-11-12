#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import os

from src.BL.Managers.BaseManager import BaseManager
from src.DL.Config import CF_RESTORE_BOOKING_DATA, get_label, TABLE_PROPERTIES, FILE_NAME, CF_RADIO_ALL
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.IO.TransactionIO import TransactionIO
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.UserCsvFiles.Cache.SearchTermCache import Singleton as SearchTermCache
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager, GeneralException
from src.GL.BusinessLayer.SessionManager import BACKUP
from src.VL.Data.Constants.Const import LEEG
from src.VL.Data.Constants.Enums import Pane
from src.DL.Lexicon import SEARCH_TERMS, TRANSACTIONS, COUNTER_ACCOUNTS, BOOKING_CODES, \
    BOOKING_CODE, COUNTER_ACCOUNT
from src.VL.Views.PopUps.Dialog_with_transactions import DialogWithTransactions
from src.VL.Views.PopUps.PopUp import PopUp
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.Const import EMPTY, RESOURCES
from src.GL.Enums import MessageSeverity, ResultCode, ActionCode
from src.GL.Functions import is_valid_file
from src.GL.Result import Result
# Working fields
from src.GL.Validate import normalize_dir

PGM = 'BookingManager'

model = Model()
bk_dict = model.get_colno_per_att_name(Table.BookingCode, zero_based=False)

CM = ConfigManager()
CsvM = CsvManager()
BCM = BookingCache()
ACM = CounterAccountCache()
STM = SearchTermCache()
UM = UserCsvFileManager()


class BookingManager(BaseManager):

    @property
    def is_consistent(self):
        return self._is_consistent

    @property
    def restore_paths(self):
        return self._restore_paths

    def __init__(self):
        super().__init__()
        self._dialog = PopUp()
        self._transaction_io = TransactionIO()
        self._undo_stack = []
        self._is_consistent = False
        self._non_existent_booking_codes = {}
        self._booking_codes_db = set()
        self._reason = EMPTY
        self._restore_paths = {}

    def link_booking(self, counter_account_number, booking_code) -> Result:
        """ Link counter-account-number to booking code """
        # Validatie
        warning = ResultCode.Warning
        if not counter_account_number:
            return Result(warning, f'{COUNTER_ACCOUNT} {counter_account_number} is verplicht.')

        booking_new_id = BCM.get_id_from_code(booking_code)
        if booking_new_id == 0 and booking_code:
            return Result(warning, f'{BOOKING_CODE} "{booking_code}" is niet gevonden.')

        counter_account_id = ACM.get_id_from_iban(counter_account_number)
        if not counter_account_id:
            return Result(warning, f'{COUNTER_ACCOUNT} {counter_account_number} is niet gevonden.')

        where = [Att(FD.Counter_account_id, counter_account_id)]
        booking_old_ids = self._db.select(Table.TransactionEnriched, name=FD.Booking_id, where=where)
        booking_old_ids_unique = {Id for Id in booking_old_ids}

        transactions_count = len(booking_old_ids)
        bookings_count_incl_empty = len(booking_old_ids_unique)

        # A. Booking is already fully linked to the same
        booking_old_id = list(booking_old_ids_unique)[0]
        if bookings_count_incl_empty == 1 and booking_old_id == booking_new_id:
            return Result(warning,
                          f'{BOOKING_CODE} "{booking_code}" is al gekoppeld aan {COUNTER_ACCOUNT} '
                          f'"{counter_account_number}".')

        # B. Multiple transactions for the specified counter_account: Ask confirmation.
        update_all = True
        # if existing_bookings_count > 1:
        if transactions_count > 1:
            booking_codes = BCM.get_codes_from_ids(booking_old_ids_unique)
            if bookings_count_incl_empty > 1:
                booking_code_bullets = "\n  o  ".join(booking_codes)
                booking_text = f' met {BOOKING_CODES}:\n  o  {booking_code_bullets}'
            else:
                if not booking_codes or booking_codes[0] == LEEG:
                    booking_text = f'zonder {BOOKING_CODE}'
                else:
                    booking_text = f' met {BOOKING_CODE} {booking_codes[0]}'
            dialog = DialogWithTransactions(where=where, radio=True)
            if not dialog.confirm(
                    f'{PGM}.set_counter_account_booking',
                    f'Er zijn {transactions_count} {TRANSACTIONS} gevonden '
                    f'bij tegenrekening {counter_account_number}{booking_text}.\n\n'
                    f'Deze kunnen allemaal gewijzigd worden in "{booking_code}".\nDoorgaan?', hide_option=False):
                return Result(action_code=ActionCode.Cancel)
            update_all = CM.get_config_item(CF_RADIO_ALL, True)

        # D. Go!
        if update_all:
            # D1. Update booking in CounterAccount and in all TransactionEnriched
            TE_id = 0
            result = self._update_all_transactions(counter_account_id, booking_new_id)
        else:
            # D2. Update booking-id,  in the current transaction only
            TE_id = CM.get_config_item(f'CF_ID_{Pane.TE}', 0)
            result = self._update_one_transaction(TE_id, booking_new_id)

        # E. Add Undo
        if result.OK:
            booking_id = list(booking_old_ids)[0] if booking_old_ids else 0
            self._add_undo(counter_account_id, TE_id, booking_id)
        return result

    def _update_one_transaction(self, transaction_id, booking_id) -> Result:
        """
        Update booking id in TransactionsEnriched for the current transaction.
        """
        self._db.update(
            Table.TransactionEnriched, where=[Att(FD.ID, transaction_id)],
            values=[Att(FD.Booking_id, booking_id)], pgm=PGM)
        return Result(
            text=f'{BOOKING_CODE} "{BCM.get_value_from_id(booking_id, FD.Booking_code)}" '
                 f'is toegekend aan de transactie.')

    def _update_all_transactions(self, counter_account_id, booking_id) -> Result:
        """
        Update booking name in CounterAccount, and booking id in MutationsEnriched
        for all transactions.
        """
        # A. CounterAccount
        booking_code = BCM.get_value_from_id(booking_id, FD.Booking_code)
        self._db.update(
            Table.CounterAccount, where=[Att(FD.ID, counter_account_id)],
            values=[Att(FD.Booking_code, booking_code)], pgm=PGM)
        # B. Transactions_enriched: update booking_id (use MUTATION_PGM for user file backup)
        count = self._transaction_io.update_booking(
            values=[Att(FD.Booking_id, booking_id)],
            where=[Att(FD.Counter_account_id, counter_account_id)])
        # C. Wrap up
        # - Set flag to back up the table
        self._session.set_user_table_changed(Table.CounterAccount)
        # - Output
        result = Result(
            text=f'{BOOKING_CODE} "{booking_code}" is toegekend aan {count} transacties van rekening '
                 f'{ACM.get_iban_from_id(counter_account_id)}.')
        return result

    """
    Undo
    """

    def undo(self) -> Result:
        """ Undo update (only last one) """
        if not self.has_undo:
            return Result(text='There is nothing to undo.')

        undo_dict = self._undo_stack.pop()
        if undo_dict[FD.ID] == 0:
            result = self._update_all_transactions(
                counter_account_id=undo_dict[FD.Counter_account_id],
                booking_id=undo_dict[FD.Booking_id])
        else:
            result = self._update_one_transaction(
                transaction_id=undo_dict[FD.ID],
                booking_id=undo_dict[FD.Booking_id])
        return result

    def has_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def _add_undo(self, counter_account_id, transaction_id, booking_id):
        """"{ Tegenrekening-id | Transactie-id | Boeking-id oud }
        # Als Transactie-id > 0, dan alleen deze transactie undo-en """
        # validate
        if transaction_id == 0 and counter_account_id == 0:
            raise GeneralException(f'{PGM}: Setting all transactions for an empty counter account is not possible ')
        self._undo_stack.append({
            FD.Counter_account_id: counter_account_id,
            FD.ID: transaction_id,
            FD.Booking_id: booking_id
        })

    """
    Backup
    """

    def validate_db_before_backup(self) -> Result:
        """ Validate booking-related tables (before backup/export) """
        self._result = Result()

        # Are there non-existing bookings in the database?
        self._get_non_existing_database_booking_codes()
        if not self._non_existent_booking_codes:
            return Result()

        # Not consistent
        PopUp().display(
                title=f'Backup maken van {BOOKING_CODES}',
                text=f'Backup van je {BOOKING_CODES} is niet mogelijk.'
                     f'\n\nDe volgende {BOOKING_CODES} bestaan niet in tabel {Table.BookingCode}:{self._reason}.'
                     f'\n\nRemedie:\nVerwijder de {BOOKING_CODES} referenties uit bovengenoemde tabel(len).'
                     f'\nDit kun je bijvoorbeeld doen door de backups van deze bestanden uit de "{BACKUP}" folder '
                     f'te verwijderen.\nCheck eventueel of deze bestanden in folder "{RESOURCES}" bestaande'
                     f'{BOOKING_CODES} bevatten.')
        return Result(ResultCode.Canceled)

    def _get_non_existing_database_booking_codes(self):
        """ Find Booking codes in SearchTerm/CounterAccount tables that are not in Booking table. """
        self._non_existent_booking_codes = {}
        self._reason = EMPTY
        where = [Att(FD.Booking_code, EMPTY, relation=SQLOperator().NE)]
        self._booking_codes_db = set(self._db.select(Table.BookingCode, name=FD.Booking_code, where=where))
        self._validate_booking_codes_in_table(Table.CounterAccount, where, COUNTER_ACCOUNTS)
        self._validate_booking_codes_in_table(Table.SearchTerm, where, SEARCH_TERMS)

    def _validate_booking_codes_in_table(self, table_name, where, descriptive_name):
        """ Save booking codes that don't exist in BookingCodes. """
        # Get all table booking names
        booking_codes = set(self._db.select(table_name, name=FD.Booking_code, where=where))
        # Check if they exist in table Booking
        for booking_code in booking_codes:
            if booking_code not in self._booking_codes_db:
                if table_name not in self._non_existent_booking_codes:
                    self._non_existent_booking_codes[table_name] = set()
                self._non_existent_booking_codes[table_name].add(booking_code)
        self._reason = self._add_completion_text(self._reason, table_name, descriptive_name)

    def _add_completion_text(self, reason, table_name, descriptive_name) -> str:
        if table_name not in self._non_existent_booking_codes or not self._non_existent_booking_codes[table_name]:
            return reason
        sub_text = "\n    o  ".join(list(self._non_existent_booking_codes[table_name]))
        return f'{reason}\n\n  In tabel "{descriptive_name}":\n    o  {sub_text}'

    """
    Restore
    """

    def validate_csv_files_before_restore(self):
        """ Validate booking-related csv files (before import) """
        self._result = Result()
        self._non_existent_booking_codes = {}

        # Validate the restore folder (e.g. "../2023-01-21")
        subdir = CM.get_config_item(CF_RESTORE_BOOKING_DATA)
        if not subdir:
            self._result.add_message(
                f'Selecteer eerst een terugzet folder bij "{get_label(CF_RESTORE_BOOKING_DATA)}".',
                severity=MessageSeverity.Warning)
            return
        dirname = normalize_dir(f'{self._session.backup_dir}{subdir}')
        if not dirname or not os.path.isdir(dirname):
            self._result.add_message(
                f'Terugzet folder "{subdir}" is niet gevonden in "{self._session.backup_dir}".',
                severity=MessageSeverity.Error)
            return

        # Validate the csv files format in the restore folder
        self._get_restore_paths(dirname, subdir)
        if not self._result.OK:
            return

        # Validate: bookings in csv files (except in BookingCodes.csv) must exist
        # a. in the BookingCodes.csv (if present in the backup), or else
        # b. in the database.
        booking_codes = set()
        if self._restore_paths.get(Table.BookingCode, EMPTY):
            rows = CsvM.get_rows(data_path=self._restore_paths.get(Table.BookingCode), include_header_row=True)
            header = rows[0]
            c_booking_code = header.index(FD.Booking_code.title())
            for row in rows[1:]:
                booking_codes.add(row[c_booking_code])
        else:
            # Populate booking cache with tabel BookingCodes
            BCM.initialize(force=True)
            booking_codes = BCM.booking_codes
        self._validate_other_csv_file_bookings(booking_codes)

        # Completion
        text = f'het volgende bestand ' if len(self._restore_paths) == 1 else f'de volgende bestanden '
        bullets = '\n    o  '.join([os.path.basename(p) for p in self._restore_paths.values()])
        if not PopUp().confirm(
                'Restore_booking_related_data',
                f'De volgende acties zullen worden uitgevoerd:\n\n'
                f'1. Vanuit subfolder "{subdir}" {text} terugzetten in de database:\n\n    o  {bullets}\n\n'
                f'2. Opnieuw importeren van je {TRANSACTIONS}.\n\n'):
            self._result = Result(ResultCode.Canceled)

    def _get_restore_paths(self, dirname, subdir):
        self._restore_paths = {}
        for table_name in model.csv_tables:
            filename = TABLE_PROPERTIES.get(table_name, {}).get(FILE_NAME, EMPTY)
            path = f'{dirname}{filename}'
            if is_valid_file(path):
                rows = CsvManager().get_rows(data_path=path, include_header_row=True)
                if len(rows) < 2:  # No data or only a header: ignore
                    continue
                self._restore_paths[table_name] = path
                header = rows[0]
                model_def = model.get_db_definition(table_name)
                for colno, att in model_def.items():
                    if att.name.title() != header[colno - 1].title():
                        cause = f'\n\nIn kolom {colno} wordt "{att.name.title()}" verwacht ' \
                                f'maar er is "{header[colno - 1].title()}" gevonden.'
                        self._result.add_message(
                            f'Terug te zetten bestand "{filename}" in subfolder "{subdir}" heeft ongeldige header:'
                            f'\n"{header}".{cause}',
                            severity=MessageSeverity.Error)
                        break
                    continue
        # Nothing found
        if not self._restore_paths:
            self._result.add_message(
                f'Er zijn geen terug te zetten bestanden gevonden in subfolder "{subdir}".',
                severity=MessageSeverity.Warning)

    def _validate_other_csv_file_bookings(self, booking_codes=None):
        # Check if other files match with the Booking cache.
        # (Booking cache is populated from either Booking.csv or else Booking table).
        for table_name, path in self._restore_paths.items():
            if table_name in model.booking_code_related_tables:
                UM.validate_csv_file(table_name, full_check=True, existing_booking_codes=booking_codes)
