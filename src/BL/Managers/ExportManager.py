from datetime import datetime

from src.DL.Config import CF_COMMA_REPRESENTATION_DISPLAY
from src.DL.IO.AnnualAccountIO import AnnualAccountIO
from src.DL.IO.TransactionIO import TransactionIO
from src.DL.Lexicon import CSV_FILE
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EXT_CSV, JAARREKENING, EMPTY
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'ExportManager'

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
csvm = CsvManager()
CM = ConfigManager()
session = Session()
BKM = BookingCache()

comma_target = CM.get_config_item(CF_COMMA_REPRESENTATION_DISPLAY)

TPL_HEADER = 'header'
TPL_BODY = 'body'
TPL_FOOTER = 'footer'

SUBGROUP = 'SUBGROUP'
# Singular
YEAR = 'JAAR'
YEAR_PREVIOUS = 'VORIG JAAR'

VAR_SINGULAR_DESC = {
    YEAR: 'Jaar',
    YEAR_PREVIOUS: 'Vorig jaar'
}
# Plural
TYPES = 'TYPEN'
MAINGROUPS = 'HOOFDGROEPEN'
SUBGROUPS = 'SUBGROEPEN'
AMOUNTS = 'BEDRAGEN'
GENERAL = 'GENERAAL'

# Plural totals (used in processing)
TOTAL = 'TOTAAL'
TOTAL_GENERAL = f'TOTAAL {GENERAL}'
TOTAL_TYPE = f'TOTAAL {TYPES}'
TOTAL_MAINGROUP = f'TOTAAL {MAINGROUPS}'

VAR_NAMES_SINGULAR = [YEAR, YEAR_PREVIOUS]
VAR_NAMES_PLURAL = [TYPES, MAINGROUPS, SUBGROUPS, AMOUNTS]
VAR_NAMES_TOTAL = [TOTAL_TYPE, TOTAL_MAINGROUP, TOTAL_GENERAL]
VAR_NAMES_AMOUNTS = VAR_NAMES_TOTAL.copy()
VAR_NAMES_AMOUNTS.extend([AMOUNTS])


class Field:
    @property
    def template_var_name(self):
        return self._template_var_name

    @property
    def column_no(self):
        return self._column_no

    @property
    def value(self):
        return self._value

    @property
    def value_prv(self):
        return self._value_prv

    @property
    def same_value_count(self):
        return self._same_value_count

    """
    Setters
    """

    @value.setter
    def value(self, value):
        self._value = value

    @value_prv.setter
    def value_prv(self, value):
        self._value_prv = value

    @same_value_count.setter
    def same_value_count(self, value):
        self._same_value_count = value

    def __init__(self, name, value=None, column: int = 0):
        self._template_var_name = name
        self._value = value
        self._column_no = column
        # context
        self._value_prv = EMPTY
        self._same_value_count = 0


def get_total_label(var_name):
    return f'{TOTAL} {var_name}'


