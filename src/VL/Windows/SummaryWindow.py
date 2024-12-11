#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-11-25 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Summary.SummaryDriver import SummaryDriver
from src.DL.Config import CF_COMBO_SUMMARY, CF_SUMMARY_YEAR, CF_SUMMARY_MONTH_FROM, CF_SUMMARY_OPENING_BALANCE
from src.DL.Enums.Enums import Summary
from src.DL.IO.OpeningBalanceIO import OpeningBalanceIO
from src.DL.Lexicon import SUMMARY
from src.GL.Enums import ResultCode
from src.GL.Functions import FloatToStr, maybeFloat
from src.GL.Result import Result
from src.VL.Data.Constants.Const import CMD_OK, CMD_CANCEL
from src.VL.Data.Constants.Enums import WindowType
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import get_name_from_key
from src.VL.Views.SummaryView import SummaryView
from src.VL.Windows.BaseWindow import BaseWindow


class SummaryWindow(BaseWindow):

    def __init__(self, te_rows):
        super().__init__('SummaryWindow', f'{SUMMARY} opties', WindowType.PopUp_with_statusbar)
        self._view = SummaryView()
        self._te_rows = te_rows
        self._summary_manager = SummaryDriver()
        self._OB_IO = OpeningBalanceIO()

    def _event_handler(self, event, values):
        # Set view in main window
        event_key = get_name_from_key(event)

        # Button clicks
        if event_key == CMD_OK:
            if not self._is_valid_input():
                return

            # Create summary
            self._result = self._summary_manager.create_summary(
                self._CM.get_config_item(CF_COMBO_SUMMARY),
                self._te_rows)
            return

        elif event_key == CMD_CANCEL:
            self._result = Result(ResultCode.Canceled)
            return

        elif event_key == CF_SUMMARY_YEAR:
            # Get the selected year
            year = int(self._CM.get_config_item(CF_SUMMARY_YEAR, 0))
            # Get/set the opening balance
            opening_balance = self._OB_IO.get_opening_balance(year)
            self._CM.set_config_item(CF_SUMMARY_OPENING_BALANCE,  FloatToStr(str(opening_balance)))
        return

    def _appearance_before(self):
        """ Dynamically format when typing."""
        # Jaar
        self._window[self.gui_key(CF_SUMMARY_YEAR, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) != Summary.SearchResult)
        # Maand vanaf en t/m
        self._window[self.gui_key(CF_SUMMARY_MONTH_FROM, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) == Summary.PeriodicAccount)
        # Begin saldo
        self._window[self.gui_key(CF_SUMMARY_OPENING_BALANCE, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) in (Summary.PeriodicAccount, Summary.AnnualAccountPlus)
        )
        # In Config amount is str.
        opening_balance = self._CM.get_config_item(CF_SUMMARY_OPENING_BALANCE)
        self._window[self.gui_key(CF_SUMMARY_OPENING_BALANCE, WTyp.IN)].update(value=opening_balance)

    def _is_valid_input(self) -> bool:
        summary_type = self._CM.get_config_item(CF_COMBO_SUMMARY)

        # Summary type
        if not summary_type:
            self._result = Result(ResultCode.Warning, f'Kies een soort {SUMMARY}.')
            return False

        if (summary_type in (
                Summary.AnnualAccount,
                Summary.AnnualAccountPlus,
                Summary.PeriodicAccount)):

            # Year
            if not self._CM.get_config_item(CF_SUMMARY_YEAR):
                self._result = Result(ResultCode.Warning, 'Kies een jaar.')
                return False

            # Opening balance
            amount = self._CM.get_config_item(CF_SUMMARY_OPENING_BALANCE)
            if not maybeFloat(amount):
                self._result = Result(ResultCode.Warning, f'"{amount}" is geen geldig bedrag.')
                return False
        return True
