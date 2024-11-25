import os
from datetime import datetime

from src.BL.Managers.BookingManager import BookingManager
from src.BL.Managers.ConsistencyManager import ConsistencyManager
from src.BL.Managers.ImportManager import ImportManager
from src.BL.Validator import Validator, slash
from src.DL.Config import CF_IBAN, TAB_LOG, CMD_IMPORT_TE, CMD_WORK_WITH_BOOKING_CODES, \
    CMD_WORK_WITH_SEARCH_TERMS, CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION
from src.DL.Config import CF_OUTPUT_DIR, CF_VERBOSE, \
    CF_INPUT_DIR, CMD_HELP_WITH_BOOKING, get_label, CMD_HELP_WITH_OUTPUT_DIR, INPUT_DIR, CMD_FACTORY_RESET, \
    CF_REMARKS, get_text_file
from src.DL.IO.CounterAccountIO import CounterAccountIO
from src.DL.IO.TransactionIO import TransactionIO
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Lexicon import (
    OUTPUT_DIR, TRANSACTIONS, CMD_SEARCH_FOR_EMPTY_BOOKING_CODE, COUNTER_ACCOUNTS, BOOKING_CODES, to_text_key,
    CMD_WORK_WITH_OPENING_BALANCES, SEARCH_TERMS, OPENING_BALANCES)
from src.DL.Model import Model
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import STRIPE, EMPTY, APP_NAME, BLANK, USER_MUTATIONS_FILE_NAME, EXT_CSV
from src.GL.Enums import MessageSeverity, ResultCode, LogLevel, ActionCode
from src.GL.Functions import remove_crlf, remove_file
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result, log
from src.GL.Validate import toBool, isInt
from src.VL.Controllers.BaseController import BaseController, DD
from src.VL.Data.Constants.Color import GREEN, BLUE
from src.VL.Data.Constants.Const import CMD_CONSISTENCY, CMD_HELP_WITH_INPUT_DIR, LEEG, CMD_SEARCH, CMD_UNDO, \
    CMD_CONFIG, CMD_SUMMARY
from src.VL.Data.Constants.Enums import Pane
from src.VL.Functions import help_message, get_name_from_text
from src.VL.Models.BaseModelTable import BaseModelTable
from src.VL.Views.PopUps.Info import Info
from src.VL.Views.PopUps.Input import Input
from src.VL.Views.PopUps.PopUp import PopUp
from src.VL.Windows.ConfigWindow import ConfigWindow
from src.VL.Windows.General.Boxes import confirm_factory_reset, info_box
from src.VL.Windows.General.MessageBox import message_box
from src.VL.Windows.ListWindow import BookingCodesWindow, OpeningBalancesWindow
from src.VL.Windows.ListWindow import SearchTermsWindow
from src.VL.Windows.SearchWindow import SearchWindow
from src.VL.Windows.SummaryWindow import SummaryWindow

BCM = BookingCodeCache()

model = Model()

CsvM = CsvManager()
CM = ConfigManager()

PGM = 'MainController'
REFRESH_TRANSACTIONS = '_refresh_transactions'


def get_log_line(label=EMPTY, indent=0, key=EMPTY):
    line = '. . . . . . . . . . . . . . . . . . . . . : '
    text = get_label(key) if key else label
    indentation = BLANK * indent if indent > 0 else EMPTY
    return f'{indentation}{text}{line[len(indentation) + len(text):]}'


