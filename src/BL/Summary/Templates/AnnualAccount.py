from datetime import datetime

from src.BL.Functions import get_annual_account_filename
from src.BL.Summary.SummaryBase import BCM, session, csvm
from src.BL.Summary.Templates.Const import *
from src.BL.Summary.Templates.TemplateBase import TemplateBase, get_total_label
from src.DL.IO.AnnualAccountIO import AnnualAccountIO
from src.DL.Lexicon import ANNUAL_ACCOUNT, TRANSACTIONS, REALISATION
from src.GL.Const import EMPTY
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'AnnualAccount'

# noinspection SpellCheckingInspection
"""
----------------------------------------------------------------------------------------------
EXAMPLE:
----------------------------------------------------------------------------------------------
"Realisatie {jaar} wijkgemeente Leiden Zuidwest"			
            "Realisatie"    "Begroting" "Begroting"  
            {jaar}  {jaar}  {vorigjaar}
{typen}			
    {hoofdgroepen}		
        {subgroepen}	{bedragen}

            {totaal hoofdgroep}

            {totaal type}

            {totaal generaal}
----------------------------------------------------------------------------------------------
"""


class AnnualAccount(TemplateBase):
    def __init__(self):
        super().__init__()


        self._total_amounts = {}  # amounts per level
        self._level_no = {}
        self._first = True
        self._c_first_amount = 3  # type, maingroup, subgroup, then amounts.

        self._annual_account_io = AnnualAccountIO()
        self._annual_budgets = {}
        self._budget_years = 0

    def export(self, template_name=None, year=None, month_from=None, month_to=None) -> Result:
        self._template_name = ANNUAL_ACCOUNT
        self._year = int(year) if year else int(datetime.now().year)
        # Process output template
        self._validate_template()
        self._analyze_template()

        # Merge generated realisation from db with annual budgets from 'Jaarrekening.csv'
        sorted_bookings = self._get_merged_bookings()

        # Output naar CSV.
        # Filename example: "Jaarrekening (templateX) 2024 tm maand 4.csv"
        filename = get_annual_account_filename(self._year, self._transaction_io.month_max, title=template_name)
        self._out_path = f'{session.export_dir}{filename}'
        self._construct(sorted_bookings)
        return Result(text=f'De {ANNUAL_ACCOUNT} van {self._year} is geëxporteerd naar "{self._out_path}"') \
            if self._result.OK else self._result

    def _substitute_singular_var(self, cell) -> str:
        """ N.B. Cell has been validated already. """
        if not cell:
            return EMPTY
        var = cell[1:-1]  # Remove {}
        if var == YEAR:
            return str(self._year)
        elif var == YEAR_PREVIOUS:
            return str(self._year - 1)
        elif var in VAR_SINGULAR_DESC:
            return VAR_SINGULAR_DESC[var]
        else:
            return f'{cell} (*UNSUPPORTED*)'

    def _analyze_template(self):
        """ Precondition: file syntax has been validated. Variables are in UC. """
        self._r = -1
        self._c = 0
        self._out_row_ignored = False

        for row in self._template_rows:
            self._r += 1

            # a. Blank row (only if output has not been ignored for now, e.g. do not print blank lines between totals)
            if all(cell == EMPTY for cell in row):
                if not self._out_row_ignored:
                    self._out_rows.append(row)
                continue

            # b. Title row
            if all((cell == EMPTY or cell.startswith('"')) for cell in row):
                self._out_rows.append([self._substitute_vars_in_text(cell) for cell in row])
                self._out_row_ignored = False

            # c. Ignore totals
            elif all(TOTAL in (cell[1:-1]) for cell in row if cell != EMPTY):
                self._out_row_ignored = True

            # d. List column headings = Row with only singular variables
            elif all((cell[1:-1] in VAR_NAMES_HEADER) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                self._out_rows.append([self._substitute_singular_var(cell) for cell in row])
                self._out_row_ignored = False

            # e. List rows = Row with only plural vars (columns)
            # Remember row (=column header). Level break = when blank line or totals
            elif all((cell[1:-1] in VAR_NAMES_DETAIL) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                [self._add_column_field(row[c], c) for c in range(len(row))]
                self._out_row_ignored = True
            else:
                raise GeneralException(
                    f'Fout in regel {self._r}: Gemengde meervoudige en enkelvoudige variabelen in een regel '
                    f'worden niet ondersteund.')


    """
    Construction
    """

    def _get_merged_bookings(self) -> list:
        """ Add budget booking columns to realisation """
        realisation_rows = self._transaction_io.get_realisation_data(self._year)
        if not realisation_rows:
            return []

        total_amount = sum(row[3] for row in realisation_rows)
        self._x_check(self._transaction_io.total_amount, total_amount, 'Ophalen Realisatie data')

        budget_rows = self._annual_account_io.get_annual_budget_data(self._year - 1)
        self._budget_years = max(len(budget_rows[0]) - self._c_first_amount, 0) if budget_rows else 0

        # Merge on type, maingroup, subgroup.
        amounts_realisation = {BCM.get_lk(r[0], r[1], r[2]): r for r in realisation_rows}
        amounts_budget = {BCM.get_lk(r[0], r[1], r[2]): r for r in budget_rows}
        amounts = {}

        # If realisation booking has budget amount(s): Add budget amount(s) next to realisation amount
        a1 = self._c_first_amount
        for lk, v in amounts_realisation.items():
            budget_amounts = amounts_budget[lk][a1:] if lk in amounts_budget else []
            amounts[lk] = self._get_budget_amounts(v[a1], budget_amounts)

        # If budget-booking not in realisation-bookings: Add budget booking and amount(s) with realisation amount = 0.0
        for lk, v in amounts_budget.items():
            if lk not in amounts_realisation:
                amounts[lk] = self._get_budget_amounts(0.0, amounts_budget[lk][a1:])

        # Sort bookings by booking seqno
        lk_by_seqno = [item[0] for item in sorted(
            {lk: BCM.get_seqno_from_lk(lk) for lk in amounts}.items(), key=lambda x: x[1])]
        sorted_bookings = [self._get_booking_row(lk, amounts[lk]) for lk in lk_by_seqno]

        # X-check
        total_amount = sum(row[3] for row in sorted_bookings)
        self._x_check(self._transaction_io.total_amount, total_amount, 'Merge Realisatie en Budget')

        return sorted_bookings

    @staticmethod
    def _get_booking_row(lk: str, amounts: list) -> list:
        row = lk.split('|')
        row.extend(amounts)
        return row

    def _get_budget_amounts(self, realisation_amount: float, budget_amounts: list):
        if not budget_amounts:
            budget_amounts = [0.0 for _ in range(self._budget_years)]
        row = [realisation_amount]
        row.extend(budget_amounts)
        return row

    def _construct(self, sorted_bookings):
        """
        N.B. Out rows are already been filled with title.
        fields = {seqNo: Field}
        """
        if not sorted_bookings:
            raise GeneralException(
                f'{PGM}: Er is niets te doen. Er zijn geen transacties in de database gevonden '
                f'(voor jaar {self._year}).')

        col_count = len(sorted_bookings[0])
        if col_count != len(self._column_fields):
            # Coulance. "Jaarrekening.csv" is leading in no. of amount columns. Amounts start at column 4.
            if col_count >= 4:
                col_max = min(col_count, len(self._column_fields))
                column_fields = {i: self._column_fields[i] for i in range(col_max)}
                self._column_fields = column_fields
            else:
                raise GeneralException(
                    f'{PGM}: Aantal boeking kolommen ({col_count}) '
                    f'is ongelijk aan template kolommen ({len(self._column_fields)})')

        # Preparation
        self._total_amounts = {
            GENERAL: self._initialize_totals(),
            TYPES: self._initialize_totals(),
            MAINGROUPS: self._initialize_totals()
        }
        self._level_no = {
            GENERAL: 0,
            TYPES: 1,
            MAINGROUPS: 2
        }

        for F in self._column_fields.values():
            F.value_prv = EMPTY
            F.same_value_count = 0

        # Add data (with level breaks)
        [self._add_data_row(row) for row in sorted_bookings]
        # Last time
        self._add_totals(last=True)

        # General total
        # Format and add only the amounts.
        self._format_and_add_total_row(GENERAL)
        self._add_row(TOTAL_GENERAL)

        # Write CSV
        csvm.write_rows(self._out_rows, data_path=self._out_path, open_mode='w')

        # Check-check-double-check
        if self._total_amounts[GENERAL]:
            total_general = round(self._total_amounts[GENERAL][0], 2)
            self._x_check(self._transaction_io.total_amount, total_general, 'Export naar CSV')

    @staticmethod
    def _x_check(total_amount_db, total_amount_processed, step_name=None):
        amount_processed = round(total_amount_processed, 2)
        amount_db = round(total_amount_db, 2)
        if amount_processed != amount_db:
            raise GeneralException(
                f'Totale {REALISATION} verwerkt in stap "{step_name}" is {amount_processed}.\n'
                f'Totale {REALISATION} in de {TRANSACTIONS} is {amount_db}.\n'
                f'Het verschil is {round(amount_db - amount_processed, 2)}.')

    def _initialize_totals(self) -> list:
        return [0.0 for _ in range(self._c_first_amount, len(self._column_fields))]

    def _add_data_row(self, data_row):
        """
        E.g. data_row = condensed Transaction row =
            [myType, myMaingroup, mySubgroup, myAmountRealisation, myAmountBudget, ...]
        """

        # Level break
        self._lb_fields = {c: F for c, F in self._column_fields.items() if c < self._c_first_amount - 1}

        # Set the new values
        for c, F in self._column_fields.items():
            F.value = data_row[c]

        # - Output totals of previous level (if > 1 printed)
        self._add_totals()

        # New level: Start the level = add level-title to the output
        for c, F in self._lb_fields.items():
            if self._is_level_break(c):
                self._format_and_add_value(F.template_var_name, F.value, write=True)
                F.value_prv = F.value
                F.same_value_count = 0
            else:
                F.same_value_count += 1

        # Format and add data values
        """
        Add only last 2 cells.
        Precondition: Last data row cell contains the amount.
        Example:
            {SUBGROUP: 'Levend geld',
             BEDRAG: 15.25}
        """

        # Sum realisation totals per [type, maingroup, general]
        for i in range(self._c_first_amount, len(data_row)):
            amount_db = data_row[i]
            j = i - self._c_first_amount
            # For this column i
            for level_name, amounts in self._total_amounts.items():
                if j in self._total_amounts[level_name]:  # Per level (general, type, maingroup)
                    self._total_amounts[level_name][j] += amount_db  # Per amount (real., budget, ...)

        # Format and add the last columns (subgroup, amounts).
        [self._format_and_add_value(F.template_var_name, F.value)
         for c, F in self._column_fields.items()
         if c > 1]

        # Output the row
        self._add_row()

    def _is_level_break(self, column) -> bool:
        return self._lb_fields[column].value != self._lb_fields[column].value_prv

    def _add_totals(self, last=False):
        """
         From least to most significant level-break, write a total (if > 1 row was printed).
         E.g. first for maingroup, then type.
         """
        for c in sorted(self._lb_fields.keys(), reverse=True):
            level_name = self._lb_fields[c].template_var_name  # TYPES, MAINGROUPS
            total_label = get_total_label(self._lb_fields[c].value_prv)
            # If the total is not in the template, it is not printed.
            if (self._is_level_break(c) and self._lb_fields[c].same_value_count > 0) or last:
                self._format_and_add_total_row(level_name, total_label)

    def _format_and_add_total_row(self, level_name, total_label=EMPTY):
        """ Also add optional empty columns """
        var_name = get_total_label(level_name)
        values = self._total_amounts[level_name]

        if var_name in self._template_var_names:

            # Output empty columns
            [self._output_cell(EMPTY) for _ in range(self._r_c[AMOUNTS][1] - 1)]

            # Output total label
            self._output_cell(TOTAL_GENERAL.title() if level_name == GENERAL else total_label.title())

            # Format and output the total values
            [self._output_cell(self._format_amount(values[i])) for i in range(len(values))]

            # Output the total row
            self._add_row(var_name)

        # Initialize totals (real., budget, ...)
        level_no = self._level_no[level_name]
        for name, no in self._level_no.items():
            if no >= max(level_no, 1):  # Do not clear General total
                self._total_amounts[name] = self._initialize_totals()