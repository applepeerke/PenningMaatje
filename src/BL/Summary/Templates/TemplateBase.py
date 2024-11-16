import os.path

from src.BL.Summary.SummaryBase import SummaryBase, session, csvm
from src.BL.Summary.Templates.Const import *
from src.BL.Summary.Templates.TemplateField import TemplateField
from src.DL.Config import CF_COMMA_REPRESENTATION_DISPLAY
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Lexicon import CSV_FILE
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Const import EXT_CSV, EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.Functions import format_date
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'TemplateBase'
loop_count = 100

CM = ConfigManager()
comma_target = CM.get_config_item(CF_COMMA_REPRESENTATION_DISPLAY)

VAR_NAMES_MAP = {
    TYPES: FD.Booking_type,
    MAINGROUPS: FD.Booking_maingroup,
    SUBGROUPS: FD.Booking_subgroup,
    AMOUNTS: FD.Amount_signed,
    DATES: FD.Date,
    COSTS: FD.Amount_signed,
    REVENUES: FD.Amount_signed,
    DESCRIPTIONS: FD.Comments,
    BOOKING_CODES: FD.Booking_code,
    BOOKING_DESCRIPTIONS: FD.Booking_code  # Not in model, derived from code
}


def get_total_label(var_name):
    return f'{TOTAL} {var_name}'


