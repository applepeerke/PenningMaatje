#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-08 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.Base import Base
from src.DL.Model import FD
from src.DL.Objects.Figure import Figure
from src.DL.Objects.TimelineItem import TimelineItem
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.Lexicon import TRANSACTIONS
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.Result import Result
from src.GL.Validate import isInt

csvm = CsvManager()
BCM = BookingCodeCache()

PGM = 'SummaryBase'


def transform_figures(figures: dict) -> dict:
    """ List to Figure """
    figures = {k: Figure(k, timeline) for k, timeline in figures.items()}
    return figures


def sanitize_value(item: TimelineItem) -> int:
    """ Budget rows may be all EMPTY instead of 0 if no occurrence like "Inkomsten" has been found. """
    return 0 if item.amount == EMPTY else item.amount


class SummaryBase(Base):

    def __init__(self):
        super().__init__()
        self._te_rows = []
        self._formatted_rows = []
        self._report = None
        self._out_def = {}
        self._c_booking_type = -1
        self._c_amount_signed = -1
        self._c_period = -1
        self._Id = False
        self._result = Result()

    def create_summary(self, te_rows) -> Result:
        """ Precondition: Transaction enriched rows include header """
        self._te_rows = te_rows
        # Validation
        if not self._te_rows or len(self._te_rows) < 2:
            return Result(text=f'Geen {TRANSACTIONS} gevonden.', severity=MessageSeverity.Completion)

    def _get_period(self, date):
        raise NotImplementedError(f'{PGM}: Method "_get_period" is not implemented.')

    def _map_db_rows_to_report(self, derived_names, period_name=None):
        """
        Format input: Table.TransactionEnriched.
        Format output: Report.CsvExport, filtered input columns, other names and order.
        Input names (atts) must be mapped to output names (atts).
        """
        # Report
        self._out_def = self._report.map_report_to_model(derived_names=derived_names)

        # Header
        if not self._Id:
            header = self._report.header_names
        else:
            header = ['ID']
            header.extend(self._report.header_names)

        # Add derived attributes booking-code and -type from booking-id
        # Header
        self._c_amount_signed = header.index(FD.Amount_signed)
        self._c_booking_id = header.index(FD.Booking_id)
        self._c_booking_code = header.index(FD.Booking_code)
        self._c_booking_type = header.index(FD.Booking_type)
        self._c_date = header.index(FD.Date)
        self._c_period = header.index(period_name) if period_name else -1
        self._x = []

        # Details
        self._formatted_rows = [header]
        # - Select values
        [self._add_formatted_row(te_row) for te_row in self._te_rows]

        # - Enrich values
        for row in self._formatted_rows[1:]:  # details
            # Booking code /type
            booking_id = row[self._c_booking_id]
            booking_code = BCM.get_value_from_id(booking_id, FD.Booking_code)
            booking_type = BCM.get_value_from_id(booking_id, FD.Booking_type)
            row[self._c_booking_code] = booking_code
            row[self._c_booking_type] = booking_type
            # Period
            period = self._get_period(row[self._c_date])
            if period:
                row[self._c_period] = period
                if period not in self._x:
                    self._x.append(period)
        # Remove FK
        [row.pop(self._c_booking_id) for row in self._formatted_rows]

    def _add_formatted_row(self, te_row):
        """ Add selected row attributes based on report definition. """
        # Id is used to check for completeness
        row = te_row[:1] if self._Id else []
        rest_row = [self._add_cell(te_row, att) for att in self._report.attributes]
        row.extend(rest_row)
        self._formatted_rows.append(row)

    def _add_cell(self, te_row, att):
        """
        @return: mapped te-row value
        Out_def = report-model mapping {report_att_name: model_att_no | EMPTY }
        """
        return te_row[self._out_def[att.name]] if isInt(self._out_def[att.name]) else EMPTY
