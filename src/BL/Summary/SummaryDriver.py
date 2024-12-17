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
from src.BL.Summary.Templates.ResultPerBookingCode import ResultsPerBookingCode
from src.Base import Base
from src.DL.Config import CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_MONTH_TO, \
    CF_SUMMARY_OPENING_BALANCE
from src.DL.Enums.Enums import Summary
from src.DL.IO.OpeningBalanceIO import OpeningBalanceIO
from src.DL.Lexicon import TEMPLATE_ANNUAL_ACCOUNT, SEARCH_RESULT, YEAR, \
    TEMPLATE_NAME, TEMPLATE_PERIODIC_ACCOUNT, TEMPLATE_REALISATION_PER_BOOKING_CODE, MONTH_FROM, MONTH_TO, SUMMARY, \
    SUMMARIES
from src.GL.Enums import MessageSeverity
from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result


class SummaryDriver(Base):

    def __init__(self):
        super().__init__()
        self._AA = None
        self._PA = None
        self._BR = None
        self._search_results = SearchResults()
        self._result = Result()
        self._summary_type = None
        self._template_filenames = {}
        self._CLI_mode = False

    def create_summary(self, summary_type, te_rows=None, template_filenames=None, iban=None, CLI_mode=False) -> Result:
        self._summary_type = summary_type
        self._template_filenames = template_filenames
        self._CLI_mode = CLI_mode
        self._result = Result()

        year = self._CM.get_config_item(CF_SUMMARY_YEAR, 0)
        month_from = self._CM.get_config_item(CF_SUMMARY_MONTH_FROM, 0)
        month_to = self._CM.get_config_item(CF_SUMMARY_MONTH_TO, 0)
        if not self._template_filenames:
            self._template_filenames = {
                Summary.AnnualAccount: TEMPLATE_ANNUAL_ACCOUNT,
                Summary.PeriodicAccount: TEMPLATE_PERIODIC_ACCOUNT,
                Summary.RealisationPerBookingCode: TEMPLATE_REALISATION_PER_BOOKING_CODE
            }

        try:
            export_count = 0
            # A. Search results
            if summary_type == Summary.SearchResult:
                return self._search_results.create_summary(te_rows, title=SEARCH_RESULT)

            # B. Annual account
            elif summary_type == Summary.AnnualAccount:
                export_count += self._produce_csv_files(summary_type, iban, year)

            # C. Periodical account
            elif summary_type == Summary.PeriodicAccount:
                export_count += self._produce_csv_files(summary_type, iban, year, month_from, month_to)

            # D. Annual account Plus
            elif summary_type == Summary.AnnualAccountPlus:
                export_count += self._produce_csv_files(Summary.AnnualAccount, iban, year)
                export_count += self._produce_csv_files(Summary.RealisationPerBookingCode, iban, year)
                export_count += self._produce_csv_files(Summary.PeriodicAccount, iban, year, 1, 12)

            # E. Realisation per booking code
            elif summary_type == Summary.RealisationPerBookingCode:
                export_count += self._produce_csv_files(Summary.RealisationPerBookingCode, iban, year)
            else:
                raise GeneralException(f'Overzicht "{summary_type}" wordt niet ondersteund.')

            # Completion
            prefix = f'{SUMMARY} is' if export_count == 1 else f'{export_count} {SUMMARIES} zijn'
            self._result.add_message(f'{prefix} geëxporteerd naar "{self._session.export_dir}"')

        except GeneralException as e:
            self._result.add_message(e.message, severity=MessageSeverity.Error)

        return self._result

    def _produce_csv_files(self, summary_type=None, iban=None, year=None, month_from=0, month_to=0) -> int:
        """
        Also called via pm.py and UT, so should contain all parameters.
        """
        export_count = 0
        summary_type = summary_type or self._summary_type
        self._result = Result()

        # Validation
        prefix = f'{summary_type} overzichten zijn NIET gemaakt.'

        template_filename = self._template_filenames.get(summary_type) if self._template_filenames else None
        self._required_parm(prefix, TEMPLATE_NAME, template_filename)
        self._required_parm(prefix, YEAR, year)
        if not self._result.OK:
            raise GeneralException(self._result.get_messages_as_message())

        # "Jaarrekening t/m maand x"
        if summary_type == Summary.AnnualAccount:
            self._AA = AnnualAccount(iban, template_filename, self._CLI_mode)
            self._result = self._AA.export(year)
            return self._AA.export_count

        elif summary_type == Summary.RealisationPerBookingCode:
            self._BR = ResultsPerBookingCode(iban, template_filename, self._CLI_mode)
            self._result = self._BR.export(year)
            return self._BR.export_count

        # Periodic summary
        elif summary_type == Summary.PeriodicAccount:
            # Validation
            self._required_parm(prefix, MONTH_FROM, month_from)
            self._required_parm(prefix, MONTH_TO, month_to)
            if not self._result.OK:
                return 0

            # Export
            if self._CLI_mode:
                opening_balance = OpeningBalanceIO().get_opening_balance(year)
            else:
                opening_balance = toFloat(self._CM.get_config_item(CF_SUMMARY_OPENING_BALANCE))

            self._PA = PeriodicAccount(iban, opening_balance, template_filename, self._CLI_mode)
            self._PA.export(year, month_from, month_to)
            return self._PA.export_count

    def _required_parm(self, prefix, name, value):
        if not value:
            self._result.add_message(f'{prefix} "{name}" is niet opgegeven.', severity=MessageSeverity.Error)
