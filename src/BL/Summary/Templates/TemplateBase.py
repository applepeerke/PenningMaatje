import os.path

from src.BL.Summary.SummaryBase import SummaryBase, session, csvm
from src.BL.Summary.Templates.Const import *
from src.BL.Summary.Templates.TemplateField import TemplateField
from src.DL.Config import CF_COMMA_REPRESENTATION_DISPLAY
from src.DL.IO.TransactionIO import TransactionIO
from src.DL.Lexicon import CSV_FILE
from src.DL.Model import FD
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
    BOOKING_DESCRIPTIONS: FD.Booking_code
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

    def __init__(self, template_name):
        super().__init__()
        self._transaction_io = TransactionIO()
        self._template_name = template_name
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

        # Validate the template
        self._validate_template()

    def export(self, year=None, month_from=None, month_to=None) -> Result:
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
        while count < loop_count and cell.find('{', s) > -1:
            count += 1
            s += 1
            e = cell.find('}', s)
            var_name = cell[s:e]
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
            s = e + 1
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
        raise NotImplementedError

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

    def _substitute_singular_var(self, cell) -> str:
        """ N.B. Cell has been validated already. """
        raise NotImplementedError

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
