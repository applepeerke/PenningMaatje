#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import os
import shutil

from src.BL.Managers.BookingCodeManager import BookingCodeManager
from src.BL.Summary.Templates.Const import ACCOUNT_NAME_LABEL
from src.BL.Validator import Validator
from src.DL.Config import OUTPUT_DIR, CF_INPUT_DIR, CF_OUTPUT_DIR, \
    CF_SHOW_ALL_POPUPS, CF_HIDDEN_POPUPS, CF_THEME, CF_FONT, CF_FONT_SIZE, CF_FONT_TABLE, CF_FONT_TABLE_SIZE, \
    CMD_FACTORY_RESET, \
    CMD_LAYOUT_OPTIONS, CF_IMAGE_SUBSAMPLE
from src.DL.DBDriver.Att import Att
from src.DL.IO.AccountIO import AccountIO
from src.DL.Lexicon import CMD_RESTORE_BACKUP
from src.DL.Model import FD
from src.DL.Objects.Account import Account
from src.DL.Table import Table
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager
from src.GL.BusinessLayer.ConfigManager import CMD_HELP_WITH_INPUT_DIR, CMD_HELP_WITH_OUTPUT_DIR
from src.GL.BusinessLayer.SessionManager import OUTPUT_SUBDIRS
from src.GL.Const import EMPTY
from src.GL.Enums import ActionCode, ResultCode
from src.GL.Result import Result
from src.GL.Validate import normalize_dir
from src.VL.Controllers.BaseController import BaseController
from src.VL.Functions import get_name_from_text, help_message
from src.VL.Views.PopUps.Info import Info
from src.VL.Views.PopUps.Input import Input
from src.VL.Windows.LayoutOptionsWindow import LayoutOptionsWindow

PGM = 'ConfigController'

