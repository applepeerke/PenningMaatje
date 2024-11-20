#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ------------------------------------------------------------------------------------------------------------------

import datetime

from PenningMaatje import get_root_dir, get_app_root_dir, slash
from src.DL.Model import Model
from src.DL.Lexicon import OUTPUT_DIR, LOG
from src.GL.Const import APP_NAME, EMPTY
from src.GL.Validate import normalize_dir

PGM = 'SessionManager'

UT = 'UT'
BACKUP = 'Backup'
EXPORT = 'Export'
DATA = 'Data'
INPUT = 'Input'
OUTPUT = 'Output'
IMAGES = 'images'
RESOURCES = 'resources'
TEMPLATES = 'templates'
DB_EXT = '.db'
OUTPUT_SUBDIRS = (BACKUP, DATA, LOG, EXPORT)


class Singleton:
    """ Singleton """

    class SessionManager:
        """Implementation of Singleton interface """

        @property
        def error_message(self):
            return self._error_message

        @property
        def started(self):
            return self._started

        @property
        def root_dir(self):
            return self._root_dir

        @property
        def output_dir(self):
            return self._output_dir

        @property
        def export_dir(self):
            return self._export_dir

        @property
        def resources_dir(self):
            return self._resources_dir

        @property
        def database_dir(self):
            return self._database_dir

        @property
        def images_dir(self):
            return self._images_dir

        @property
        def templates_dir(self):
            return self._templates_dir

        @property
        def database_path(self):
            return self._database_path

        @property
        def db(self):
            return self._db

        @property
        def log_dir(self):
            return self._log_dir

        @property
        def backup_dir(self):
            return self._backup_dir

        @property
        def suffix(self):
            return self._suffix

        @property
        def unit_test(self):
            return self._unit_test

        @property
        def unit_test_auto_continue(self):
            return self._unit_test_auto_continue

        @property
        def account_bban(self):
            return self._account_bban

        @property
        def user_tables_changed(self):
            return self._user_tables_changed

        @property
        def is_a_transaction_saved(self):
            return self._is_a_transaction_saved
        
        @property
        def CLI_mode(self):
            return self._CLI_mode

        """
        Setters
        """

        @db.setter
        def db(self, value):
            self._db = value

        @account_bban.setter
        def account_bban(self, value):
            self._account_bban = value

        @unit_test_auto_continue.setter
        def unit_test_auto_continue(self, value):
            self._unit_test_auto_continue = value

        @is_a_transaction_saved.setter
        def is_a_transaction_saved(self, value):
            self._is_a_transaction_saved = value

        def __init__(self):
            """
            Constructor
            """
            self._error_message = EMPTY

            self._app_initialized = False
            self._started = False

            self._root_dir = None
            self._app_root_dir = None
            self._app_src_dir = None
            self._resources_dir = None
            self._database_dir = None
            self._output_dir = None
            self._log_dir = None
            self._backup_dir = None
            self._export_dir = None
            self._images_dir = None
            self._templates_dir = None
            self._database_path = None
            self._suffix = None
            self._unit_test = False
            self._unit_test_auto_continue = False
            self._db = None
            self._account_bban = None
            self._user_tables_changed = {}
            self._is_a_transaction_saved = False
            self._CLI_mode = False

            self._initialize_app()

        def _initialize_app(self):
            if self._app_initialized:
                return

            # App folders
            self._root_dir = get_root_dir()
            self._app_src_dir = get_app_root_dir()
            self._resources_dir = normalize_dir(f'{self._app_src_dir}{RESOURCES}')
            self._templates_dir = normalize_dir(f'{self._resources_dir}{TEMPLATES}')
            self._images_dir = normalize_dir(f'{self._resources_dir}{IMAGES}')

            self._app_initialized = True

        def start(self, output_dir=EMPTY, unit_test=False, force=False, CLI_mode=False) -> bool:
            if self._started and not unit_test and not force:
                return True

            # Output folder is required
            self._started = False
            self._output_dir = normalize_dir(output_dir)
            self._unit_test = unit_test
            self._CLI_mode = CLI_mode

            # Unit test - Input override
            if self._unit_test:
                self._output_dir = normalize_dir(f'{self._root_dir}{UT}{slash()}{OUTPUT}') if not output_dir else output_dir
                self._resources_dir = normalize_dir(f'{self._root_dir}{UT}{slash()}{RESOURCES}')
                self._templates_dir = normalize_dir(f'{self._resources_dir}{TEMPLATES}')

            if self._output_dir:
                self.set_suffix()
                self._set_paths()
                self._started = self._error_message == EMPTY
            else:
                self._error_message = f'{OUTPUT_DIR} is verplicht.'

            return self._started

        def set_suffix(self):
            self._suffix = f'_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S.%f")

        def _set_paths(self) -> bool:
            # Output
            self._database_dir = normalize_dir(f'{self._output_dir}{DATA}', create=True)
            self._log_dir = normalize_dir(f'{self._output_dir}{LOG}', create=True)
            self._backup_dir = normalize_dir(f'{self._output_dir}{BACKUP}', create=True)
            self._export_dir = normalize_dir(f'{self._output_dir}{EXPORT}', create=True)
            self._database_path = f'{self._database_dir}{APP_NAME}{DB_EXT}'

            # Check
            if not self._output_dir \
                    or not self._resources_dir \
                    or not self._database_dir \
                    or not self._log_dir \
                    or not self._backup_dir \
                    or not self._templates_dir \
                    or not self._images_dir:
                self._error_message = f'Niet alle folder paden konden ingesteld worden.'
                return False
            return True

        def set_user_table_changed(self, table_name, value=True):
            if table_name in Model().user_maintainable_tables:
                self._user_tables_changed[table_name] = value

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
            Singleton._instance = Singleton.SessionManager()

        # Store instance reference as the only member in the handle
        self.__dict__['__Singleton_instance'] = Singleton._instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self._instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self._instance, attr, value)