class ExportManager:
    def __init__(self):
        self._transaction_io = TransactionIO()
        self._template_name = str
        self._year = 0
        self._cell_count = 0
        self._r = 0
        self._c = 0
        self._r_c = {}
        self._template_rows = []
        self._row_fields = {}
        self._colno_current = 0
        self._out_rows = []
        self._out_row = []

        self._blank_lines = 0
        self._out_path = None
        self._total_amounts = {}  # amounts per level
        self._level_no = {}
        self._first = True
        self._c_first_amount = 3  # type, maingroup, subgroup, then amounts.

        self._annual_account_io = AnnualAccountIO()
        self._annual_budgets = {}
        self._budget_years = 0

    def export(self, template_name=JAARREKENING, year=datetime.now().year) -> Result:
        self._template_name = template_name
        self._year = int(year)

        # Process output template
        self._validate_template()
        self._analyze_template()
        # Merge generated realisation from db with annual budgets from 'Jaarrekening.csv'
        sorted_bookings = self._get_merged_bookings()

        # Output naar CSV
        self._out_path = f'{session.export_dir}{JAARREKENING} {year} tm maand {self._transaction_io.month_max}{EXT_CSV}'
        self._construct(sorted_bookings)
        return Result(text=f'De {JAARREKENING} van {year} is geëxporteerd naar "{self._out_path}"')

    """
    Validation
    """

    def _validate_template(self):
        # Validate template
        # - Existence
        dir_name = session.templates_dir
        path = f'{dir_name}{self._template_name}{EXT_CSV}'
        if not path:
            raise GeneralException(f'{CSV_FILE} "{path}" bestaat niet.')

        self._template_rows = csvm.get_rows(include_header_row=True, data_path=path, include_empty_row=True)
        # - Content of file
        if not self._template_rows:
            raise GeneralException(f'Bestand "{path}" is leeg.')

        # - Content of cells
        for row in self._template_rows:
            self._c = 0
            if all(cell == EMPTY for cell in row):
                self._blank_lines += 1
            else:
                for cell in row:
                    self._check_cell(cell)
                    self._c += 1
                self._blank_lines = 0
        self._r += 1

        # Convert pure variables to uppercase
        self._template_rows = [[self._var_to_upper(cell) for cell in row] for row in self._template_rows]

    def _check_cell(self, cell):
        # Syntax check
        if not cell:
            return
        if '"' in cell:
            if not cell.startswith('"') or not cell.endswith('"'):
                raise GeneralException(f'{self._get_prefix()}Waarde "{cell}" begint of eindigt niet met een """ ')
        elif not cell.startswith('{'):
            raise GeneralException(f'{self._get_prefix()}Waarde "{cell}" begint  niet met een "{{".')
        elif not cell.endswith('}'):
            raise GeneralException(f'{self._get_prefix()}Waarde "{cell}" eindigt niet met een "}}".')
        # Comment
        s = cell.find('{')
        if s == -1:
            return
        # Do the variable names exist?
        count = 0
        while count < 100 and cell.find('{', s) > -1:
            count += 1
            s += 1
            e = cell.find('}', s)
            var_name = cell[s:e]
            # Amounts can be present multiple times. Remember only the 1st occurrence.
            var_name_uc = var_name.upper()
            if var_name_uc in self._r_c:
                continue
            # New var_name
            if var_name_uc not in (VAR_NAMES_SINGULAR + VAR_NAMES_PLURAL + VAR_NAMES_TOTAL):
                raise GeneralException(f'{self._get_prefix()}Variabele "{var_name}" wordt niet ondersteund.')
            if cell.startswith('"') and var_name_uc not in VAR_NAMES_SINGULAR:
                raise GeneralException(
                    f'{self._get_prefix()}Plural variabele "{var_name}" wordt niet ondersteund in een tekst.')
            self._r_c[var_name_uc] = (self._r, self._c, self._blank_lines)
            s = e + 1

    def _get_prefix(self):
        return f'Fout in regel {self._r + 1} kolom {self._c + 1}: '

    """
    Definition
    """

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
            elif all((cell[1:-1] in VAR_NAMES_SINGULAR) for cell in row if cell != EMPTY):
                self._out_rows.append([self._substitute_singular_var(cell) for cell in row])
                self._out_row_ignored = False

            # e. List rows = Row with only plural vars (columns)
            # Remember row (=column header). Level break = when blank line or totals
            elif all((cell[1:-1] in VAR_NAMES_PLURAL) for cell in row if cell != EMPTY):
                [self._add_field(row[c], c) for c in range(len(row))]
                self._out_row_ignored = True
            else:
                raise GeneralException(
                    f'Fout in regel {self._r}: Gemengde meervoudige en enkelvoudige variabelen in een regel '
                    f'worden niet ondersteund.')

    @staticmethod
    def _var_to_upper(cell) -> str:
        return cell.upper() if cell.startswith('{') else cell

    def _add_field(self, cell, column):
        """ 0-based row/col """
        if not cell:
            return
        self._row_fields[self._c] = Field(cell[1:-1], column=column)
        self._c += 1

    def _substitute_vars_in_text(self, cell) -> str:
        """ N.B. Cell has been validated already. """
        if not cell:
            return EMPTY
        cell = cell[1:-1]  # Remove apostrophes
        s = cell.find('{')
        if s > -1:
            count = 0
            while count < 100 and cell.find('{', s) > -1:
                count += 1
                e = cell.find('}', s)
                cell = self._substitute_var_in_text(cell, s, e + 1)
                s = s + 1
        return cell

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

    def _substitute_var_in_text(self, cell, s, e) -> str:
        var = cell[s + 1:e - 1].upper()
        if var == YEAR:
            cell = f'{cell[:s]}{self._year}{cell[e:]}'
        return cell


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
        amounts_realisation = {BKM.get_lk(r[0], r[1], r[2]): r for r in realisation_rows}
        amounts_budget = {BKM.get_lk(r[0], r[1], r[2]): r for r in budget_rows}
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
            {lk: BKM.get_seqno_from_lk(lk) for lk in amounts}.items(), key=lambda x: x[1])]
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
                f'{PGM}: Er is niets te doen. Er zijn geen transacties in de database gevonden.')

        col_count = len(sorted_bookings[0])
        if col_count != len(self._row_fields):
            # Coulance. "Jaarrekening.csv" is leading in no. of amounts. Amounts start at column 4.
            if col_count >= 4:
                row_fields = {i: self._row_fields[i] for i in range(4)}
                self._row_fields = row_fields
            else:
                raise GeneralException(
                    f'{PGM}: Aantal boeking kolommen ({col_count}) '
                    f'is ongelijk aan template kolommen ({len(self._row_fields)})')

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

        for F in self._row_fields.values():
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
        total_general = round(self._total_amounts[GENERAL][0], 2)
        self._x_check(self._transaction_io.total_amount, total_general, 'Export naar CSV')

    @staticmethod
    def _x_check(total_amount_db, total_amount_processed, step_name):
        amount_processed = round(total_amount_processed, 2)
        amount_db = round(total_amount_db, 2)
        if amount_processed != amount_db:
            raise GeneralException(
                f'Totaal realisatie bedrag verwerkt in stap "{step_name}" is {amount_processed}.\n'
                f'Totaal realisatie bedrag in de mutaties is {amount_db}.\n'
                f'Het verschil is {round(amount_db - amount_processed, 2)}.')

    def _initialize_totals(self) -> list:
        return [0.0 for _ in range(self._c_first_amount, len(self._row_fields))]

    def _add_data_row(self, data_row):
        """
        E.g. data_row = condensed Transaction row =
            [myType, myMaingroup, mySubgroup, myAmountRealisation, myAmountBudget, ...]
        """

        # Level break
        self._lb_fields = {c: F for c, F in self._row_fields.items() if c < self._c_first_amount - 1}

        # Set the new values
        for c, F in self._row_fields.items():
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
            for level_name, amounts in self._total_amounts.items():  # Per level (general, type, maingroup)
                self._total_amounts[level_name][j] += amount_db  # Per amount (real., budget, ...)

        # Format and add the last columns (subgroup, amounts).
        [self._format_and_add_value(F.template_var_name, F.value)
         for c, F in self._row_fields.items()
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

    def _format_and_add_value(self, var_name, value=None, write=False):
        """ Also add optional empty columns """
        # Output empty columns
        colno_varname = self._r_c[var_name][1]
        [self._add_cell(EMPTY) for _ in range(colno_varname - self._colno_current)]

        # Format and output the value
        self._add_cell(self._format_amount(var_name, value))

        # Output the row
        if write:
            self._add_row(var_name)

    def _format_and_add_total_row(self, level_name, total_label=EMPTY):
        """ Also add optional empty columns """
        var_name = get_total_label(level_name)
        values = self._total_amounts[level_name]

        # Output empty columns
        [self._add_cell(EMPTY) for _ in range(self._r_c[AMOUNTS][1] - 1)]

        # Output total label
        self._add_cell(
            TOTAL_GENERAL.title() if level_name == GENERAL
            else total_label.title())

        # Format and output the total values
        [self._add_cell(self._format_amount(var_name, values[i])) for i in range(len(values))]

        # Output the total row
        self._add_row(var_name)
        level_no = self._level_no[level_name]

        # Initialize totals (real., budget, ...)
        for name, no in self._level_no.items():
            if no >= max(level_no, 1):  # Do not clear General total
                self._total_amounts[name] = self._initialize_totals()

    @staticmethod
    def _format_amount(var_name, value) -> str:
        """ If it is an amount (realisation, budget), format and total it."""
        if var_name in VAR_NAMES_AMOUNTS:
            value = round(value, 2)
            if comma_target == ',':
                value = str(value).replace('.', ',')
        return value

    def _add_cell(self, value):
        self._out_row.append(value)
        self._colno_current += 1
        self._first = False

    def _add_row(self, var_name=None):
        # Blank lines before
        if var_name and var_name in self._r_c:
            self._add_empty_rows(self._r_c[var_name][2])
        # Add row
        self._out_rows.append(self._out_row)
        # Initialize row
        self._out_row = []
        self._colno_current = 0
        # Blank line after
        if var_name and var_name.startswith(TOTAL):
            self._add_empty_rows(1)

    def _add_empty_rows(self, count):
        [self._out_rows.append([EMPTY]) for _ in range(count)]
