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
from src.VL.Data.Constants.Const import CMD_OK, CMD_CANCEL
from src.VL.Data.Constants.Enums import WindowType
from src.DL.Lexicon import SUMMARY
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import get_name_from_key
from src.VL.Views.SummaryView import SummaryView
from src.VL.Windows.BaseWindow import BaseWindow
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Enums import ResultCode
from src.GL.Result import Result


class SummaryWindow(BaseWindow):

    def __init__(self, te_rows):
        super().__init__('SummaryWindow', f'{SUMMARY} opties', WindowType.PopUp_with_statusbar)
        self._view = SummaryView()
        self._te_rows = te_rows
        self._CM = ConfigManager()
        self._summary_manager = SummaryDriver()

    def _event_handler(self, event, values):
        # Set view in main window
        event_key = get_name_from_key(event)

        # Button clicks
        if event_key == CMD_OK:
            summary_type = self._CM.get_config_item(CF_COMBO_SUMMARY)
            # Validation
            if not summary_type:
                self._result = Result(ResultCode.Warning, f'Kies een soort {SUMMARY}.')
                return
            if (summary_type in (Summary.AnnualAccount, Summary.AnnualAccountPlus, Summary.PeriodicAccount) and
                    not self._CM.get_config_item(CF_SUMMARY_YEAR)):
                self._result = Result(ResultCode.Warning, 'Kies een jaar.')
                return

            # Create summary
            self._result = self._summary_manager.create_summary(self._te_rows, summary_type)
            return
        elif event_key == CMD_CANCEL:
            self._result = Result(ResultCode.Canceled)
            return
        return

    def _appearance_before(self):
        # Jaar
        self._window[self.gui_key(CF_SUMMARY_YEAR, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) != Summary.SearchResult)
        # Maand vanaf en t/m
        self._window[self.gui_key(CF_SUMMARY_MONTH_FROM, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) == Summary.PeriodicAccount)
        # Begin saldo
        self._window[self.gui_key(CF_SUMMARY_OPENING_BALANCE, WTyp.FR)].update(
            visible=self._CM.get_config_item(CF_COMBO_SUMMARY) not in (Summary.SearchResult, Summary.AnnualAccount))
