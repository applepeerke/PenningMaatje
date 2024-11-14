from datetime import datetime

from src.BL.Summary.SummaryBase import session, csvm, BCM
from src.BL.Summary.Templates.Const import *
from src.BL.Summary.Templates.TemplateBase import TemplateBase, VAR_NAMES_MAP
from src.BL.Summary.Templates.TemplateField import TemplateField
from src.DL.Lexicon import PERIODIC_ACCOUNTS, TRANSACTIONS, MONTH_DESCRIPTIONS, PERIODIC_ACCOUNT
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.Const import EMPTY, BLANK, EXT_CSV
from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException

PGM = 'PeriodicAccount'

# noinspection SpellCheckingInspection
"""
----------------------------------------------------------------------------------------------
EXAMPLE:
----------------------------------------------------------------------------------------------
    "Bankrekening wijkgemeente Leiden Zuidwest"				
        {maand}			{jaar}

"datum"	"Omschrijving"	"inkomsten"	"uitgaven"	"Grootboek"
        "Beginsaldo"	{beginsaldo}		
        "Eindsaldo"	{eindsaldo}		
        "totaal inkomsten\\uitgaven"	{totaal inkomsten}	{totaal uitgaven}	

{datums}	{Omschrijvingen}	{inkomsten}	{uitgaven}	{Boeking omschrijvingen}
----------------------------------------------------------------------------------------------
"""


