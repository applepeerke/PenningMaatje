#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# -------------------------------------------------------------------------------------------------------------------
import json
import os
from typing import Optional

from src.BL.Functions import get_icon
from src.DL.Config import *
from src.DL.DBDriver.Functions import get_home_dir
from src.VL.Data.Constants.Color import DEFAULT_FONT_TABLE, DEFAULT_FONT_TABLE_SIZE, DEFAULT_FONT, \
    DEFAULT_FONT_SIZE
from src.VL.Data.Constants.Const import FONT
from src.GL.Const import NONE, EMPTY, APP_NAME
from src.GL.Functions import is_valid_file
from src.GL.GeneralException import GeneralException
from src.GL.Validate import normalize_dir

PGM = 'ConfigManager'
SUFFIX = 'CF_'


class ConfigManager:
    """ ConfigManager """

    class ConfigManagerInstance(object):

        @property
        def unit_test(self):
            return self._unit_test

        @property
        def config_dict(self):
            return self._config_dict

        @unit_test.setter
        def unit_test(self, value):
            self._unit_test = value

        @config_dict.setter
        def config_dict(self, value):
            self._config_dict = value

        def __init__(self, unit_test=False):
            self._unit_test = unit_test
            self._config_dict = {k: I.value for k, I in configDef.items()}
            self._file_name = EMPTY
            self._persist = False
            self._log_cache = []
            self._search_dict = {
                CF_SEARCH_YEAR: EMPTY,
                CF_SEARCH_MONTH: EMPTY,
                CF_SEARCH_COUNTER_ACCOUNT: EMPTY,
                CF_SEARCH_AMOUNT: EMPTY,
                CF_SEARCH_AMOUNT_TO: EMPTY,
                CF_SEARCH_TRANSACTION_CODE: EMPTY,
                CF_SEARCH_TEXT: EMPTY,
                CF_SEARCH_REMARKS: False,
                CF_SEARCH_AMOUNT_TOTAL: EMPTY
            }

        def start_config(self, persist=False):
            self._persist = persist
            self._log_cache.append('Starting configuration')
            self._log_cache.append(f'  o Step 1/5: Config has been started with mode persist={persist} ')
            # Get config path
            path = str(self.get_path())
            if not path:
                self._fatal_error(
                    f'Configuratie pad kon niet vastgesteld worden. Ongeldig pad "{path}"')
            self._log_cache.append(f'  o Step 2/5: Config path="{path}"')

            # Write config to disk (1st time)
            text = 'exists on disk'
            if not os.path.exists(path):
                text = 'has been stored to disk (1st time)'
                self.set_config_item(CF_SETTINGS_PATH, path)
                self.write_config()
            self._log_cache.append(f'  o Step 3/5: Config {text}.')

            # Read and verify config on disk
            self._config_dict = self._verify_config(path)
            self._log_cache.append(f'  o Step 4/5: Config has been retrieved from disk.')

            # Avoid initialization issues when empty_booking mode is still active at start-up.
            self.initialize_search_criteria()
            self._log_cache.append(f'  o Step 5/5: Search criteria have been initialized.')

        def yield_log_cache(self):
            log_cache = self._log_cache
            self._log_cache = []
            return log_cache

        @staticmethod
        def _fatal_error(message):
            """
            Starting the configuration is the first step in the app. If this fails, show what happened.
            """
            try:
                import PySimpleGUI as sg
                sg.PopupOK(
                    f'\n{message}\n', title='Fout opgetreden', grab_anywhere=True, keep_on_top=True, font=FONT,
                    icon=get_icon())
            except Exception as e:
                message = f'Bericht kon niet getoond worden. Reden: "{e}"\n' \
                          f'Het te tonen bericht was: "{message}"'
                print(message)
            raise GeneralException(message)

        def write_config(self):
            path = self.get_path()
            config = {k: v for k, v in self._config_dict.items() if k.startswith(SUFFIX)}
            with open(path, "w") as f:
                json.dump(config, f, indent=4)

        def _verify_config(self, path) -> dict:
            if not os.path.exists(path):
                self._fatal_error(f'Configuratie bestaat niet in "{path}"')

            try:
                with open(path, "rb") as f:
                    d = json.load(f)
            except Exception as e:
                error_text = f'Configuratie kon niet worden geladen: {e}'
                self._fatal_error(error_text)

            # Verify all keys are in config (NB: temporary cache items in mem do not have to be on disk)
            not_in_config = {k for k in d if k not in configDef}
            if not_in_config:
                error_text = (f'Verificatie van de configuratie is mislukt. Het pad is "{path}"\n '
                              f'Niet ondersteund zijn items: {not_in_config}')
                self._fatal_error(error_text)

            # Add new config items that are not on disk yet
            not_on_disk = {k: v for k, v in configDef.items() if k not in d}
            for k, config_item in not_on_disk.items():
                if k.startswith('CF_'):
                    d[k] = config_item.value
            return d

        def config_exists(self) -> bool:
            return is_valid_file(self.get_path())

        def get_path(self) -> str:
            """
            Place "cookie" in user home dir if persistence asked for or "cookie" is already present there.
            N.B. Do not use app_root_dir, in the .app/.exe this may not exist.
            """
            suffix = '_ut' if self._unit_test else EMPTY
            if not self._file_name:
                self._file_name = f'.{APP_NAME.lower()}{suffix}.json'
            return f'{normalize_dir(os.path.expanduser(get_home_dir()))}{self._file_name}'

        def get_config_item(self, key, dft=None):
            value = self._config_dict.get(key, dft)
            # Override with specified default
            if not value and value is not False and dft is not None:
                value = dft
            return None if value == NONE else value

        def set_config_item(self, key, value, validate=True):
            if not key or key not in configDef:
                return None
            if validate:
                method = configDef.get(key, EMPTY).validation_method
                if method and not method(value):
                    raise GeneralException(f'Ongeldige waarde "{value}" voor "{get_label(key)}".')
            if key.endswith('_DIR'):
                value = normalize_dir(value)
            self._config_dict[key] = value

        def set_radio_button(self, key, value):
            # Used in Dialog
            if key == CF_RADIO_ALL:
                self.set_config_item(key, value)
                self.set_config_item(CF_RADIO_ONLY_THIS_ONE, not value)
            elif key == CF_RADIO_ONLY_THIS_ONE:
                self.set_config_item(key, value)
                self.set_config_item(CF_RADIO_ALL, not value)
            else:
                pass

        def get_tooltip(self, key) -> Optional[str]:
            """ Always show tooltip for the tooltip checkbox ;-) """
            if (key not in configDef or not self._config_dict.get(CF_TOOL_TIP, False)) \
                    and key != CF_TOOL_TIP:
                return None
            return configDef[key].tooltip

        def get_font(self, font_type=None, addition=0) -> tuple:
            font_code = f'_{font_type}' if font_type else EMPTY
            default_font = DEFAULT_FONT_TABLE if font_type == 'TABLE' else DEFAULT_FONT
            default_font_size = DEFAULT_FONT_TABLE_SIZE if font_type == 'TABLE' else DEFAULT_FONT_SIZE
            return (self.get_config_item(f'CF_FONT{font_code}', default_font),
                    int(self.get_config_item(f'CF_FONT{font_code}_SIZE', default_font_size)) + addition)

        """ 
        Layout extra columns
        """

        def get_extra_column_attribute_names(self) -> list:
            return [v for k, v in LAYOUT_EXTRA_COLUMNS.items() if self.get_config_item(k, False) is True]

        def is_attribute_visible(self, att) -> bool:
            for k, att_name in LAYOUT_EXTRA_COLUMNS.items():
                if att.name == att_name:
                    return self.get_config_item(k, True)
            return att.visible

        """ 
        Search
        """

        def set_search_for_empty_booking_codes(self, on=True):
            """
            To search for empty booking codes, the only criteria must be that
            Booking is empty and Counter account is not.
            """
            # ON
            if on:
                self.initialize_search_criteria()
                self.set_config_item(CF_SEARCH_BOOKING_CODE, LEEG)
                self.set_config_item(CF_SEARCH_COUNTER_ACCOUNT, NIET_LEEG)
            # OFF
            elif self.get_config_item(CF_SEARCH_BOOKING_CODE) == LEEG:
                self.set_config_item(CF_SEARCH_BOOKING_CODE, EMPTY)
                self.set_config_item(CF_SEARCH_COUNTER_ACCOUNT, EMPTY)

        def initialize_search_criteria(self):
            for k, v in self._search_dict.items():
                self._config_dict[k] = False if type(v) is bool else EMPTY

        def is_any_search_criterium_specified(self, exclude=None):
            return any(self._is_specified(k, v) for k, v in self._search_dict.items()
                       if not exclude or k not in exclude)

        def is_search_for_empty_booking_mode(self):
            return self.get_config_item(CF_SEARCH_BOOKING_CODE) == LEEG and \
                self.get_config_item(CF_SEARCH_COUNTER_ACCOUNT) == NIET_LEEG and \
                not self.is_any_search_criterium_specified(exclude=[CF_SEARCH_BOOKING_CODE, CF_SEARCH_COUNTER_ACCOUNT])

        def _is_specified(self, k, v):
            return (type(v) is bool and self._config_dict[k] is True) \
                or (type(v) is str and self._config_dict[k] != EMPTY)

        @staticmethod
        def _sanitize(config_dict) -> dict:
            for k, v in config_dict.items():
                if v == NONE:
                    config_dict[k] = EMPTY
            return config_dict

        """
        Dictionaries
        """

        def initialize_hidden_popup(self, key) -> str:
            hidden_popups = self.get_config_item(CF_HIDDEN_POPUPS, {})
            if key not in hidden_popups:
                hidden_popups[key] = False
            self.set_config_item(CF_HIDDEN_POPUPS, hidden_popups)
            return hidden_popups[key]

        def update_hidden_popup(self, key, value):
            self._set_dict_item(CF_HIDDEN_POPUPS, key, value)

        def get_location(self, key) -> tuple:
            return tuple(self._get_dict_item(CF_WINDOW_LOCATIONS, key, dft=(None, None)))

        def set_location(self, key, value: tuple):
            self._set_dict_item(CF_WINDOW_LOCATIONS, key, value)

        def get_combo_max(self) -> int:
            return self.get_config_item(CF_ROWS_COMBO_MAX, 20)

        def _get_dict_item(self, config_key, item_key, dft=None):
            d = self.get_config_item(config_key, {})
            value = d.get(item_key, dft)
            if not value and value is not False and dft is not None:
                value = dft
            return value

        def _set_dict_item(self, config_key, item_key, item_value):
            d = self.get_config_item(config_key, {})
            d[item_key] = item_value
            self.set_config_item(config_key, d)

    # storage for the instance reference
    __instance = None

    def __init__(self, unit_test=False):
        """ Create singleton instance """
        # Check whether we already have an instance
        if ConfigManager.__instance is None:
            # Create and remember instance
            ConfigManager.__instance = ConfigManager.ConfigManagerInstance(unit_test)

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = ConfigManager.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
