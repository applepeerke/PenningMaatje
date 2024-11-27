
from datetime import datetime

from src.BL.Managers.ImportManager import ImportManager
from src.BL.Summary.SearchResults import SearchResults
from src.BL.Summary.SummaryDriver import SummaryDriver
from src.DL.Config import CF_OUTPUT_DIR, CF_INPUT_DIR, CF_IMPORT_PATH_BOOKING_CODES, CF_IMPORT_PATH_COUNTER_ACCOUNTS, \
    CF_IMPORT_PATH_SEARCH_TERMS, BOOKING_CODES_CSV, COUNTER_ACCOUNTS_CSV, SEARCH_TERMS_CSV, \
    CF_IMPORT_PATH_OPENING_BALANCE, OPENING_BALANCE_CSV, CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_MONTH_TO, \
    ACCOUNTS_CSV, CF_IMPORT_PATH_ACCOUNTS, CF_VERBOSE
from src.DL.DBInitialize import DBInitialize
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Lexicon import BOOKING_CODES
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Enums import LogLevel
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import normalize_dir

session = Session()


class PMC:
    def __init__(self, output_dir, year=None, build=False, input_dir=None, iban=None, verbose=False):
        self._year = year or datetime.now().year
        self._iban = iban

        self._CM = ConfigManager()
        result = self._start_up(input_dir, output_dir, build, verbose)

        if not result.OK:
            raise GeneralException(result.get_messages_as_message())

        self._summary_driver = SummaryDriver()

    def _start_up(self, input_dir, output_dir, build, verbose) -> Result:
        """ Start without using GUI Controller """
        input_dir = normalize_dir(f'{session.root_dir}Input', create=True) if not input_dir else input_dir
        output_dir = normalize_dir(f'{session.root_dir}Output', create=True) if not output_dir else output_dir

        # Session
        session.start(output_dir=output_dir, CLI_mode=True)

        # Config - create json from session
        self._create_config_from_session(input_dir, output_dir, verbose)

        # DB
        result = self._start_db(build)

        # Not consistent: Build
        if result.RT and not build:
            build = True
            result = self._start_db(build)

        # If db has been built
        if result.OK:
            count = session.db.count(Table.TransactionEnriched)
            # Import the data.
            if build or count == 0:  # Import may have failed
                # Log
                Log().start_log(session.log_dir, level=LogLevel.Verbose)
                # Populate DB
                IM = ImportManager()
                result = IM.start()
            # Write transactions without booking code
            if verbose:
                self._CM.set_search_for_empty_booking_codes()
                title = f'Ontbrekende {BOOKING_CODES}'
                TX = TransactionsIO()
                TX.search(title=f'\n{title}: ')
                if len(TX.rows) > 0:
                    SearchResults().create_summary(TX.rows, title=title, timestamp=False)
                    Log().new_line()
        return result

    def _create_config_from_session(self, input_dir, output_dir, verbose):
        """
        json config is the starting point of the Controller.
        """
        self._CM.unit_test = False  # Can be initialized as False (e.g. in MessageBox)
        # Base
        self._CM.set_config_item(CF_OUTPUT_DIR, session.output_dir)
        # Booking files
        self._CM.set_config_item(CF_INPUT_DIR, input_dir)
        self._CM.set_config_item(CF_OUTPUT_DIR, output_dir)
        self._CM.set_config_item(CF_VERBOSE, verbose)

        userdata_dir = session.userdata_dir
        self._CM.set_config_item(CF_IMPORT_PATH_ACCOUNTS, f'{userdata_dir}{ACCOUNTS_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_BOOKING_CODES, f'{userdata_dir}{BOOKING_CODES_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS, f'{userdata_dir}{COUNTER_ACCOUNTS_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_OPENING_BALANCE, f'{userdata_dir}{OPENING_BALANCE_CSV}')
        self._CM.set_config_item(CF_IMPORT_PATH_SEARCH_TERMS, f'{userdata_dir}{SEARCH_TERMS_CSV}')

        # Write the json config
        self._CM.write_config()

    @staticmethod
    def _start_db(build=False) -> Result:
        DBInit = DBInitialize()
        return DBInit.start(build=build)

    def create_summary(self, summary_type, year, month_from=1, month_to=12, template_names=None):
        self._CM.set_config_item(CF_SUMMARY_YEAR, year)
        self._CM.set_config_item(CF_SUMMARY_MONTH_FROM, month_from)
        self._CM.set_config_item(CF_SUMMARY_MONTH_TO, month_to)
        self._summary_driver.create_summary(summary_type, template_filenames=template_names, iban=self._iban,
                                            CLI_mode=True)
