import os.path

from src.DL.DBDriver.Att import Att
from src.DL.Enums.Enums import BookingType
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import Model, FD
from src.DL.Objects.AnnualAccountAmount import AnnualAccountAmount
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import isInt
from src.DL.Lexicon import TEMPLATE_ANNUAL_ACCOUNT, ANNUAL_BUDGET, REALISATION, BUDGET, BOOKING_CODE
from src.VL.Data.Constants.Const import PROTECTED_BOOKINGS

PGM = 'AnnualAccountIO'

TABLE = Table.AnnualAccount
d = Model().get_colno_per_att_name(TABLE, zero_based=False)

TOTALE = 'TOTALE'
COLUMN = 'column'
TITLE = 'title'
VALUE = 'value'
EXPECTED_TITLES = [REALISATION, BUDGET, BUDGET]

# noinspection SpellCheckingInspection
"""
----------------------------------------------------------------------------------------------
EXAMPLE:
----------------------------------------------------------------------------------------------
0   1                   2           3           4
----------------------------------------------------------------------------------------------
Realisatie 2023 en begroting 2024 wijkgemeente Leiden Zuidwest				
                        Realisatie	Begroting 	Begroting 
                        2023	    2023	    2024
Inkomsten				
    Levend geld	        7.784,74	5.500,00	7.000,00				
    TOTALE Inkomsten	7.784,74	5.500,00	7.000,00
----------------------------------------------------------------------------------------------
"""


