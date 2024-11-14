#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Summary.SearchResults import SearchResults
from src.BL.Summary.Templates.AnnualAccount import AnnualAccount
from src.BL.Summary.Templates.PeriodicAccount import PeriodicAccount
from src.DL.Config import CF_COMBO_SUMMARY, CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_MONTH_TO, \
    CF_SUMMARY_OPENING_BALANCE
from src.DL.Enums.Enums import Summary
from src.DL.Lexicon import ANNUAL_ACCOUNT, SEARCH_RESULT, PERIODIC_ACCOUNTS
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Enums import MessageSeverity
from src.GL.Result import Result

session = Session()


class SummaryDriver:

    def __init__(self):
        self._CM = ConfigManager()
        self._AA = AnnualAccount()
        self._PA = None
        self._search_results = SearchResults()
        self._result = Result()

    def create_summary(self, summary_type, te_rows=None) -> Result:
        year = self._CM.get_config_item(CF_SUMMARY_YEAR, 0)
        month_from = self._CM.get_config_item(CF_SUMMARY_MONTH_FROM, 0)
        month_to = self._CM.get_config_item(CF_SUMMARY_MONTH_TO, 0)
        opening_balance = self._CM.get_config_item(CF_SUMMARY_OPENING_BALANCE, 0.0)

        # A. Search results
        if summary_type == Summary.SearchResult:
            return self._search_results.create_summary(te_rows, title=SEARCH_RESULT)

        # B. Annual account
        elif summary_type == Summary.AnnualAccount:
            self.produce_csv_files(ANNUAL_ACCOUNT, year)

        # B. Periodical account
        elif summary_type == Summary.PeriodicAccount:
            self._PA = PeriodicAccount(opening_balance)
            self.produce_csv_files(PERIODIC_ACCOUNTS, year, month_from, month_to)

        # B. Annual account Plus
        elif summary_type == Summary.AnnualAccountPlus:
            self._PA = PeriodicAccount(opening_balance)
            self.produce_csv_files(ANNUAL_ACCOUNT, year)
            self.produce_csv_files(PERIODIC_ACCOUNTS, year, month_from, month_to)
        return self._result

    def produce_csv_files(self, template_name=None, year=None, month_from=0, month_to=0):
        self._result = Result()
        prefix = f'{template_name} overzichten zijn NIET gemaakt.'
        if not year:
            self._result.add_message(f'{prefix} "Jaar" is niet opgegeven.', severity=MessageSeverity.Error)
            return

        # "Jaarrekening t/m maand x"
        if template_name == ANNUAL_ACCOUNT:
            self._result = self._AA.export(year)

        # Periodic summary
        elif template_name == PERIODIC_ACCOUNTS:
            # Validation
            if not month_from:
                self._result.add_message(
                    f'{prefix} "Maand vanaf" is niet opgegeven.', severity=MessageSeverity.Error)
                return
            if not month_to:
                self._result.add_message(
                    f'{prefix} "Maand t/m" is niet opgegeven.', severity=MessageSeverity.Error)
                return

            # Export
            self._PA.export(year, month_from, month_to)

            # Completion message
            self._result.add_message(f'{self._PA.export_count} {PERIODIC_ACCOUNTS} zijn geëxporteerd naar '
                                     f'"{session.export_dir}"')
