#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

from datetime import datetime

from src.BL.Summary.SummaryBase import SummaryBase
from src.DL.Report import *
from src.DL.Lexicon import TRANSACTIONS
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EXT_CSV
from src.GL.Enums import MessageSeverity, ActionCode
from src.GL.Functions import is_valid_file
from src.GL.Result import Result
from src.GL.Validate import isFilename

csvm = CsvManager()


class SearchResults(SummaryBase):

    def __init__(self):
        super().__init__()
        self._session = Session()

        self._dialog = None
        if not self._session.CLI_mode:
            from src.VL.Views.PopUps.PopUp import PopUp
            self._dialog = PopUp()

    def create_summary(self, te_rows, title=None) -> Result:
        super().create_summary(te_rows[1:])
        if not self._result.OK:
            return self._result

        self._report = Report(Report.CsvExport)

        # Get file name
        file_name = f'{datetime.now().strftime("%Y-%m-%d")} - {title}' if title else \
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]} - *NO TITLE'
        # - CLI mode
        if not self._session.CLI_mode:
            from src.VL.Views.PopUps.Input import Input
            file_name = Input((200, 200)).get_input(
                label='Naam bestand',
                dft=file_name,
                unit_test=self._session.unit_test
            )
        data_path = f'{self._session.export_dir}{file_name}{EXT_CSV}'
        if self._validate_filename(file_name, data_path):
            return self._export_search_result(data_path)
        return Result()

    def _validate_filename(self, input_value, path) -> bool:
        if not isFilename(input_value):
            return False
        # CLI mode
        if not self._dialog:
            return True
        # Dialog mode
        self._dialog.relative_location = (-100, -100)
        if is_valid_file(path) and not self._dialog.confirm(
                popup_key=f'{PGM}.validate_filename', text='Bestand bestaat al. Vervangen?'):
            self._result = Result(action_code=ActionCode.Cancel)
            return False
        return True

    def _export_search_result(self, data_path) -> Result:
        self._map_db_rows_to_report(derived_names=[FD.Booking_code, FD.Booking_type, FD.Booking_id], period_name=None)
        csvm.write_rows(self._formatted_rows, data_path=data_path, open_mode='w')
        return Result(text=f'De {TRANSACTIONS} zijn geëxporteerd naar "{data_path}".',
                      severity=MessageSeverity.Completion)

    def _get_period(self, date) -> int or None:
        return EMPTY
