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

from src.BL.Validator import Validator
from src.DL.Config import OUTPUT_DIR, CF_INPUT_DIR, CF_OUTPUT_DIR, \
    CF_SHOW_ALL_POPUPS, CF_HIDDEN_POPUPS, CF_THEME, CF_FONT, CF_FONT_SIZE, CF_FONT_TABLE, CF_FONT_TABLE_SIZE, \
    CMD_FACTORY_RESET, \
    CMD_LAYOUT_OPTIONS, CF_IMAGE_SUBSAMPLE
from src.GL.BusinessLayer.ConfigManager import ConfigManager, CMD_HELP_WITH_INPUT_DIR, CMD_HELP_WITH_OUTPUT_DIR
from src.GL.BusinessLayer.SessionManager import APP_OUTPUT_DIR
from src.GL.Const import EMPTY
from src.GL.Enums import ActionCode, ResultCode
from src.GL.Result import Result
from src.GL.Validate import normalize_dir
from src.VL.Controllers.BaseController import BaseController
from src.VL.Functions import get_name_from_text, help_message
from src.VL.Views.PopUps.Info import Info
from src.VL.Windows.LayoutOptionsWindow import LayoutOptionsWindow

CM = ConfigManager()

PGM = 'ConfigController'


class ConfigController(BaseController):

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._validation_manager = Validator()  # Used in start_config
        self._prv_values = {
            CF_INPUT_DIR: CM.get_config_item(CF_INPUT_DIR),
            CF_OUTPUT_DIR: CM.get_config_item(CF_OUTPUT_DIR),
        }

    def handle_event(self, event):
        super().handle_event(event)
        if not self._result.OK:
            return

        self._help_message()

        diag_prefix = 'Handling event - Config - '
        # Folders
        if self._event_key == get_name_from_text(CF_OUTPUT_DIR):
            self._diag_message(f'{diag_prefix}Output directory selected')
            self._config_folder_selected(CF_OUTPUT_DIR)
        elif self._event_key == get_name_from_text(CF_INPUT_DIR):
            self._diag_message(f'{diag_prefix}Input directory selected')
            self._config_folder_selected(CF_INPUT_DIR)

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
        save = {CF_THEME: CM.get_config_item(CF_THEME),
                CF_FONT: CM.get_config_item(CF_FONT),
                CF_FONT_SIZE: CM.get_config_item(CF_FONT_SIZE),
                CF_FONT_TABLE: CM.get_config_item(CF_FONT_TABLE),
                CF_FONT_TABLE_SIZE: CM.get_config_item(CF_FONT_TABLE_SIZE),
                CF_IMAGE_SUBSAMPLE: CM.get_config_item(CF_IMAGE_SUBSAMPLE)}
        prv = save.copy()
        new = {}
        self._result = Result(action_code=ActionCode.Retry)
        while not new or (any(prv[k] != new[k] for k in new) and self._result.RT):
            for k, v in new.items():
                prv[k] = v
            W.display()
            new = {CF_THEME: CM.get_config_item(CF_THEME),
                   CF_FONT: CM.get_config_item(CF_FONT),
                   CF_FONT_SIZE: CM.get_config_item(CF_FONT_SIZE),
                   CF_FONT_TABLE: CM.get_config_item(CF_FONT_TABLE),
                   CF_FONT_TABLE_SIZE: CM.get_config_item(CF_FONT_TABLE_SIZE),
                   CF_IMAGE_SUBSAMPLE: CM.get_config_item(CF_IMAGE_SUBSAMPLE)}

        self._restart_app = W.restart_app()
        if not self._restart_app:
            if all(save[k] == new[k] for k in new):
                self._result = Result()

        # Depending on selections,
        # - Reset hidden popups
        if CM.get_config_item(CF_SHOW_ALL_POPUPS):
            CM.set_config_item(CF_HIDDEN_POPUPS, {})

    """
    Config
    """

    def _config_folder_selected(self, cf_item):
        self._result = Result()
        # User may have been canceled the PopUp, or selected the same folder.
        if CM.get_config_item(cf_item) == self._prv_values.get(cf_item, EMPTY):
            self._result.code = ResultCode.Canceled
            return
        # Validate the new folder.
        self._result = self._validation_manager.validate_config_dir(cf_item)
        if not self._result.OK:
            self._cancel_smoothly(cf_item)
            return
        # Process
        if cf_item == CF_OUTPUT_DIR:
            # Main output location has been changed. This also contains the database (in subfolder Data).
            # Ask to move output folder.
            from_dir = self._prv_values[cf_item]
            to_dir = CM.get_config_item(cf_item)
            self._result = self._validation_manager.validate_move_output_dir(from_dir=from_dir, to_dir=to_dir)
            if self._result.OK:
                self._create_output_dir(to_dir)
            if not self._result.OK:
                self._cancel_smoothly(cf_item)
                return
            self._move_output_dir(from_dir=from_dir, to_dir=to_dir)
            if not self._session.started:
                self._model.do_factory_reset = True
                return
            if not self._result.OK:
                self._cancel_smoothly(cf_item)
                return
            # Set previous config value to current
            self._prv_values[cf_item] = to_dir
        elif cf_item == CF_INPUT_DIR:
            self._prv_values[cf_item] = CM.get_config_item(cf_item)
            self._model.do_import = True
        # Write the config to disk
        CM.write_config()

    def _cancel_smoothly(self, cf_item):
        text = self._result.get_messages_as_message()
        if text:
            Info().info('config_canceled_smoothly', title='Geannuleerd', text=text)
        # Reset
        CM.set_config_item(cf_item, self._prv_values[cf_item])
        self._result = Result()

    def _create_output_dir(self, to_dir):
        self._result = Result()
        # Create
        to_dir = normalize_dir(to_dir, create=True)
        if not os.path.isdir(to_dir):
            box_text = f'{OUTPUT_DIR} wijzigen is niet mogelijk.\n\nReden:\n'
            self._result = Result(ResultCode.Canceled, f'{box_text}Doelfolder {to_dir} kon niet gemaakt worden.')

    def _move_output_dir(self, from_dir, to_dir):
        self._result = Result()
        shutil.move(from_dir, f'{to_dir}{APP_OUTPUT_DIR}')
        # Restart session. Database location has changed.
        self._session.start(output_dir=to_dir, force=True)

    """
    Messages
    """

    def _help_message(self):
        if self._event_key == CMD_HELP_WITH_OUTPUT_DIR:
            help_message(CF_OUTPUT_DIR)
        elif self._event_key == CMD_HELP_WITH_INPUT_DIR:
            help_message(CF_INPUT_DIR)