class MainController(BaseController):

    @property
    def unit_test(self):
        return self._unit_test

    @property
    def is_a_transaction_saved_in_this_iteration(self):
        return self._is_a_transaction_saved_in_this_iteration

    @property
    def db_started(self):
        return self._db_started

    @property
    def restart_app(self):
        return self._restart_app

    """
    Setters
    """

    @is_a_transaction_saved_in_this_iteration.setter
    def is_a_transaction_saved_in_this_iteration(self, value):
        self._is_a_transaction_saved_in_this_iteration = value

    @restart_app.setter
    def restart_app(self, value):
        self._restart_app = value

    def __init__(self, main_model, main_window, unit_test=False, diagnostic_mode=False):
        super().__init__(diagnostic_mode)
        self._main_model = main_model
        self._main_window = main_window
        self._unit_test = unit_test

        self._result = Result()
        self._restart_app = False
        self._search_mode = False
        self._db_started = False
        self._managers_started = False

        self._input_dir_changed = False
        self._session.is_a_transaction_saved = False
        self._is_a_transaction_saved_in_this_iteration = False
        # After a fatal error, do a factory reset.
        if self._diagnostic_mode:
            self._factory_reset(ask_to_remove=False)
        # Start config - Here already because needed by ViewModel initialization
        self._validation_manager = Validator()  # Used in start_config
        self._start_config(unit_test)
        # Start diagnostic mode in verbose
        if not self._diagnostic_mode and toBool(CM.get_config_item(CF_VERBOSE, False)) is True:
            self._diagnostic_mode = True
            self._diag_message('Starting Diagnostic mode (Configuration has been started, in verbose logging mode)')

        self._dialog = PopUp()

        self._IM = None
        self._UM = None
        self._IO = None
        self._counter_account_io = None
        self._transactions_io = None
        self._transaction_io = None
        self._consistency_manager = None
        self._booking_manager = None

        self._session = None
        self._search_window = None
        self._config_window = None

    def start_up(self):
        # Config has already been started in constructor.
        if self._result.ER:  # Constructor error (E.g. No output folder set)
            return
        self._result = Result()

        # Start the session
        self._start_session()

        # Log the cached config messages
        self._diag_message('Starting Log')
        self._start_log('Configuration')

        # Start Db
        db_built = self._start_db()
        if not self._result.OK:
            return

        self._start_managers()

        if self._input_dir_changed or db_built:
            self._diag_message('Starting Import')
            self.import_transactions()
            self._input_dir_changed = False

        # Warning mode.
        # Now the GUI can be built. Even when there is no data.
        self._diag_message('Validating Booking related csv files')
        self._result = self._UM.validate_resource_files(full_check=False)

        # sg window.
        self._diag_message('Starting GUI')
        self._main_model.build_all_panes()

        if self._result.ER:
            raise GeneralException(self._result.get_messages_as_message())

    def _start_session(self):
        if not self._session or not self._session.started:
            self._diag_message('Starting Session')
            self._session = Session()
            self._session.start(CM.get_config_item(CF_OUTPUT_DIR), unit_test=CM.unit_test)
        if not self._session.started:
            self._result = Result(ResultCode.Error, self._session.error_message)

    def _start_db(self) -> bool:
        self._diag_message('Starting Database')
        self._db_started = False
        build = False
        DD.start(build)
        # Retry
        if not DD.result.OK:
            build = True
            DD.start(build)
            self._result = DD.result
            if not self._result.OK:
                self._diag_message('Starting Factory reset')
                self._factory_reset(f'De {APP_NAME} database kon niet gestart worden.')
                self._restart_app = True
        # Success
        if self._result.OK:
            self._db_started = True
        return build

    def _start_managers(self):
        self._managers_started = False
        # IO managers need session db.
        self._diag_message('Starting IO managers')
        self._main_model.start_io()
        self._counter_account_io = CounterAccountIO()
        self._transactions_io = TransactionsIO()
        self._transaction_io = TransactionIO()

        # DD need IO managers.
        self._diag_message('Populating Combo boxes')
        DD.initialize_combos()

        self._diag_message('Starting Import/Export managers')
        self._IM = ImportManager()
        self._UM = UserCsvFileManager()
        self._consistency_manager = ConsistencyManager()
        self._booking_manager = BookingManager()
        if self._result.OK:
            self._managers_started = True

    def handle_event(self, event):
        super().handle_event(event)
        if not self._result.OK:
            return

        self._is_a_transaction_saved_in_this_iteration = False

        # Save pending remarks from Transaction pane
        if self._event_key != get_name_from_text(CF_REMARKS):
            self.save_pending_remarks()

        self._help_message()

        # _________________
        # D a s h b o a r d
        # -----------------
        diag_prefix = 'Handling event - Dashboard - '
        # Account number
        if self._event_key == get_name_from_text(CF_IBAN):
            self._diag_message(f'{diag_prefix}Account number selected')
            self._main_model.refresh_dashboard()

        # Button clicks
        # - Refresh
        elif self._event_key == CMD_IMPORT_TE:
            self._diag_message(f'{diag_prefix}Import button pressed')
            self._save_and_backup()
            self.import_transactions()

        # - Config
        elif self._event_key == CMD_CONFIG:
            self._diag_message(f'{diag_prefix}Configuration button pressed')
            self.config()

        # - Search
        elif self._event_key == CMD_SEARCH:
            self._diag_message(f'{diag_prefix}Search button pressed')
            CM.set_search_for_empty_booking_codes_with_counter_account(on=False)  # Deactivate search empty_booking mode.
            self.search()

        # - Summary
        elif self._event_key == CMD_SUMMARY:
            self._diag_message(f'{diag_prefix}Summary button pressed')
            SummaryWindow(self._main_model.models[Pane.TE].rows).display()

        # - Undo
        elif self._event_key == CMD_UNDO:
            self._diag_message(f'{diag_prefix}Undo button pressed')
            self._result = self._booking_manager.undo()
            if self._result.OK:
                self._search_for_empty_booking_codes()

        # - Search for empty booking
        elif self._event_key == CMD_SEARCH_FOR_EMPTY_BOOKING_CODE:
            self._diag_message(f'{diag_prefix}Search for empty booking button pressed')
            self._search_for_empty_booking_codes()

        # Table row clicks
        elif isinstance(event, tuple) and len(event) == 3 and isInt(event[2][0]):
            diag_prefix = 'Handling event - Dashboard row selected: '
            if event[0] == Table.Year:
                self._diag_message(f'{diag_prefix}Year')
                self._search_mode = False
                CM.initialize_search_criteria()  # Deactivate search empty_booking mode.
                self._main_model.refresh_dashboard(Pane.YS, pane_row_no=event[2][0])
            elif event[0] == Table.Month:
                self._diag_message(f'{diag_prefix}Month')
                self._search_mode = False
                CM.initialize_search_criteria()  # Deactivate search empty_booking mode.
                self._main_model.refresh_dashboard(Pane.MS, pane_row_no=event[2][0])
            elif event[0] == Table.TransactionEnriched:
                self._diag_message(f'{diag_prefix}Transactions enriched')
                self._main_model.refresh_dashboard(Pane.TE, pane_row_no=event[2][0], TX_only=True)
            elif event[0] == Table.Log:
                self._diag_message('Handling event - Log row selected')
                self._show_log_row(self._main_model.models[Pane.LG], event[2][0])

        # Transaction pane
        # - Booking
        elif self._event_key == get_name_from_text(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION):
            self._diag_message(f'{diag_prefix}Counter account number selected')
            self._set_counter_account_booking_code(
                self._main_model.models[Pane.TX].counter_account,
                BCM.get_code_from_combo_desc(CM.get_config_item(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION)))
            if self._result.OK:
                self._result = self._main_model.refresh_dashboard(
                    Pane.TE, CM.get_config_item(f'CF_ROW_NO_{Pane.TE}'), search_mode=self._search_mode)

        # - Remarks - update the model (for appearance), but pend the db action until another event is done.
        elif self._event_key == get_name_from_text(CF_REMARKS):
            self._diag_message(f'{diag_prefix}Remarks changed')
            self._main_model.models[Pane.TX].update_from_config()

        # ___________________________
        # T a b   B o o k i n g s
        # ---------------------------
        # Work with bookings
        elif self._event_key == CMD_WORK_WITH_BOOKING_CODES:
            self._maintain_booking_code_related(diag_prefix, BOOKING_CODES, BookingCodesWindow)

        elif self._event_key == CMD_WORK_WITH_SEARCH_TERMS:
            self._maintain_booking_code_related(diag_prefix, SEARCH_TERMS, SearchTermsWindow)

        elif self._event_key == CMD_WORK_WITH_OPENING_BALANCES:
            self._maintain_booking_code_related(diag_prefix, OPENING_BALANCES, OpeningBalancesWindow, refresh=False)

        # _____________
        # T a b   L o g
        # -------------
        diag_prefix = 'Handling event - Log - '
        if self._event_key == CMD_CONSISTENCY:
            self._diag_message(f'{diag_prefix}Consistency button pressed')
            self._consistency_check()

        # _____________
        # W r a p   u p
        # -------------

        # Remarks saved: refresh TE rows
        elif self._is_a_transaction_saved_in_this_iteration:
            self._main_model.refresh_dashboard(
                Pane.TE, CM.get_config_item(f'CF_ROW_NO_{Pane.TE}'), search_mode=self._search_mode)

    def _maintain_booking_code_related(self, prefix, table_desc, window, refresh=True):
        self._diag_message(f'{prefix}Work with {table_desc} button pressed')
        self._maintain_list(window)
        # Changes made in BookingCodes, then back up, re-import and refresh caches.
        if refresh and any(changed for changed in self._session.user_tables_changed.values()):
            self.import_transactions()

    def _start_config(self, unit_test):
        try:
            CM.start_config(unit_test)
            # - Input dir and Output dir MUST exist.
            self._set_required_config(CF_INPUT_DIR)
            self._set_required_config(CF_OUTPUT_DIR)
            if self._input_dir_changed:
                # Save required items immediately to json. To avoid the dialog asking set it again.
                CM.write_config()

            # Log config startup steps in diagnostic mode
            config_cache = CM.yield_log_cache()
            if self._diagnostic_mode:
                [log(line, sev=MessageSeverity.Completion) for line in config_cache]
        except GeneralException as ge:
            self._result = Result(ResultCode.Error, ge.message)
            self._factory_reset(
                f'{APP_NAME} kon niet gestart worden.', f'{ge.message}\n\n', ask_to_remove=False)

    def _consistency_check(self):
        # This is from Log pane, so no completion message needed here.
        self._start_log('Consistentie check')
        self._consistency_manager.run()
        self._import_log()
        return

    """
    Initialization
    """

    def _set_required_config(self, config_item):
        dir_name_prv = CM.get_config_item(config_item)
        if config_item == CF_INPUT_DIR:
            self._input_dir_changed = False

        # Pop up
        self._get_required_config(config_item)

        # Fail
        dir_name = CM.get_config_item(config_item)
        if not dir_name or not os.path.isdir(dir_name):
            raise GeneralException(
                f'Verplichte folder "{get_label(config_item)}" kon niet ingesteld worden.')
        # Success
        elif dir_name != dir_name_prv:
            if config_item == CF_INPUT_DIR:
                self._input_dir_changed = True

    def _get_required_config(self, config_item, force=False):
        while not self._is_valid_required_dir(config_item) or force:
            force = False
            if not Input().set_folder_in_config(
                    config_item, self._result, version=get_text_file('Version')):
                # Box closed
                CM.set_config_item(config_item, EMPTY)
                break
            # Prevent loop when unittest auto_continues with an invalid dir
            if self._session.unit_test and self._session.unit_test_auto_continue:
                break

    def _is_valid_required_dir(self, config_item) -> bool:
        """ Checked at start up, folder change, consistency check, and import transactions. """
        self._result = Result()
        dir_name = CM.get_config_item(config_item, EMPTY)
        if not dir_name or not os.path.isdir(dir_name):
            return False
        # Output dir MUST NOT contain valid transaction files, and MUST contain > 0 subfolder with transaction files.
        # Input dir MUST contain valid transaction files only.
        self._result = self._validation_manager.validate_config_dir(config_item)
        return self._result.OK

    @staticmethod
    def has_data() -> bool:
        return DD.has_rows(Table.TransactionEnriched)

    def has_undo(self) -> bool:
        return self._search_mode and self._booking_manager.has_undo()

    @staticmethod
    def has_log_data() -> bool:
        return DD.has_rows(Table.Log)

    """
    Dashboard
    """

    def import_transactions(self, import_user_csv_files=True):
        self._result = Result()

        # Ask user confirmation
        if import_user_csv_files and not self._is_import_confirmed():
            return

        # Go
        try:
            # - Initialize if e.g. called from UT
            if not self._session or not self._session.started:
                self._start_session()
            if self._result.OK and not self._db_started:
                self._start_db()
            if self._result.OK and not self._managers_started:
                self._start_managers()
            if not self._result.OK:
                raise GeneralException(self._result.get_messages_as_message())

            self._start_log('Import')

            # - First save pending booking related data, and backup it in the csv folder of today.
            self._save_and_backup(validate_db=False)

            # - Import
            result = self._IM.start(import_user_csv_files)
            self._import_log()

            if result.OK:
                # Force restart after new import. Accounts and layout may be changed.
                self._restart_app = True
                self._result = Result(action_code=ActionCode.Retry, text=f'Import is gedaan.')
                return

            action = 'geannuleerd' if result.ER else 'gedaan met waarschuwingen'
            self._result = Result(code=result.code, text=f'Import is {action}. Zie tab{TAB_LOG}voor meer informatie.')
        except GeneralException as ge:
            self._result = Result(ResultCode.Error, ge.message)

    def _is_import_confirmed(self) -> bool:

        # No data yet, then skip the dialog.
        if not self.has_data():
            return True

        input_dir = CM.get_config_item(CF_INPUT_DIR)
        if not input_dir:
            return False

        text = f'Wil je {TRANSACTIONS} opnieuw importeren?\n\n' \
               f'De gegevens in {APP_NAME} worden dan vervangen.\n' \
               f'De {INPUT_DIR} is:\n\n  "{os.path.basename(input_dir[:-1])}"'

        if not self._dialog.confirm(popup_key=f'{PGM}.import_transactions', text=text):
            self._result = Result(action_code=ActionCode.Cancel)
            return False
        return True

    def _search_for_empty_booking_codes(self):
        """ search for empty booking codes """
        self._search_mode = True
        CM.set_search_for_empty_booking_codes_with_counter_account()
        self._result = self._transactions_io.search(dialog_mode=False)
        if not self._transactions_io.rows:
            message_box(f'Gefeliciteerd!\nAlle {TRANSACTIONS} met {COUNTER_ACCOUNTS} zijn al gecategoriseerd.',
                        key='all_booking_codes_set')
            return
        # Update Transactions pane: set header, formatted rows
        rows = [Model().get_report_colhdg_names(Table.TransactionEnriched)]
        rows.extend(self._transactions_io.rows)
        self._main_model.models[Pane.TE].set_data(rows)

    """
    Dashboard - Transaction pane - "Remarks" is editable
    """

    @staticmethod
    def check_emptied_remarks():
        if CM.get_config_item(CF_REMARKS) == EMPTY:
            CM.set_config_item(CF_REMARKS, LEEG)

    def save_pending_remarks(self):
        if self._transaction_io and self._transaction_io.save_pending_remarks():
            self._flag_transaction_saved()

    def _flag_transaction_saved(self, message=EMPTY):
        self._session.is_a_transaction_saved = True
        self._is_a_transaction_saved_in_this_iteration = True
        self._result = Result(ResultCode.Ok, message or 'Gegevens zijn gewijzigd.')

    def _set_counter_account_booking_code(self, iban, booking_code):
        """
        Update the booking code of a counter_account via the transaction pane
        """
        self._result = self._booking_manager.link_booking(iban, booking_code)
        if not self._result.OK:
            return
        self._flag_transaction_saved()

    def config(self):
        loop_count = 0
        while loop_count < 100:
            loop_count += 1
            account_model = BaseModelTable(Table.Account)
            account_model.set_data(DD.fetch_set(Table.Account))
            self._config_window = ConfigWindow(account_model)
            self._config_window.display()
            self._result = self._config_window.result
            if self._config_window.model.do_factory_reset:
                self._factory_reset(to_text_key(CMD_FACTORY_RESET))
                break
            if self._result.OK and self._config_window.model.do_import:
                self.import_transactions(import_user_csv_files=False)
                break
            if not self._result.RT:  # Account description changed: redisplay
                break

    def search(self):
        self._search_window = SearchWindow(self._main_model, self._main_window)
        self._search_window.display()
        self._result = self._search_window.result
        if CM.is_any_search_criterium_specified():
            self._search_mode = True

    """
    Tab Log
    """

    @staticmethod
    def _show_log_row(VM, row_no):
        row = VM.rows[row_no]
        info_box(row[1:-6][0], 'Log regel')

    def _start_log(self, action) -> str:
        """ Start the logging, return the path """
        log_level = LogLevel.Verbose if CM.get_config_item(CF_VERBOSE, False) else LogLevel.Info
        log_path = f'{self._session.log_dir.replace(self._session.output_dir, EMPTY)}{Log().log_file_name}'

        # For start log: Verbose
        Session().set_suffix()
        Log().start_log(Session().log_dir, level=LogLevel.Verbose)

        log(STRIPE, GREEN)
        log(f"Applicatie {APP_NAME}", GREEN)
        log(STRIPE, GREEN)

        log(get_log_line('Datum en tijd'), BLUE, new_line=False)
        log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        log(get_log_line('Actie'), BLUE, new_line=False)
        log(action)
        # Folder met bankafschriften
        log(get_log_line(INPUT_DIR), BLUE, new_line=False)
        log(CM.get_config_item(CF_INPUT_DIR))
        # Uitvoer folder
        log(get_log_line(key=CF_OUTPUT_DIR), BLUE, new_line=False)
        log(self._session.output_dir)
        log(f'{OUTPUT_DIR} items en subfolders:', BLUE)
        log(get_log_line('Database', indent=2), BLUE, new_line=False)
        log(f'..{slash()}{self._session.database_path.replace(self._session.output_dir, EMPTY)}')
        log(get_log_line('Backup folder', indent=2), BLUE, new_line=False)
        log(f'..{slash()}{self._session.backup_dir.replace(self._session.output_dir, EMPTY)}')
        log(get_log_line('Log', indent=2), BLUE, new_line=False)
        log(f'..{slash()}{log_path}')
        log(get_log_line('Log niveau'), BLUE, new_line=False)
        log(log_level)

        log(STRIPE, GREEN)

        # Now set the desired level
        Log().log_level = log_level
        self._log_started = True
        return log_path

    def _import_log(self):
        log_file_name = Log().log_file_name
        with open(f'{self._session.log_dir}{log_file_name}') as f:
            lines = f.readlines()
        out_lines = [[remove_crlf(line)] for line in lines]
        DD.insert_many(Table.Log, out_lines, clear=True)

    """
    Close
    """

    def close(self):
        # Main display is to be closed, so a separate messagebox (if any serious messages)
        if not self._result.OK:
            message_box(self._result.get_messages_as_message(), severity=self._result.severity, key='before_close')
        self._result = Result()
        try:
            self._save_and_backup()
            self._delete_stale_files()
            # Display message(s)
            message_box(self._result.get_messages_as_message(), severity=self._result.severity, key='after_close')
            CM.write_config()
        except GeneralException as ge:
            message_box(ge.message, severity=MessageSeverity.Error)

    def _delete_stale_files(self):
        DD.delete_stale_files()
        self._result.add_messages(DD.result.messages)

    def _save_and_backup(self, validate_db=True):
        """
        1. Save pending db changes (remarks)
        2. Backup booking related db data in csv files of the backup folder of today
        """
        self.save_pending_remarks()
        self._export_user_updates(validate_db)

    def _export_user_updates(self, validate_db=True):
        """
        Backup wijzigingen in "Boekingen, Zoektermen etc." in csv bestanden in een subdir.
        Backup wijzigingen in transacties ("Remarks, boeking") op generiek level.
        """
        if not self._session.is_a_transaction_saved and \
                not any(changed is True for changed in self._session.user_tables_changed.values()):
            return  # Nothing to do.

        # Db consistency check
        if validate_db:
            # Between restoring user csv files and importing bank transactions a check is not needed.
            self._result = Result()
        else:
            self._result = self._booking_manager.validate_db_before_backup()
        if not self._result.OK:
            return

        # A. Main tables (Booking and SearchTerm and ...).
        # If any of the main user tables is changed, or user_mutations.csv must be updated,
        # backup all user maintenance tables.
        # N.B. Strictly speaking this full backup is only needed when booking has been changed.
        [self._session.set_user_table_changed(table_name) for table_name in model.user_maintainable_tables]
        DD.export_user_tables()
        self._result.add_message(f'Er is een backup gemaakt van handmatige wijzigingen.')

        # When the user updates e.g. the booking main table, user_mutations.csv is updated already.
        # So backup user_mutations.csv only when the user has updated a transaction.
        if not self._session.is_a_transaction_saved:
            return

        # B. Transaction updates (Remarks, Booking)
        self._session.is_a_transaction_saved = False
        if self._UM.export_transaction_user_updates():
            self._result.add_message(
                f'Er is een backup gemaakt van je {TRANSACTIONS} wijzigingen in '
                f'{USER_MUTATIONS_FILE_NAME}{EXT_CSV}.')

    """
    Messages
    """

    def _help_message(self):
        if self._event_key == CMD_HELP_WITH_OUTPUT_DIR:
            help_message(CF_OUTPUT_DIR)
        elif self._event_key == CMD_HELP_WITH_INPUT_DIR:
            help_message(CF_INPUT_DIR)
        if self._event_key == CMD_HELP_WITH_BOOKING:
            help_message(CMD_HELP_WITH_BOOKING)

    """
    Error handling
    """

    def _factory_reset(self, title=None, sub_title=EMPTY, ask_to_remove=True):
        # Config may have been removed at restart app.
        if not CM.config_exists():
            return
        try:
            if ask_to_remove and not confirm_factory_reset(
                    f'{sub_title}Wil je {APP_NAME} opnieuw instellen?\n\n'
                    f'Wijzigingen die je in {APP_NAME} hebt aangebracht zullen verwijderd worden.\n'
                    f'Backups blijven wel bewaard.\n',
                    title):
                self._result = Result(ResultCode.Canceled)
                return
            # Remove config
            message = EMPTY
            if remove_file(CM.get_path()):
                message = 'De configuratie is verwijderd.'
            # Remove database
            db_path = self._session.database_path
            if db_path:
                remove_file(f'{db_path}-shm')
                remove_file(f'{db_path}-wal')
                if remove_file(db_path):
                    message = 'De gegevens en de configuratie zijn verwijderd.' \
                        if message else 'De gegevens zijn verwijderd.'
            # Exit
            if message:
                Info().info('factory_reset_message', text=message)
                self._result = Result(ResultCode.Exit)
            if self._unit_test:
                raise GeneralException('Unit test exception')
        except Exception as e:
            print(str(e))
            if self._unit_test:
                raise
