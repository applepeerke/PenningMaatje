
from datetime import datetime

from src.BL.Managers.ExportManager import ExportManager
from src.BL.Managers.ImportManager import ImportManager
from src.BL.Summary.SummaryDriver import SummaryDriver
from src.DL.Config import CF_OUTPUT_DIR, CF_INPUT_DIR, CF_IMPORT_PATH_BOOKINGS, CF_IMPORT_PATH_COUNTER_ACCOUNTS, \
    CF_IMPORT_PATH_SEARCH_TERMS, BOOKINGS_CSV, COUNTER_ACCOUNTS_CSV, SEARCH_TERMS_CSV
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.DBInitialize import DBInitialize
from src.DL.Enums.Enums import Summary
from src.DL.Model import FD
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.Enums import LogLevel
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import normalize_dir
from src.GL.BusinessLayer.SessionManager import Singleton as Session

CM = ConfigManager()
log = Log()
session = Session()


class PMC:
    def __init__(self, input_dir, output_dir, year=None, build=False):
        input_dir = normalize_dir(f'{session.root_dir}Input', create=True) if not input_dir else input_dir
        output_dir = normalize_dir(f'{session.root_dir}Output', create=True) if not output_dir else output_dir
        self._year = year or datetime.now().year

        session.start(output_dir=output_dir, CLI_mode=True)

        self._start_up(input_dir, output_dir, build)

        self._em = ExportManager()
        self._summary_driver = SummaryDriver()

    def produce_csv_files(self):
        # Jaarrekening t/m maand x
        self._em.export(year=self._year)

        # Kwartalen
        [self._export_transactions(q=i) for i in range(1, 5)]

        # Maanden
        [self._export_transactions(i, i) for i in range(1, 13)]

    def _export_transactions(self, month_from=None, month_to=None, q=None):
        if q:
            month_from = ((q - 1) * 3) + 1
            month_to = month_from + 2

        where = [Att(FD.Year, self._year)]
        if month_from == month_to:
            title = f'{self._year} maand {month_from} transacties'
            where.extend([Att(FD.Month, month_from)])
        else:
            title = f'{self._year} Q{q} transacties'
            where.extend([
                Att(FD.Month, month_from, relation=SQLOperator().GE),
                Att(FD.Month, month_to, relation=SQLOperator().LE)]
            )
        te_rows = session.db.select(Table.TransactionEnriched, where=where)
        if te_rows:
            self._result = self._summary_driver.create_summary(te_rows, Summary.SearchResult, title)
            if not self._result.OK:
                raise GeneralException(self._result.get_messages_as_message() or self._result.text)

    def _start_up(self, input_dir, output_dir, build) -> Result:
        """ Start without using GUI Controller """

        # Config - create json from session
        self._create_config_from_session(input_dir, output_dir)

        # DB
        result = self._start_db(build)
        if (result.OK and build) or result.RT:
            # Log
            log.start_log(session.log_dir, level=LogLevel.Verbose)
            # Populate DB
            IM = ImportManager()
            result = IM.start()
        return result

    @staticmethod
    def _create_config_from_session(input_dir, output_dir):
        """
        json config is the starting point of the Controller.
        """
        CM.unit_test = False  # Can be initialized as False (e.g. in MessageBox)
        # Base
        CM.set_config_item(CF_OUTPUT_DIR, session.output_dir)
        # Input
        CM.start_config(persist=True)
        # Booking files
        CM.set_config_item(CF_INPUT_DIR, input_dir)
        CM.set_config_item(CF_OUTPUT_DIR, output_dir)

        resources_dir = session.resources_dir
        CM.set_config_item(CF_IMPORT_PATH_BOOKINGS, f'{resources_dir}{BOOKINGS_CSV}')
        CM.set_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS, f'{resources_dir}{COUNTER_ACCOUNTS_CSV}')
        CM.set_config_item(CF_IMPORT_PATH_SEARCH_TERMS, f'{resources_dir}{SEARCH_TERMS_CSV}')

        # Write the json config
        CM.write_config()

    @staticmethod
    def _start_db(build=False) -> Result:
        DBInit = DBInitialize()
        return DBInit.start(build=build)