class PeriodicAccount(TemplateBase):
    @property
    def closing_balance(self):
        return self._closing_balance

    def __init__(self, opening_balance=0.0):
        super().__init__(PERIODIC_ACCOUNT)
        self._te_def = Model().get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
        self._condensed_row_def = {}
        self._month_from = 0
        self._month_to = 0
        self._month_from_current = 0
        self._month_to_current = 0
        self._opening_balance_start_of_year = opening_balance
        self._opening_balance = 0.0
        self._closing_balance = 0.0
        self._total_costs = 0.0
        self._total_revenues = 0.0

    def _initialize_year(self):
        self._opening_balance = self._opening_balance_start_of_year

    def export(self, year=None, month_from=None, month_to=None):
        """ Process all months to calculate opening/closing balance. Only print the requested ones. """
        # Opening balance is updated
        self._out_rows = []

        self._year = int(year) if year else int(datetime.now().year)
        self._month_from = month_from
        self._month_to = month_to if month_to else month_from

        # Export per month, quarter, semester
        self._initialize_year()
        [self._export(m + 1) for m in range(12)]

        self._initialize_year()
        [self._export(q * 3 + 1, q * 3 + 3) for q in range(4)]

        self._initialize_year()
        [self._export(s * 6 + 1, s * 6 + 6) for s in range(2)]

    def _export(self, month, month_to=None):
        """
        @param: month = current month. M: [1-12], Q: [1, 4, 7, 10], S: [1, 7]
        @param: month_to = month to.   M: [1-12], Q: [3, 6, 9, 12], S: [1, 2]
        """
        self._month_from_current = month
        self._month_to_current = month_to

        # Get the transactions for the period.
        transactions = self._transaction_io.get_transactions(self._year, month, month_to)

        # Get the period totals.
        c_amount = self._te_def[FD.Amount_signed]
        self._total_costs = sum(row[c_amount] for row in transactions if row[c_amount] < 0.0)
        self._total_revenues = sum(row[c_amount] for row in transactions if row[c_amount] > 0.0)
        self._closing_balance = self._opening_balance + self._total_revenues + self._total_costs

        # Output the periods that are completely within the requested months-window.
        month_to = month if month_to is None else month_to
        if transactions and self._month_from <= month <= month_to <= self._month_to:
            self._write_report(transactions, month, month_to)

        # Set the opening balance
        self._opening_balance = self._closing_balance

    def _write_report(self, transactions, month, month_to=None):

        # Process output template
        self._analyze_template()

        # Output naar CSV.
        # Filename example: "Periodieke rekening 2024 maand 4.csv"
        filename = f'{PERIODIC_ACCOUNTS} {self._year} {self._get_title(month, month_to)}{EXT_CSV}'
        self._out_path = f'{session.export_dir}{filename}'

        # Construct the report
        self._construct(transactions)

        # Write CSV
        csvm.write_rows(self._out_rows, data_path=self._out_path, open_mode='w')
        self._export_count += 1

    @staticmethod
    def _get_title(month, month_to) -> str:
        if not month_to or month == month_to:
            return f'maand {month}'
        elif month_to - month == 2:
            return f'Q{int(((month - 1) / 3) + 1)}'
        elif month_to - month == 5:
            return f'S{int(((month - 1) / 6)) + 1}'
        else:
            raise GeneralException(f'Report title could not be established for month {month} and month_to {month_to}')

    def _substitute_singular_var(self, cell) -> str:
        """
        Variables in the heading.
        N.B. Cell has been validated already.
        """
        if not cell:
            return EMPTY
        if cell.startswith('"'):
            return cell[1:-1]

        var = cell[1:-1]  # Remove {}

        if var == YEAR:
            return str(self._year)
        elif var == YEAR_PREVIOUS:
            return str(self._year - 1)
        elif var in (MONTH, MONTH_FROM):
            if self._month_to_current is None:
                return MONTH_DESCRIPTIONS.get(self._month_from_current)
            else:
                return (f'{MONTH_DESCRIPTIONS.get(self._month_from_current)} '
                        f'tot {MONTH_DESCRIPTIONS.get(self._month_to_current)}')
        elif var == MONTH_TO:
            return str(self._month_to_current or EMPTY)
        elif var == OPENING_BALANCE:
            return str(self._format_amount(self._opening_balance))
        elif var == CLOSING_BALANCE:
            return str(self._format_amount(self._opening_balance + self._total_costs + self._total_revenues))
        elif var == TOTAL_REVENUES:
            return str(self._format_amount(self._total_revenues))
        elif var == TOTAL_COSTS:
            return str(self._format_amount(self._total_costs))
        elif var in VAR_SINGULAR_DESC:
            return VAR_SINGULAR_DESC[var]
        else:
            return f'{cell} (*UNSUPPORTED*)'

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

            # c. Output Column headings = Row with only Singular variables
            elif all((cell[1:-1] in VAR_NAMES_HEADER) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                self._out_rows.append([self._substitute_singular_var(cell) for cell in row])
                self._out_row_ignored = False

            # d. List Columns = Row with only Plural vars
            # Remember row (=column headers and positions). Level break = when blank line or totals
            elif all((cell[1:-1] in VAR_NAMES_DETAIL) for cell in row if (cell != EMPTY and not cell.startswith('"'))):
                [self._add_column_field(row[c], c) for c in range(len(row))]
                self._out_row_ignored = True
            else:
                raise GeneralException(
                    f'Fout in regel {self._r}: Gemengde meervoudige en enkelvoudige variabelen in een regel '
                    f'worden niet ondersteund.')

        # Map column fields with model definition
        [self._map_var_name(F) for F in self._column_fields.values()]

    def _map_var_name(self, F) -> TemplateField:
        F.model_var_name = VAR_NAMES_MAP.get(F.template_var_name)
        if not F.model_var_name:
            raise GeneralException(
                f'Fout in regel {self._r}: Variabele "{F.model_var_name}" wordt niet ondersteund. '
                f'De variable kon niet gemapped worden met een model variable.')
        return F

    """
    Construction
    """

    def _construct(self, transactions):
        """
        N.B. Out rows are already been filled with title rows. Added here are the transactions:
        [datum, Omschrijving, inkomsten, uitgaven, Grootboek]
        """
        if not transactions:
            self._result.add_message(
                f'{PGM}: Er is niets te doen. Er zijn geen transacties in de database gevonden '
                f'(voor jaar {self._year}, maand van {self._month_from} en maand t/m {self._month_to}).')
            return  # Nothing to do. No exception, other months may have data.

        # Calculate total amount
        d = self._te_def
        total_amount_signed = sum(row[d[FD.Amount_signed]] for row in transactions)

        # Prepare the rows while formatting the cells
        condensed_rows = [[self._substitute_value(F.template_var_name, row[d[F.model_var_name]])
                           for _, F in self._column_fields.items()]
                          for row in transactions]

        # Format and add the rows
        start_row = len(self._out_rows)
        self._condensed_row_def = {F.template_var_name: c for c, F in self._column_fields.items()}
        total_amount_split_up = 0.0
        for row in condensed_rows:
            total_amount_split_up = (
                    total_amount_split_up +
                    row[self._condensed_row_def[COSTS]] +
                    row[self._condensed_row_def[REVENUES]])
            self._add_data_row(row)

        # X-check after dividing signed amount over 2 columns
        self._x_check(total_amount_signed, total_amount_split_up, '1. Voor uitvoer regels maken')

        # X-check output (string representation)
        c_costs = [F.column_no for F in self._column_fields.values() if F.template_var_name == COSTS][0]
        c_revenues = [F.column_no for F in self._column_fields.values() if F.template_var_name == REVENUES][0]
        total_amount_out = sum(
            self._add_str_amounts(row[c_costs], row[c_revenues])
            for row in self._out_rows[start_row:])
        self._x_check(total_amount_signed, total_amount_out, '2. Voor export naar CSV')

    @staticmethod
    def _add_str_amounts(costs: str, revenues: str) -> float:
        return toFloat(costs) + toFloat(revenues)

    def _substitute_value(self, template_var_name, value):
        if template_var_name in (COSTS, REVENUES):
            return self._split_costs_revenues(value, template_var_name)
        elif template_var_name == DESCRIPTIONS:
            desc = self._get_comments_part(value, 'OMSCHRIJVING')
            if len(desc) < 10:
                name = self._get_comments_part(value, 'NAAM')
                desc = f'{name} {desc}' if desc else name
            if len(desc) < 10:
                prefix = self._get_comments_part(value, FIRST)
                iban = self._get_comments_part(value, 'IBAN')
                period = self._get_comments_part(value, 'PERIODE')
                desc = f'{prefix} {iban} {period}'
            return desc
        elif template_var_name == BOOKING_DESCRIPTIONS:
            return BCM.get_value_from_booking_code(value, FD.Booking_description)
        else:
            return value

    def _get_comments_part(self, value, endswith) -> str:
        """
        Retrieve a part form the comments.
        Example comment: "Naam: P. Puk Omschrijving: Nieuwe fiets IBAN: f4673..."
        """
        desc = EMPTY
        # Search in first line
        if endswith == FIRST:
            desc = self._remove_last_word(value)
        else:
            # Search key part (like "Omschrijving" or "Naam").
            items_uc = value.upper().split(':')
            index = [i for i in range(len(items_uc)) if items_uc[i].endswith(endswith)]
            # Next item has the value.
            if index:
                j = index[0] + 1
                if j < len(items_uc):
                    desc = self._remove_last_word(value, j)
        return desc.strip()

    @staticmethod
    def _remove_last_word(value, index=0) -> str:
        """ Remove last word (e.g. "IBAN") """
        lines = value.split(':')  # Now not UC
        if not lines or index >= len(lines):
            return value
        line = lines[index]
        words = line.split(BLANK)
        return BLANK.join(words[:-1]) if words else value

    @staticmethod
    def _split_costs_revenues(amount, target) -> float:
        if target == REVENUES:
            return amount if amount >= 0 else 0.0
        else:
            return amount if amount < 0 else 0.0

    def _add_data_row(self, data_row):
        """
        E.g. data_row = [datum, Omschrijving, inkomsten, uitgaven, Grootboek]
        """

        # Set the new values
        for c, F in self._column_fields.items():
            F.value = data_row[self._condensed_row_def[F.template_var_name]]

        # Format and add the columns and output the row.
        [self._format_and_add_value(F.template_var_name, F.value) for c, F in self._column_fields.items()]

        # Add the row
        self._add_row()

    @staticmethod
    def _x_check(total_amount_db, total_amount_processed, step_name=None):
        amount_processed = round(total_amount_processed, 2)
        amount_db = round(total_amount_db, 2)
        if amount_processed != amount_db:
            raise GeneralException(
                f'Totaal bedrag verwerkt in de lijst is {amount_processed}.\n'
                f'Totaal bedrag in de {TRANSACTIONS} is {amount_db}.\n'
                f'Het verschil is {round(amount_db - amount_processed, 2)}.')
