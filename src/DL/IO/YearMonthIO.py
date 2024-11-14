#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime

from src.BL.Functions import get_BBAN_from_IBAN
from src.DL.Config import CF_IBAN, CF_ROWS_TRANSACTION
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.AttType import AttType
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Model import Model, FD
from src.DL.Objects.Month import Month
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as AccountCache
from src.DL.YearMonthTransactionsMax import YearMonthTransactionsMax
from src.DL.Lexicon import OVERBOOKING, COSTS, REVENUES, OVERBOOKINGS
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Enums import Color, MessageSeverity
# Working fields
from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import isInt

PGM = 'YearMonthIO'

error_prefix = f'{PGM} {Color.RED}Error{Color.NC}:'

model = Model()
BCM = BookingCodeCache()
ACM = AccountCache()
CM = ConfigManager()
TE_dict = model.get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
mo_dict = model.get_colno_per_att_name(Table.Month)


class YearMonthIO:

    def __init__(self):
        self._first_month_with_transactions = 0
        self._db = None
        self._warnings = []
        self._warning_rk_dict = {}
        self._result = Result()
        self._TE_manager = TransactionsIO()
        self._max_rows_TE = YearMonthTransactionsMax()
        self._max_rows_TE_defined = CM.get_config_item(CF_ROWS_TRANSACTION)

    def refresh_data(self) -> Result:
        """
        from_month is always 1.
        to_month is always 12.
        """
        self._result = Result()
        kwargs = self.get_default_kwargs()
        # Validate input
        try:
            self._chk_input(**kwargs)
        except GeneralException as e:
            self._result.add_message(f'{error_prefix}{e.message}', MessageSeverity.Error)
            return self._result

        from_year = kwargs['from_year']
        from_month = kwargs['from_month']
        to_month = kwargs['to_month']
        to_year = kwargs['to_year']

        # Go!
        # Delete the 12 months
        self._db = Session().db
        self._db.clear(Table.Month)

        account_bban = get_BBAN_from_IBAN(CM.get_config_item(CF_IBAN))

        # Get rows per year/month
        yy = from_year
        mm = from_month
        while yy <= to_year:
            where_year = [Att(FD.Account_bban, account_bban), Att(FD.Year, yy, type=AttType.Int)]
            if self._db.fetch(Table.TransactionEnriched, where=where_year):
                mm_2 = 12 if yy < to_year else to_month  # to_month is always 12.
                while mm <= mm_2:
                    # Get rows
                    where = where_year.copy()
                    where.append(Att(FD.Month, mm, type=AttType.Int))
                    month_rows = self._db.fetch(Table.TransactionEnriched, where=where)
                    self._set_max_month(yy, mm, len(month_rows))
                    # Calculate results
                    self._db.insert(Table.Month, self._calculate_month(month_rows, Month(yy, mm)), pgm=PGM)
                    mm += 1
            mm = 1
            yy += 1

        # Year summary
        self._create_jaaroverzicht(from_year, to_year)

        # Completion warnings
        sorted_warnings = sorted(self._warning_rk_dict.items(), key=lambda kv: kv[1][0], reverse=True)
        for v in sorted_warnings:
            self._result.add_message(
                f'{PGM} {Color.ORANGE}Waarschuwing{Color.NC}: '
                f'{v[1][0]} keer BBAN van tegenrekening "{v[0]}" niet gevonden. '
                f'1st mededeling = "{v[1][1]}"', severity=MessageSeverity.Warning)
        return self._result

    def _set_max_month(self, year, month, count):
        # Remember the most recent month with the most rows.
        # Threshold is the defined number.
        if count >= self._max_rows_TE_defined:
            count = self._max_rows_TE_defined
        if count >= self._max_rows_TE.count:
            self._max_rows_TE = YearMonthTransactionsMax(year, month, count)

    @staticmethod
    def get_default_kwargs() -> dict:
        where = [Att(FD.Account_bban, get_BBAN_from_IBAN(CM.get_config_item(CF_IBAN)))]
        from_year = Session().db.fetch_min(Table.TransactionEnriched, FD.Year, where=where) or 0
        to_year = Session().db.fetch_max(Table.TransactionEnriched, FD.Year, where=where) or 0
        if from_year == 0 or to_year == 0:
            return {}
        return {'from_year': max(from_year, 2000),
                'to_year': to_year if to_year >= from_year else datetime.now().year,
                'from_month': 1,
                'to_month': 12}

    @staticmethod
    def _chk_input(from_year=None, from_month=None, to_year=None, to_month=None):

        if not isInt(from_year) or not 2000 <= from_year <= datetime.now().year:
            raise GeneralException(f'jaar vanaf moet tussen 2000 and {datetime.now().year} liggen.')

        if not isInt(to_year) or to_year < from_year or to_year > datetime.now().year:
            raise GeneralException(f'jaar t/m moet >= jaar_vanaf en <= huidige jaar zijn.')

        if not isInt(from_month) or not 0 < from_month < 13:
            raise GeneralException(f'maand vanaf moet een nummer zijn tussen 1 en 12.')

        if not isInt(to_month) or not 0 < to_month < 13:
            raise GeneralException(f'maand t/m moet een nummer zijn tussen 1 en 12.')

        if from_year == to_year and from_month > to_month:
            raise GeneralException(f'maand t/m moet >= maand_vanaf zijn.')

    def _calculate_month(self, te_rows, M: Month) -> list:
        mo_row = [0, 0, 0, 0, 0, 0, 0]
        mo_row[mo_dict[FD.Year]] = M.year
        mo_row[mo_dict[FD.Month]] = M.maand
        if not te_rows:
            return mo_row

        bedrag_signed, totaal_abs, split_abs = 0.00, 0.00, 0.00

        # Get visible optional columns
        visible_optional_att_names = [
            k for k in model.get_att_per_name(Table.Year)
            if k in CM.get_extra_column_attribute_names()
        ]

        row_no = 0
        for te_row in te_rows:
            row_no += 1
            # Check jaar-maand
            jaar = te_row[TE_dict[FD.Year]]
            maand = te_row[TE_dict[FD.Month]]
            if jaar != M.year or maand != M.maand:
                message = f'{PGM} {Color.RED}Error{Color.NC}: ' \
                          f'Input {M.year}-{M.maand} is ongelijk aan gevonden {jaar}-{maand}.'
                self._result.add_message(message, severity=MessageSeverity.Error)
                raise GeneralException(message)

            af_bij = te_row[TE_dict[FD.Add_Sub]].lower()
            bedrag_abs = te_row[TE_dict[FD.Amount]]

            totaal_abs += bedrag_abs
            bedrag_signed = bedrag_abs if af_bij == 'bij' else bedrag_abs * -1

            # Algemeen: Saldo, Uitgaven, Inkomsten
            M.balance += bedrag_signed
            if af_bij == 'bij':
                M.revenues += bedrag_signed
            else:
                M.costs += bedrag_signed

            # Boeking-gerelateerd: Inkomsten/uitgaven/overboeking
            bk_type = BCM.get_value_from_id(te_row[TE_dict[FD.Booking_id]], FD.Booking_type)
            if not bk_type or bk_type in (COSTS, REVENUES):
                pass
            elif bk_type == OVERBOOKINGS:
                if FD.Overbooking in visible_optional_att_names:
                    M.overbooking += bedrag_signed
            else:
                message = f'{PGM} {Color.RED}Error{Color.NC}: ' \
                          f'{M.year}-{M.maand} Boeking type "{bk_type}" wordt niet ondersteund.'
                self._result.add_message(message, severity=MessageSeverity.Error)
                raise GeneralException(message)

        # Saldo gecorrigeerd voor overboeking
        M.balance_corrected = M.balance - M.overbooking

        # Check: Saldo = Inkomsten + Uitgaven.
        if toFloat(M.balance) != toFloat(M.revenues + M.costs):
            diff = toFloat(M.balance) - toFloat(M.revenues + M.costs)
            self._result.add_message(
                f'{PGM} {Color.ORANGE}Waarschuwing{Color.NC}: '
                f'{M.year}-{M.maand} saldo ({round(M.balance, 2)}) is ongelijk inkomsten + uitgaven ({diff})',
                severity=MessageSeverity.Warning)

        mo_row[mo_dict[FD.Overbooking]] = round(M.overbooking, 2)
        mo_row[mo_dict[FD.Costs]] = round(M.costs, 2)
        mo_row[mo_dict[FD.Revenues]] = round(M.revenues, 2)
        mo_row[mo_dict[FD.Balance]] = round(M.balance, 2)
        mo_row[mo_dict[FD.Balance_corrected]] = round(M.balance_corrected, 2)
        return mo_row

    def _create_jaaroverzicht(self, from_year=None, to_year=None):
        yy = from_year
        while yy <= to_year:
            where = [Att(FD.Year, value=yy, type=AttType.Int)]
            # Get rows
            mo_rows = self._db.fetch(Table.Month, where=where)
            # Calculate results
            if mo_rows:
                jo_row = self._get_jaaroverzicht(mo_rows)
                # Recreate jaar
                if jo_row:
                    self._db.delete(Table.Year, where=where)
                    self._db.insert(Table.Year, jo_row, pgm=PGM)
            yy += 1

    @staticmethod
    def _get_jaaroverzicht(mo_rows) -> list:
        # MO: [id, jaar, maand, [bedragen]]
        # JO: jaar, [bedragen]
        if not mo_rows or not mo_rows[0]:
            return []

        jo_row = [mo_rows[0][1], 0.00, 0.00, 0.00, 0.00, 0.00]
        for mo_row in mo_rows:
            # Add month amounts
            for i in range(3, len(jo_row) + 2):  # skip {id, jaar, month} columns
                jo_row[i - 2] = jo_row[i - 2] + float(mo_row[i])
        for i in range(1, len(jo_row)):
            jo_row[i] = toFloat(jo_row[i])
        return jo_row