class TemplateBase(SummaryBase):

    @property
    def result(self):
        return self._result

    @property
    def export_count(self):
        return self._export_count

    def __init__(self, account_bban, template_name):
        super().__init__()
        self._account_bban = account_bban
        self._template_name = template_name

        self._te_def = Model().get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
        self._transactions_io = TransactionsIO()
        self._template_var_names = set()
        self._column_fields = {}
        self._year = 0
        self._cell_count = 0
        self._template_rows = []
        self._out_rows = []
        self._out_row = []
        self._r = 0
        self._c = 0
        self._r_c = {}
        self._blank_lines = 0
        self._out_path = None
        self._colno_current = 0
        self._export_count = 0
        self._total_amounts = {}

        # Validate the template
        self._validate_template()

    def export(self, account_bban, year=None, month_from=None, month_to=None) -> Result:
        raise NotImplementedError

    def _construct(self, rows):
        raise NotImplementedError

    @staticmethod
    def _x_check(total_amount_db, total_amount_processed, step_name=None):
        raise NotImplementedError

    """
    Validation
    """

    def _validate_template(self):
        # Validate template
        # - Existence
        dir_name = session.templates_dir
        path = f'{dir_name}{self._template_name}{EXT_CSV}'
        if not os.path.isfile(path):
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

        if self._result.OK:
            # Convert pure variables to uppercase
            self._template_rows = [[self._var_to_upper(cell) for cell in row] for row in self._template_rows]
        else:
            raise GeneralException(self._result.get_messages_as_message())

    def _check_cell(self, cell):
        # Syntax check
        if not cell:
            return
        # - Comment
        if '"' in cell:
            if not cell.startswith('"') or not cell.endswith('"'):
                self._add_error(f'{self._get_prefix()}Waarde "{cell}" begint of eindigt niet met een """ ')
        # - Variable
        elif not cell.startswith('{'):
            self._add_error(f'{self._get_prefix()}Waarde "{cell}" begint  niet met een "{{".')
        elif not cell.endswith('}'):
            self._add_error(f'{self._get_prefix()}Waarde "{cell}" eindigt niet met een "}}".')

        # Comment without variables
        s = cell.find('{')
        if s == -1:
            return

        # Do the variable names exist?
        count = 0
        s = -1
        while count < loop_count:
            s = cell.find('{', s + 1)
            if s == -1:
                break
            count += 1
            e = cell.find('}', s)
            var_name = cell[s + 1:e]
            # Amounts can be present multiple times. Remember only the 1st occurrence.
            var_name_uc = var_name.upper()
            if var_name_uc in self._r_c:
                continue
            # New var_name
            if var_name_uc not in (VAR_NAMES_HEADER + VAR_NAMES_DETAIL + VAR_NAMES_DETAIL_TOTAL):
                self._add_error(f'{self._get_prefix()}Variabele "{var_name}" wordt niet ondersteund.')
            if cell.startswith('"') and var_name_uc not in VAR_NAMES_HEADER:
                self._add_error(
                    f'{self._get_prefix()}Kolom variabele "{var_name}" wordt niet ondersteund in een tekst.')
            self._r_c[var_name_uc] = (self._r, self._c, self._blank_lines)
            s = e
        if count >= loop_count:
            self._add_error(f'{self._get_prefix()}Te veel (>{loop_count}) variabele namen gevonden in "{cell}"')

    def _get_prefix(self):
        return f'Fout in template "{self._template_name}" regel {self._r + 1} kolom {self._c + 1}: '

    def _add_error(self, message):
        self._result.add_message(message, severity=MessageSeverity.Error)

    def _add_column_field(self, cell, column):
        """ 0-based row/col """
        if not cell:
            return
        self._column_fields[self._c] = TemplateField(cell[1:-1], column=column)
        self._c += 1

    """
    Definition
    """

    def _analyze_template(self):
        """ Precondition: file syntax has been validated. Variables are in UC. """
        self._out_rows = []
        self._r = -1
        self._c = 0
        self._out_row_ignored = False

        for row in self._template_rows:
            self._r += 1

            # a. Output Blank row (only if output has not been ignored, e.g. do not print blank lines between totals)
            if all(cell == EMPTY for cell in row):
                if not self._out_row_ignored:
                    self._out_rows.append(row)
                continue

            # b. Output Comments = Row with only texts (Title row)
            if all((cell == EMPTY or cell.startswith('"')) for cell in row):
                self._out_rows.append([self._substitute_vars_in_text(cell) for cell in row])
                self._out_row_ignored = False

            # c. Ignore totals
            elif all(TOTAL in (cell[1:-1]) for cell in row if cell != EMPTY):
                self._out_row_ignored = True

            # d. Output Column headings = Row with only Singular variables
            elif all((cell[1:-1] in VAR_NAMES_HEADER) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                self._out_rows.append([self._substitute_singular_var(cell) for cell in row])
                self._out_row_ignored = False

            # e. List Columns = Row with only Plural vars
            # Remember row (=column headers and positions). Level break = when blank line or totals
            elif all((cell[1:-1] in VAR_NAMES_DETAIL) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                [self._add_column_field(row[c], c) for c in range(len(row))]
                self._out_row_ignored = True
            else:
                raise GeneralException(
                    f'{self._get_prefix()}Gemengde meervoudige en enkelvoudige variabelen in een regel '
                    f'worden niet ondersteund.')

        # Map column fields with model definition
        [self._map_var_name(F) for F in self._column_fields.values()]

    def _map_var_name(self, F) -> TemplateField:
        F.model_var_name = VAR_NAMES_MAP.get(F.template_var_name)
        if not F.model_var_name:
            raise GeneralException(
                f'{self._get_prefix()}Template variabele "{F.template_var_name}" wordt niet ondersteund. '
                f'De variable kon niet gemapped worden met een model variable.')
        return F

    def _var_to_upper(self, cell) -> str:
        if cell.startswith('{') and cell.endswith('}'):
            var_name = cell.upper()
            self._template_var_names.add(var_name[1:-1])
            return cell.upper()
        return cell

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

    def _substitute_singular_var(self, cell, final=False) -> str:
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
            return f'"{{{var}}}" (*UNSUPPORTED*)'if final else EMPTY

    def _add_data_row(self, data_row):
        raise NotImplementedError

    def _format_and_add_value(self, var_name, value=None, write=False):
        """ Also add optional empty columns """
        # Output empty columns
        colno_varname = self._r_c[var_name][1]
        [self._output_cell(EMPTY) for _ in range(colno_varname - self._colno_current)]

        # Format and output the value
        if var_name == DATES:
            self._output_cell(format_date(value, input_format='YMD', output_format='DMY'))
        else:
            self._output_cell(self._format_amount(value))

        # Output the row
        if write:
            self._add_row(var_name)

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

    def _substitute_var_in_text(self, cell, s, e) -> str:
        var = cell[s + 1:e - 1].upper()
        if var == YEAR:
            cell = f'{cell[:s]}{self._year}{cell[e:]}'
        return cell

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

    @staticmethod
    def _format_amount(value) -> str:
        """ If it is an amount, format it."""
        if not isinstance(value, float):
            return value

        value = round(value, 2)
        if comma_target == ',':
            value = str(value).replace('.', ',')
        return value if value != '0.0' else EMPTY

    def _output_cell(self, value):
        self._out_row.append(value)
        self._colno_current += 1
        self._first = False

    def _add_empty_rows(self, count):
        [self._out_rows.append([EMPTY]) for _ in range(count)]