class ConfigController(BaseController):

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._validation_manager = Validator()  # Used in start_config
        self._UM = UserCsvFileManager()
        self._booking_manager = BookingCodeManager()

        self._prv_values = {
            CF_INPUT_DIR: self._CM.get_config_item(CF_INPUT_DIR),
            CF_OUTPUT_DIR: self._CM.get_config_item(CF_OUTPUT_DIR),
        }

    def handle_event(self, event):
        super().handle_event(event)
        if not self._result.OK:
            return

        self._help_message()

        diag_prefix = 'Handling event - Config - '

        if event[0] == Table.Account:
            self._diag_message('Handling event - Account row selected')
            self._handle_row(self._model.account_model, event[2][0])

        # Folders
        elif self._event_key == get_name_from_text(CF_OUTPUT_DIR):
            self._diag_message(f'{diag_prefix}Output directory selected')
            self._config_folder_selected(CF_OUTPUT_DIR)
        elif self._event_key == get_name_from_text(CF_INPUT_DIR):
            self._diag_message(f'{diag_prefix}Input directory selected')
            self._config_folder_selected(CF_INPUT_DIR)

        # Restore backup
        elif self._event_key == CMD_RESTORE_BACKUP:
            self._diag_message(f'{diag_prefix}Restore backup button pressed')
            self._restore_booking_related_data()
            self._result.action_code = ActionCode.Close

        # Factory reset
        elif self._event_key == CMD_FACTORY_RESET:
            self._diag_message(f'{diag_prefix}Factory reset button pressed')
            self._model.do_factory_reset = True
            self._result.action_code = ActionCode.Retry

        # Layout options
        elif self._event_key == CMD_LAYOUT_OPTIONS:
            self._diag_message(f'{diag_prefix}Layout buttons button pressed')
            self._maintain_layout_options()

    def _maintain_layout_options(self):
        W = LayoutOptionsWindow()

        # While theme is changed: Reopen window with new theme (if new theme can be shown in pane).
        save = {CF_THEME: self._CM.get_config_item(CF_THEME),
                CF_FONT: self._CM.get_config_item(CF_FONT),
                CF_FONT_SIZE: self._CM.get_config_item(CF_FONT_SIZE),
                CF_FONT_TABLE: self._CM.get_config_item(CF_FONT_TABLE),
                CF_FONT_TABLE_SIZE: self._CM.get_config_item(CF_FONT_TABLE_SIZE),
                CF_IMAGE_SUBSAMPLE: self._CM.get_config_item(CF_IMAGE_SUBSAMPLE)}
        prv = save.copy()
        new = {}
        self._result = Result(action_code=ActionCode.Retry)
        while not new or (any(prv[k] != new[k] for k in new) and self._result.RT):
            for k, v in new.items():
                prv[k] = v
            W.display()
            new = {CF_THEME: self._CM.get_config_item(CF_THEME),
                   CF_FONT: self._CM.get_config_item(CF_FONT),
                   CF_FONT_SIZE: self._CM.get_config_item(CF_FONT_SIZE),
                   CF_FONT_TABLE: self._CM.get_config_item(CF_FONT_TABLE),
                   CF_FONT_TABLE_SIZE: self._CM.get_config_item(CF_FONT_TABLE_SIZE),
                   CF_IMAGE_SUBSAMPLE: self._CM.get_config_item(CF_IMAGE_SUBSAMPLE)}

        self._restart_app = W.restart_app()
        if not self._restart_app:
            if all(save[k] == new[k] for k in new):
                self._result = Result()

        # Depending on selections,
        # - Reset hidden popups
        if self._CM.get_config_item(CF_SHOW_ALL_POPUPS):
            self._CM.set_config_item(CF_HIDDEN_POPUPS, {})

    def _handle_row(self, VM, row_no):
        self._result = Result()
        accounts_io = AccountIO()
        row = VM.rows[row_no]
        account_prv = accounts_io.row_to_obj(row)
        description = Input((200, 200)).get_input(
            label=ACCOUNT_NAME_LABEL,
            dft=account_prv.description,
            unit_test=self._session.unit_test
        )
        if description is not None:  # Window not closed/canceled
            account = Account(account_prv.bban, account_prv.iban, description)
            if accounts_io.update(account, where=[Att(FD.Bban, account.bban)]):
                # - Set flag to back up the table
                self._session.set_user_table_changed(Table.Account)

        # Restart Config view
        self._result = Result(action_code=ActionCode.Retry)
    """
    Config
    """

    def _config_folder_selected(self, cf_item):
        self._result = Result()
        # User may have been canceled the PopUp, or selected the same folder.
        if self._CM.get_config_item(cf_item) == self._prv_values.get(cf_item, EMPTY):
            self._result.code = ResultCode.Canceled
            return

        # Process
        if cf_item == CF_OUTPUT_DIR:
            # Main output location has been changed. This also contains the database (in subfolder Data).
            # So a simple update (oops) is not possible...
            from_dir = self._prv_values[cf_item]
            to_dir = self._CM.get_config_item(cf_item)

            # Validation: From output folder must contain ONLY the supported subdirs.
            if not self._validation_manager.is_valid_existing_output_dir(from_dir):
                self._cancel_smoothly(cf_item)
                return

            # Validate the new output folder. Must be empty or populated with the output subfolders.
            self._result = self._validation_manager.validate_config_dir(cf_item)
            if not self._result.OK:
                self._cancel_smoothly(cf_item)
                return

            # Ask to move the output folder.
            if not self._validation_manager.is_valid_existing_output_dir(to_dir):
                self._result = self._validation_manager.validate_move_output_subdirs(from_dir=from_dir, to_dir=to_dir)
                if self._result.OK:
                    self._create_output_dir(to_dir)
                if not self._result.OK:
                    self._cancel_smoothly(cf_item)
                    return

                # Move
                [shutil.move(f'{from_dir}{base_name}', to_dir) for base_name in OUTPUT_SUBDIRS]

            # Restart session. Database location has changed.
            basename = os.path.basename(from_dir[:-1])
            to_dir = normalize_dir(os.path.join(to_dir, basename))  # Past 'Output' to to_dir
            self._session.start(output_dir=to_dir, force=True)
            if not self._session.started:
                self._model.do_factory_reset = True
                return
            if not self._result.OK:
                self._cancel_smoothly(cf_item)
                return
            # Set previous config value to current
            self._prv_values[cf_item] = to_dir

        elif cf_item == CF_INPUT_DIR:
            # Validate the new folder.
            self._result = self._validation_manager.validate_config_dir(cf_item)
            if not self._result.OK:
                self._cancel_smoothly(cf_item)
                return
            self._prv_values[cf_item] = self._CM.get_config_item(cf_item)
            self._model.do_import = True

        # Write the config to disk
        self._CM.write_config()

    def _cancel_smoothly(self, cf_item):
        text = self._result.get_messages_as_message()
        if text:
            Info().info('config_canceled_smoothly', title='Geannuleerd', text=text)
        # Reset
        self._CM.set_config_item(cf_item, self._prv_values[cf_item])
        self._result = Result()

    def _create_output_dir(self, to_dir):
        self._result = Result()
        # Create
        to_dir = normalize_dir(to_dir, create=True)
        if not os.path.isdir(to_dir):
            box_text = f'{OUTPUT_DIR} wijzigen is niet mogelijk.\n\nReden:\n'
            self._result = Result(ResultCode.Canceled, f'{box_text}Doelfolder {to_dir} kon niet gemaakt worden.')

    def _restore_booking_related_data(self):
        # 1.Check inner consistency of booking related csv files to be imported
        self._booking_manager.validate_csv_files_before_restore()
        self._result = self._booking_manager.result
        if not self._result.OK:
            return

        # 2. Import csv files from the selected backup
        self._UM.import_user_defined_csv_files(self._booking_manager.restore_paths)
        self._result = self._UM.result
        if not self._result.OK:
            return

        # 3. Import all bank transactions (without csv files) to link them the bookings
        self._model.do_import = True

    """
    Messages
    """

    def _help_message(self):
        if self._event_key == CMD_HELP_WITH_OUTPUT_DIR:
            help_message(CF_OUTPUT_DIR)
        elif self._event_key == CMD_HELP_WITH_INPUT_DIR:
            help_message(CF_INPUT_DIR)
