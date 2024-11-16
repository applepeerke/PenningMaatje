#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Functions import get_BBAN_from_IBAN
from src.BL.Summary.SearchResults import SearchResults
from src.BL.Summary.Templates.AnnualAccount import AnnualAccount
from src.BL.Summary.Templates.Const import MONTH_FROM, MONTH_TO
from src.BL.Summary.Templates.PeriodicAccount import PeriodicAccount
from src.BL.Summary.Templates.ResultPerBookingCode import ResultsPerBookingCode
from src.DL.Config import CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_MONTH_TO, \
    CF_SUMMARY_OPENING_BALANCE, CF_IBAN
from src.DL.Enums.Enums import Summary
from src.DL.Lexicon import TEMPLATE_ANNUAL_ACCOUNT, SEARCH_RESULT, PERIODIC_ACCOUNTS, YEAR, ACCOUNT_NUMBER, \
    TEMPLATE_NAME, TEMPLATE_RESULTS_PER_BOOKING_CODE
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

session = Session()


class SummaryDriver:

    def __init__(self):
        self._CM = ConfigManager()
        self._AA = None
        self._PA = None
        self._BR = None
        self._search_results = SearchResults()
        self._result = Result()

    def create_summary(self, summary_type, te_rows=None) -> Result:
        account_bban = get_BBAN_from_IBAN(self._CM.get_config_item(CF_IBAN, EMPTY))
        year = self._CM.get_config_item(CF_SUMMARY_YEAR, 0)
        month_from = self._CM.get_config_item(CF_SUMMARY_MONTH_FROM, 0)
        month_to = self._CM.get_config_item(CF_SUMMARY_MONTH_TO, 0)

        try:
            # A. Search results
            if summary_type == Summary.SearchResult:
                return self._search_results.create_summary(te_rows, title=SEARCH_RESULT)

            # B. Annual account
            elif summary_type == Summary.AnnualAccount:
                self.produce_csv_files(TEMPLATE_ANNUAL_ACCOUNT, account_bban, year)

            # B. Periodical account
            elif summary_type == Summary.PeriodicAccount:
                self.produce_csv_files(PERIODIC_ACCOUNTS, account_bban, year, month_from, month_to)

            # B. Annual account Plus
            elif summary_type == Summary.AnnualAccountPlus:
                self.produce_csv_files(TEMPLATE_ANNUAL_ACCOUNT, account_bban, year)
                self.produce_csv_files(TEMPLATE_RESULTS_PER_BOOKING_CODE, account_bban, year)
                self.produce_csv_files(PERIODIC_ACCOUNTS, account_bban, year, 1, 12)

        except GeneralException as e:
            self._result.add_message(e.message, severity=MessageSeverity.Error)

        return self._result

    def produce_csv_files(self, template_name=None, account_bban=None, year=None, month_from=0, month_to=0):
        """
        Also called via pm.py, so should contain all parameters.
        """
        self._result = Result()
        prefix = f'{template_name} overzichten zijn NIET gemaakt.'

        # Validation
        self._required_parm(prefix, TEMPLATE_NAME, template_name)
        self._required_parm(prefix, YEAR, year)
        self._required_parm(prefix, ACCOUNT_NUMBER, account_bban)
        if not self._result.OK:
            return

        # "Jaarrekening t/m maand x"
        if template_name == TEMPLATE_ANNUAL_ACCOUNT:
            self._AA = AnnualAccount(account_bban)
            self._result = self._AA.export(account_bban, year)

        elif template_name == TEMPLATE_RESULTS_PER_BOOKING_CODE:
            self._BR = ResultsPerBookingCode(account_bban)
            self._result = self._BR.export(account_bban, year)

        # Periodic summary
        elif template_name == PERIODIC_ACCOUNTS:
            # Validation
            self._required_parm(prefix, MONTH_FROM, month_from)
            self._required_parm(prefix, MONTH_TO, month_to)
            if not self._result.OK:
                return

            # Export
            opening_balance = self._CM.get_config_item(CF_SUMMARY_OPENING_BALANCE, 0.0)
            self._PA = PeriodicAccount(account_bban, opening_balance)
            self._PA.export(account_bban, year, month_from, month_to)

            # Completion message
            self._result.add_message(f'{self._PA.export_count} {PERIODIC_ACCOUNTS} zijn geëxporteerd naar '
                                     f'"{session.export_dir}"')

    def _required_parm(self, prefix, name, value):
        if not value:
            self._result.add_message(f'{prefix} "{name}" is niet opgegeven.', severity=MessageSeverity.Error)
