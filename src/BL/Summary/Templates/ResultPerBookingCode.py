from datetime import datetime

from src.BL.Functions import get_summary_filename
from src.BL.Summary.SummaryBase import csvm, BCM
from src.BL.Summary.Templates.Enums import DetailTotalVars
from src.BL.Summary.Templates.TemplateBase import TemplateBase
from src.DL.DBDriver.Att import Att
from src.DL.Lexicon import TRANSACTIONS, REALISATION, TEMPLATE_REALISATION_PER_BOOKING_CODE
from src.DL.Model import FD
from src.GL.Const import EMPTY
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'ResultPerBookingCode'

# noinspection SpellCheckingInspection
"""
----------------------------------------------------------------------------------------------
EXAMPLE:
----------------------------------------------------------------------------------------------
"Realisatie {jaar} {rekening naam} per boekingscode"		

    "Boekingscode"	"Realisatie"

    {boeking codes}	{bedragen}
        
        {totaal generaal}
----------------------------------------------------------------------------------------------
"""


class ResultsPerBookingCode(TemplateBase):
    def __init__(self, iban, template_filename, CLI_mode=False):
        super().__init__(iban, template_filename, CLI_mode)
        self._total_amounts = {}  # amounts per level
        self._level_no = {}
        self._first = True
        self._c_first_amount = 1  # type, maingroup, subgroup, then amounts.

    def export(self, year=None, month_from=1, month_to=12) -> Result:
        super().export(year, month_from, month_to)
        self._year = int(year) if year else int(datetime.now().year)

        # Process output template
        self._analyze_template()

        # Get transactions
        transactions = self._transactions_io.get_transactions(
            self._iban, self._year, month_from, month_to, order_by=[[Att(FD.Booking_code), 'ASC']])

        # Filename example: "Jaarrekening (templateX) 2024 tm maand 4.csv"
        filename = get_summary_filename(self._template_filename, self._year, self._transactions_io.month_max, )
        self._out_path = f'{self._session.export_dir}{filename}'

        # Output naar CSV.
        self._construct(transactions)

        # Wrap up
        if self._result.OK:
            self._export_count = 1
            return Result(
                text=f'De {TEMPLATE_REALISATION_PER_BOOKING_CODE} van {self._year} is geëxporteerd naar '
                     f'"{self._out_path}"')
        return self._result

    """
    Construction
    """

    def _construct(self, te_sorted_on_booking_code):
        """
        N.B. Out rows are already been filled with header rows.
        fields = {seqNo: Field}
        """
        super()._construct(te_sorted_on_booking_code)

        # Preparation
        self._total_amounts = {DetailTotalVars.General: [0.0]}

        # Detail rows
        [self._add_data_row(row) for row in self._condense(te_sorted_on_booking_code)]

        # General total
        self._format_and_add_total_row(DetailTotalVars.General)

        # Write CSV
        csvm.write_rows(self._out_rows, data_path=self._out_path, open_mode='w')

        # Check-check-double-check
        total_general = round(self._total_amounts[DetailTotalVars.General][0], 2)
        self._x_check(self._transactions_io.total_amount, total_general, 'Export naar CSV')

    def _condense(self, sorted_rows) -> list:
        """ [BookingCode, BookingDescription, Amount] """
        d = self._te_def
        booking_code_prv, booking_desc_prv, booking_seqno_prv = EMPTY, EMPTY, 0
        amount_prv = 0.0
        out_rows = []

        for row in sorted_rows:
            booking_code = row[d[FD.Booking_code]]
            booking_desc = BCM.get_value_from_booking_code(booking_code, FD.Booking_description)
            booking_seqno = BCM.get_value_from_booking_code(booking_code, FD.SeqNo)
            amount = row[d[FD.Amount_signed]]
            self._total_amounts[DetailTotalVars.General][0] += amount
            # level break
            if booking_code != booking_code_prv:
                out_rows.append([booking_code_prv, booking_desc_prv, amount_prv, booking_seqno_prv])
                amount_prv = 0.0
            # Set new values
            amount_prv += amount
            booking_code_prv = booking_code
            booking_desc_prv = booking_desc
            booking_seqno_prv = booking_seqno
        # Last time
        if amount_prv != 0.0:
            out_rows.append([booking_code_prv, booking_desc_prv, amount_prv, booking_seqno_prv])

        col_count = len(out_rows[0]) - 1  # SeqNo is derived
        if col_count != len(self._column_fields):
            raise GeneralException(
                f'{PGM}: Aantal data kolommen ({col_count}) '
                f'is ongelijk aan template kolommen ({len(self._column_fields)})')
        return sorted(out_rows, key=lambda x: x[3])

    @staticmethod
    def _x_check(total_amount_db, total_amount_processed, step_name=None):
        amount_processed = round(total_amount_processed, 2)
        amount_db = round(total_amount_db, 2)
        if amount_processed != amount_db:
            raise GeneralException(
                f'Totale {REALISATION} verwerkt in stap "{step_name}" is {amount_processed}.\n'
                f'Totale {REALISATION} in de {TRANSACTIONS} is {amount_db}.\n'
                f'Het verschil is {round(amount_db - amount_processed, 2)}.')

    def _add_data_row(self, data_row):
        # Set, format and add the columns.
        [self._format_and_add_value(F.template_var_name, data_row[c]) for c, F in self._column_fields.items()]

        # Output the row
        self._add_row()