class AnnualAccountIO(BaseIO):

    def __init__(self):
        super().__init__(TABLE)
        self._result = Result()
        self._object = None
        self._object_old = None
        self._transaction_count = 0
        self._amount_columns = {}
        self._year_realisation = 0
        self._totale_count = 0
        self._transformed_rows = []

    @staticmethod
    def row_to_obj(row) -> AnnualAccountAmount:
        return AnnualAccountAmount(
            year=row[d[FD.Year]],
            booking_type=row[d[FD.Booking_type]],
            booking_maingroup=row[d[FD.Booking_maingroup]],
            booking_subgroup=row[d[FD.Booking_subgroup]],
            amount_realisation=row[d[FD.Amount_realisation]],
            amount_budget_this_year=row[d[FD.Amount_budget_this_year]],
            amount_budget_previous_year=row[d[FD.Amount_budget_previous_year]],
        ) if row else AnnualAccountAmount()

    def get_annual_budget_data(self, year) -> list:
        """ @return: [[type, maingroup, subgroup, budget_amount_previous_year, budget_amount_this_year]] """
        out_rows = []
        rows = self._db.select(TABLE, where=[Att(FD.Year, year)])
        for row in rows:
            if (row[d[FD.Amount_budget_previous_year]] == 0.0 and
                    row[d[FD.Amount_budget_this_year]] == 0.0):
                continue
            out_rows.append([
                row[d[FD.Booking_type]],
                row[d[FD.Booking_maingroup]],
                row[d[FD.Booking_subgroup]],
                float(row[d[FD.Amount_budget_previous_year]]),
                float(row[d[FD.Amount_budget_this_year]]),
            ])
        return out_rows

    def validate(self, path, rows):
        """ Validate 'Jaarrekening.csv' """
        prefix = f'{PGM}: Fout in bestand "{os.path.basename(path)}".\n\n'
        suffix = f'\n\nDe folder is "{os.path.dirname(path)}"'
        # Format OK?
        if not rows or len(rows[0]) < 3:
            raise GeneralException(
                f'{prefix}Het bestand heeft 4 kolommen nodig, er zijn er maar {len(rows[0])} aangeleverd.{suffix}')

        # Search and populate column heading with title and year(s)
        columns = {i: {COLUMN: i, TITLE: EMPTY, VALUE: 0} for i in range(len(rows[0]))}
        year_columns = []
        found = False
        for row in rows:
            # Try to find header with title and year(s)
            for i in range(len(row)):
                if isInt(row[i]) and 1900 < int(row[i]) < 2100:
                    year = int(row[i])
                    columns[i][VALUE] = year
                    year_columns.append(i)
                    if not found:  # 1st match should be the realisation year
                        found = True
                        self._year_realisation = year
                elif row[i]:
                    columns[i][TITLE] = row[i]
            # Exit when title row with years has been found.
            if found:
                break

        self._check_header(columns, year_columns)

        # Check content
        booking_types = set()
        for row in rows:
            if row[0] in BookingType.values():
                booking_types.add(row[0])
            if row[1].upper().startswith(TOTALE):
                self._totale_count += 1

        if len(booking_types) < 3:
            raise GeneralException(
                f'{prefix} Alleen typen "{booking_types}" zijn gevonden. '
                f'"{BookingType.values()}" zijn verwacht.{suffix}')

        # Transform the rows to AnnualAccountAmounts
        self._transform(rows)

        # Check the bookings in the AnnualAccountAmounts
        missing_booking_keys = set()

        for AAA in self._transformed_rows:
            if not AAA.booking_code and AAA.booking_type not in PROTECTED_BOOKINGS:  # Skip e.g. Overboeking
                missing_booking_keys.add(f'"{AAA.booking_type} {AAA.booking_maingroup} {AAA.booking_subgroup}"')
        if missing_booking_keys:
            prefix = f'{PGM}: Ontbrekende {BOOKING_CODE}(s) "{os.path.basename(path)}".\n\n'

            bullets = EMPTY
            bullets = [f'{bullets} - {m}\n' for m in list(missing_booking_keys)]
            self._result.add_message(
                f'{prefix}De volgende boekingen hebben nog geen {BOOKING_CODE}:\n{bullets}',
                severity=MessageSeverity.Warning)

    def _check_header(self, columns, year_columns):
        """
        Can deal with 2 or 3 columns. 1st one must be Realisation.
        @param: year_columns = columns indexes that contain a year. E.g. [2, 3, 4].
        """

        for i in range(len(year_columns)):
            title = columns[year_columns[i]][TITLE]
            value = columns[year_columns[i]][VALUE]
            if EXPECTED_TITLES[i].lower() not in title.lower():
                raise GeneralException(
                    f'{PGM}: Verwachte titel is "{EXPECTED_TITLES[i]}", maar gevonden is "{title}".')
            if value < self._year_realisation or value > self._year_realisation + 1:
                raise GeneralException(
                    f'{PGM}: Verwacht jaar is {self._year_realisation} of {self._year_realisation + 1}, '
                    f'maar gevonden is "{value}".')

        # Preserve only the columns with amounts
        count = 0
        for k, v in columns.items():
            if v[VALUE] > 0:
                self._amount_columns[count] = v
                count += 1

        col_count = len(self._amount_columns)
        if col_count < 2 or col_count > 4:
            raise GeneralException(
                f'{PGM}: Er is een onjuist ({col_count}) aantal bedrag-kolommen in de aangeleverde '
                f'{TEMPLATE_ANNUAL_ACCOUNT}. '
                f'Het moeten er 2 of 3 zijn (realisatie, begroting dit/vorig jaar).')

        if col_count < 3:
            self._result.add_message(
                f'{PGM}: Er zijn {col_count} bedrag-kolommen aanwezig in de aangeleverde '
                f'{TEMPLATE_ANNUAL_ACCOUNT}.\n'
                f'De tweede ("{self._amount_columns[1]["title"]})" wordt voor de {ANNUAL_BUDGET} gebruikt.',
                MessageSeverity.Warning)

    def _transform(self, rows):
        """ Transform 'Jaarrekening.csv' to [AnnualAccount] """
        self._transformed_rows = []
        booking_type, booking_maingroup, type_or_maingroup, type_or_maingroup_decided = EMPTY, EMPTY, EMPTY, EMPTY

        # Bepaal de kolommen met bedragen.
        if len(self._amount_columns) == 2:
            c_amount_budget_previous_year = None
            c_amount_budget_this_year = 1
        else:
            c_amount_budget_previous_year = 1
            c_amount_budget_this_year = 2

        # Process
        count_total_type = 0
        for row in rows:
            # Previous values
            p_type = booking_type
            p_maingroup = booking_maingroup
            p_type_or_maingroup = type_or_maingroup_decided

            type_or_maingroup = row[0]
            booking_subgroup = row[1]

            # EOF
            if booking_subgroup.upper().startswith(TOTALE):
                count_total_type += 1
                if count_total_type == self._totale_count:
                    break

            # Level break
            if type_or_maingroup:
                type_or_maingroup_decided = type_or_maingroup
                # Kolom 1 bevat ofwel booking-type (Inkomsten/Uitgaven/Overboekingen) of -hoofdgroep.
                if type_or_maingroup in BookingType.values():
                    booking_type = type_or_maingroup
                    booking_maingroup = EMPTY
                else:
                    booking_maingroup = type_or_maingroup
            else:
                booking_type = p_type
                # If there is no type|maingroup and type-mode: Move subgroup to maingroup.
                if p_type_or_maingroup in BookingType.values() and booking_subgroup:
                    type_or_maingroup_decided = p_type_or_maingroup
                    booking_maingroup = booking_subgroup
                    booking_subgroup = EMPTY
                else:
                    type_or_maingroup_decided = p_maingroup
                    booking_maingroup = p_maingroup

            # Bepaal de bedragen.
            amount_realisation = row[self._amount_columns[0]['column']]
            amount_budget_this_year = row[self._amount_columns[c_amount_budget_this_year]['column']]
            amount_budget_previous_year = row[self._amount_columns[c_amount_budget_previous_year]['column']] \
                if c_amount_budget_previous_year else 0.0

            amount_exists = (amount_realisation or
                             amount_budget_previous_year or
                             amount_budget_this_year)

            # Voeg toe als er een bedrag in de regel is, wat geen totaal is.
            if (booking_type
                    and amount_exists
                    and not booking_maingroup.upper().startswith('TOT')
                    and not booking_subgroup.upper().startswith('TOT')):
                self._transformed_rows.append(AnnualAccountAmount(
                    year=self._year_realisation,
                    booking_type=booking_type,
                    booking_maingroup=booking_maingroup,
                    booking_subgroup=booking_subgroup,
                    amount_realisation=toFloat(amount_realisation),
                    amount_budget_this_year=toFloat(amount_budget_this_year),
                    amount_budget_previous_year=toFloat(amount_budget_previous_year)  # Optional column
                ))

    def insert_many(self):
        [self._insert(AAA) for AAA in self._transformed_rows]
