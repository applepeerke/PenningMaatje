
from datetime import datetime

from src.BL.Managers.ImportManager import ImportManager
from src.BL.Summary.SummaryDriver import SummaryDriver
from src.DL.Config import CF_OUTPUT_DIR, CF_INPUT_DIR, CF_IMPORT_PATH_BOOKINGS, CF_IMPORT_PATH_COUNTER_ACCOUNTS, \
    CF_IMPORT_PATH_SEARCH_TERMS, BOOKING_CODES_CSV, COUNTER_ACCOUNTS_CSV, SEARCH_TERMS_CSV, \
    CF_IMPORT_PATH_OPENING_BALANCE, OPENING_BALANCE_CSV, CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_MONTH_TO, \
    ACCOUNTS_CSV, CF_IMPORT_PATH_ACCOUNTS
from src.DL.DBInitialize import DBInitialize
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Enums import LogLevel
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import normalize_dir

log = Log()
session = Session()


class PMC:
    def __init__(self, output_dir, year=None, build=False, input_dir=None):
        self._year = year or datetime.now().year

        self._CM = ConfigManager()
        result = self._start_up(input_dir, output_dir, build)

        if not result.OK:
            raise GeneralException(result.get_messages_as_message())

        self._summary_driver = SummaryDriver()

    def create_summary(self, summary_type, year, month_from=1, month_to=12, template_names=None, iban=None):
        self._CM.set_config_item(CF_SUMMARY_YEAR, year)
        self._CM.set_config_item(CF_SUMMARY_MONTH_FROM, month_from)
        self._CM.set_config_item(CF_SUMMARY_MONTH_TO, month_to)
        self._summary_driver.create_summary(summary_type, template_filenames=template_names, iban=iban, CLI_mode=True)

    def _start_up(self, input_dir, output_dir, build) -> Result:
        """ Start without using GUI Controller """
        input_dir = normalize_dir(f'{session.root_dir}Input', create=True) if not input_dir else input_dir
        output_dir = normalize_dir(f'{session.root_dir}Output', create=True) if not output_dir else output_dir

        # Session
        session.start(output_dir=output_dir, CLI_mode=True)

        # Config - create json from session
        self._create_config_from_session(input_dir, output_dir)

        # DB
        result = self._start_db(build)

        # Not consistent: Build
        if result.RT and not build:
            build = True
            result = self._start_db(build)

        # If db has been built, import the data.
        if result.OK:
            count = session.db.count(Table.TransactionEnriched)
            if build or count == 0:  # Import may have failed
                # Log
                log.start_log(session.log_dir, level=LogLevel.Verbose)
                # Populate DB
                IM = ImportManager()
                result = IM.start()
        return result

    def _create_config_from_session(self, input_dir, output_dir):
        """
        json config is the starting point of the Controller.
        """
        self._CM.unit_test = False  # Can be initialized as False (e.g. in MessageBox)
        # Base
        self._CM.set_config_item(CF_OUTPUT_DIR, session.output_dir)
        # Booking files
        self._CM.set_config_item(CF_INPUT_DIR, input_dir)
        self._CM.set_config_item(CF_OUTPUT_DIR, output_dir)

        resources_dir = session.resources_dir
        self._CM.set_config_item(CF_IMPORT_PATH_ACCOUNTS, f'{resources_dir}{ACCOUNTS_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_BOOKINGS, f'{resources_dir}{BOOKING_CODES_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS, f'{resources_dir}{COUNTER_ACCOUNTS_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_OPENING_BALANCE, f'{resources_dir}{OPENING_BALANCE_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_SEARCH_TERMS, f'{resources_dir}{SEARCH_TERMS_CSV}')

        # Write the json config
        self._CM.write_config()

    @staticmethod
    def _start_db(build=False) -> Result:
        DBInit = DBInitialize()
        return DBInit.start(build=build)
