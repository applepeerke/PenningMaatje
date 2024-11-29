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
from src.DL.Config import CF_RESTORE_BOOKING_DATA, get_label, TABLE_PROPERTIES, FILE_NAME, CF_RADIO_ALL, \
    CF_POPUP_INPUT_VALUE
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.IO.SearchTermIO import SearchTermIO
from src.DL.IO.TransactionIO import TransactionIO
from src.DL.Lexicon import SEARCH_TERMS, TRANSACTIONS, BOOKING_CODES, \
    BOOKING_CODE, COUNTER_ACCOUNT, SEARCH_TERM
from src.DL.Model import FD, Model
from src.DL.Objects.SearchTerm import SearchTerm
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.UserCsvFiles.Cache.SearchTermCache import Singleton as SearchTermCache
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager, GeneralException
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import BACKUP
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity, ResultCode, ActionCode
from src.GL.Functions import is_valid_file
from src.GL.Result import Result
# Working fields
from src.GL.Validate import normalize_dir
from src.VL.Data.Constants.Const import LEEG
from src.VL.Data.Constants.Enums import Pane
from src.VL.Views.PopUps.Dialog_with_transactions import DialogWithTransactions
from src.VL.Views.PopUps.PopUp import PopUp

PGM = 'BookingManager'

model = Model()
bk_dict = model.get_colno_per_att_name(Table.BookingCode, zero_based=False)

CM = ConfigManager()
CsvM = CsvManager()
BCM = BookingCodeCache()
ACM = CounterAccountCache()
STM = SearchTermCache()
UM = UserCsvFileManager()


class BookingCodeManager(BaseManager):

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
        self._search_term_io = SearchTermIO()
        self._undo_stack = []
        self._is_consistent = False
        self._non_existent_booking_codes = {}
        self._booking_codes_db = set()
        self._reason = EMPTY
        self._restore_paths = {}

        self._booking_code = None
        self._booking_old_ids = []
        self._booking_old_ids_unique = []
        self._TE_id = 0
        self._entity_key = EMPTY
        self._entity_value = None

    def link_name_to_new_search_term(self, search_term, booking_code) -> Result:
        """ Link transactions without Counter account to a search term """
        self._entity_key = SEARCH_TERM
        self._entity_value = search_term
        self._booking_code = booking_code

        # Validation
        if not search_term:
            return Result(ResultCode.Warning, f'{SEARCH_TERM} is verplicht.')
        if search_term in STM.search_terms:
            return Result(ResultCode.Warning, f'{SEARCH_TERM} {search_term} bestaat al.')

        # List transactions while specifying a proper search term.
        self._result = Result(action_code=ActionCode.Retry)
        while self._result.RT:
            self._result = self._dialog_handling(where=[Att(FD.Name, search_term, relation=SQLOperator().LIKE)])

        # Insert searchterm
        if self._result.GO:
            # Insert the new search term.
            if self._search_term_io.insert(SearchTerm(
                    search_term=CM.get_config_item(CF_POPUP_INPUT_VALUE),
                    booking_code=booking_code)):
                # Success: Refresh search term cache.
                STM.initialize(force=True)

        # No Undo here
        return self._result

    def link_booking_to_counter_account(self, counter_account_number, booking_code) -> Result:
        """ Link counter-account-number to booking code """
        self._entity_key = COUNTER_ACCOUNT
        self._entity_value = counter_account_number
        self._booking_code = booking_code

        # Validation
        warning = ResultCode.Warning
        if not counter_account_number:
            return Result(warning, f'{COUNTER_ACCOUNT} is verplicht.')

        counter_account_id = ACM.get_id_from_iban(counter_account_number)
        if not counter_account_id:
            return Result(warning, f'{COUNTER_ACCOUNT} {counter_account_number} is niet gevonden.')

        where = [Att(FD.Counter_account_id, counter_account_id)]
        result = self._dialog_handling(where)
        if not result.OK:
            return result

        # Add Undo
        booking_id = list(self._booking_old_ids)[0] if self._booking_old_ids else 0
        self._add_undo(counter_account_id, self._TE_id, booking_id)
        return result

    def _dialog_handling(self, where) -> Result:
        # A. Validation
        # a. Target Booking code exists?
        booking_new_id = BCM.get_id_from_code(self._booking_code)
        if booking_new_id == 0 and self._booking_code:
            return Result(ResultCode.Warning, f'{BOOKING_CODE} "{self._booking_code}" is niet gevonden.')

        # b. Booking code already fully linked to the entity? Nothing to do.
        #   Get the unique booking ids that are already linked to the entity (counter account or search term)
        self._booking_old_ids = self._db.select(Table.TransactionEnriched, name=FD.Booking_id, where=where)
        self._booking_old_ids_unique = {Id for Id in self._booking_old_ids}
        if len(self._booking_old_ids_unique) == 1 and list(self._booking_old_ids_unique)[0] == booking_new_id:
            return Result(
                ResultCode.Warning,
                f'{BOOKING_CODE} "{self._booking_code}" is al gekoppeld '
                f'aan {self._entity_key} "{self._entity_value}".')

        # B. Multiple booking ids exist for the specified entity: Ask confirmation.
        update_all = True
        # if existing_bookings_count > 1:
        if len(self._booking_old_ids) > 1:
            booking_description = BCM.get_value_from_booking_code(self._booking_code, FD.Booking_description)
            dialog_text = (
                f'Er zijn {len(self._booking_old_ids)} {TRANSACTIONS} gevonden '
                f'bij {self._entity_key} "{self._entity_value}"{self._get_booking_text()}.\n\n'
                f'Deze kunnen allemaal gewijzigd worden in "{booking_description}".\nDoorgaan?')

            input_label = SEARCH_TERM if self._entity_key == SEARCH_TERM else EMPTY
            dialog = DialogWithTransactions(where=where, has_radio=True, input_label=input_label)
            if not dialog.confirm(
                    f'{PGM}.set_counter_account_booking_code', dialog_text, hide_option=False):
                return Result(action_code=ActionCode.Cancel)
            update_all = CM.get_config_item(CF_RADIO_ALL, True)

        # C. Go!
        if update_all:
            # D1. Update booking in all TransactionEnriched where counter account or search term is matched.
            self._TE_id = 0
            result = self._update_all_transactions(where, booking_new_id)
        else:
            # D2. Update booking-id,  in the current transaction only
            self._TE_id = CM.get_config_item(f'CF_ID_{Pane.TE}', 0)
            result = self._update_one_transaction(self._TE_id, booking_new_id)
        return result

    def _get_booking_text(self):
        booking_codes = BCM.get_codes_from_ids(self._booking_old_ids_unique)
        if len(self._booking_old_ids_unique) > 1:
            booking_code_bullets = "\n  o  ".join(booking_codes)
            booking_text = f' met {BOOKING_CODES}:\n  o  {booking_code_bullets}'
        else:
            if not booking_codes or booking_codes[0] == LEEG:
                booking_text = f' zonder {BOOKING_CODE}'
            else:
                booking_text = f' met {BOOKING_CODE} {booking_codes[0]}'
        return booking_text

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

    def _update_all_transactions(self, where, booking_id) -> Result:
        """
        Update booking id in MutationsEnriched for all transactions.
        """
        # Transactions_enriched: update booking_id (use MUTATION_PGM for user file backup)
        count = self._transaction_io.update_booking(
            values=[Att(FD.Booking_id, booking_id)],
            where=where)

        # - Output
        booking_code = BCM.get_value_from_id(booking_id, FD.Booking_code)
        result = Result(
            text=f'{BOOKING_CODE} "{booking_code}" is toegekend aan {count} {TRANSACTIONS} '
                 f'van {self._entity_key} {self._entity_value}.')
        return result

    """
    Undo - Counter account 
    """

    def undo_counter_account(self) -> Result:
        """ Undo update (only last one) """
        if not self.has_undo:
            return Result(text='There is nothing to undo.')

        undo_dict = self._undo_stack.pop()
        if undo_dict[FD.ID] == 0:
            Id = undo_dict[FD.Counter_account_id]
            self._entity_key = COUNTER_ACCOUNT
            self._entity_value = ACM.get_iban_from_id(Id)
            # All transactions
            result = self._update_all_transactions(
                where=[Att(FD.Counter_account_id, Id)],
                booking_id=undo_dict[FD.Booking_id])
        else:
            # 1 transaction
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
            text=f'Backup van je {BOOKING_CODES} is niet mogelijk: de database is niet consistent.'
                 f'\n\n{BOOKING_CODES} in onderstaande tabel(len) refereren naar '
                 f'niet bestaande {BOOKING_CODES} (in tabel {Table.BookingCode}):{self._reason}.'
                 f'\n\nRemedie:\n  1. Voeg de ontbrekende {BOOKING_CODES} toe, of'
                 f'\n  2. Verwijder uit de "{BACKUP}" folder backups van deze bestanden '
                 f'(of verwijder/wijzig alleen de verkeerde referenties). '
                 f'\n     importeer vervolgens de {TRANSACTIONS} opnieuw.')
        return Result(ResultCode.Canceled)

    def _get_non_existing_database_booking_codes(self):
        """ Find Booking codes in SearchTerm/CounterAccount tables that are not in Booking table. """
        self._non_existent_booking_codes = {}
        self._reason = EMPTY
        where = [Att(FD.Booking_code, EMPTY, relation=SQLOperator().NE)]
        self._booking_codes_db = set(self._db.select(Table.BookingCode, name=FD.Booking_code, where=where))
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
