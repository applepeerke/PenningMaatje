from abc import ABC
from copy import copy
from typing import Optional

from src.DL.Config import CF_SEARCH_AMOUNT, CF_SEARCH_AMOUNT_TO, \
    CF_COMMA_REPRESENTATION_DB, CF_COMMA_REPRESENTATION_DISPLAY, CF_SEARCH_YEAR, CF_SEARCH_MONTH, \
    CF_SEARCH_TRANSACTION_CODE, CF_SEARCH_TEXT, CF_SEARCH_COUNTER_ACCOUNT, CF_SEARCH_REMARKS, CF_SEARCH_BOOKING_CODE
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.VL.Data.Constants.Const import LEEG, NIET_LEEG
from src.DL.Lexicon import TRANSACTIONS
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Const import EMPTY
from src.GL.Enums import ResultCode
from src.GL.Functions import FloatToStr, tuple_to_value, toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import toBool, isInt
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache

CM = ConfigManager()
oper = SQLOperator()

PGM = 'TransactionsIO'
TABLE = Table.TransactionEnriched
c_counter_account_id = Model().get_column_number(TABLE, FD.Counter_account_id)

BCM = BookingCache()


class TransactionsIO(BaseIO, ABC):

    @property
    def rows(self):
        return self._rows

    @property
    def total(self):
        return self._total

    def __init__(self):
        super().__init__(TABLE)
        self._comma_target = CM.get_config_item(CF_COMMA_REPRESENTATION_DB)
        self._comma_source = CM.get_config_item(CF_COMMA_REPRESENTATION_DISPLAY)
        self._where_atts = []
        self._dialog_mode = False
        self._rows = []
        self._total = self.get_total()
        self._te_dict = self._model.get_colno_per_att_name(TABLE, zero_based=False)

    """
    Search
    """

    def search(self, dialog_mode=True) -> Result:
        self._dialog_mode = dialog_mode

        # A. Search for AND relations
        try:
            where = self._get_where_from_config(dialog=True)
        except GeneralException as e:
            return Result(ResultCode.Error, e.message)

        if where is None:  # No search criteria specified
            return Result()

        # B. Get the rows. Search for OR relations.
        self._rows = self._db.fetch(TABLE, where=where)
        #    Search in Name has been specified: Search for Comments and Remarks too.
        if any(att.name == FD.Name for att in where):
            self._rows.extend(
                self._db.fetch(TABLE, where=self._get_where_from_config(att_name_text=FD.Comments)))
            self._rows.extend(
                self._db.fetch(TABLE, where=self._get_where_from_config(att_name_text=FD.Remarks, dialog=True)))
            # Remove duplicates
            self._rows = self._deduplicate_rows(self._rows)

        if not self._rows:
            result = Result(text=f'Geen {TRANSACTIONS} gevonden.')
        else:
            if CM.is_search_for_empty_booking_mode():
                # Sort (list counter_account with most rows first)
                # Get rows per counter_account_id
                account_ids = {}
                for r in self._rows:
                    Id = r[c_counter_account_id]
                    if Id in account_ids:
                        account_ids[Id].append(r)
                    else:
                        account_ids[Id] = [r]
                # Sort counter_account_ids on rows count
                sorted_ids = dict(sorted(account_ids.items(), key=lambda item: len(item[1]), reverse=True))
                self._rows = []
                for Id, rows in sorted_ids.items():
                    self._rows.extend(rows)
            else:
                self._rows = sorted(self._rows, key=lambda row: row[0], reverse=True)
            result = Result(text=f'{len(self._rows)} {TRANSACTIONS} gevonden.')

        # C. Total amount
        self._total = self.get_total()
        return result

    @staticmethod
    def _deduplicate_rows(rows) -> list:
        # Remove duplicates
        out_rows = []
        rows = sorted(rows, key=lambda x: x[0])
        row_id_prv = 0
        for row in rows:
            if row[0] == row_id_prv:
                continue
            row_id_prv = row[0]
            out_rows.append(row)
        return out_rows

    def _get_where_from_config(self, att_name_text=FD.Name, dialog=False) -> Optional[list]:
        """ att_name_text:  Naam (1st time), Bijzonderheden, Mededelingen """
        self._where_atts = []
        amount = toFloat(CM.config_dict[CF_SEARCH_AMOUNT], self._comma_source)
        amount_to = toFloat(CM.config_dict[CF_SEARCH_AMOUNT_TO], self._comma_source)
        amount = EMPTY if amount == 0 else amount
        amount_to = EMPTY if amount_to == 0 else amount

        self._add_where_att(FD.Year, 'int', self._get_int_value(tuple_to_value(CM.get_config_item(CF_SEARCH_YEAR))))
        self._add_where_att(FD.Month, 'int', self._get_int_value(tuple_to_value(CM.get_config_item(CF_SEARCH_MONTH))))
        self._add_where_att(FD.Amount_signed, 'float', amount, relation=oper.EQ if not amount_to else oper.GE)
        self._add_where_att(FD.Amount_signed, 'float', amount_to, relation=oper.LE)
        self._add_where_att(FD.Transaction_code, 'str', CM.get_config_item(CF_SEARCH_TRANSACTION_CODE))
        self._add_where_att(att_name_text, 'str', self._wildcard(CM.get_config_item(CF_SEARCH_TEXT)))
        # Remarks checkbox
        if toBool(CM.get_config_item(CF_SEARCH_REMARKS)):
            att = self._model.get_att(Table.TransactionEnriched, FD.Remarks, value=EMPTY, relation=oper.NE)
            self._where_atts.append(copy(att))
        # Booking and Counter-account: Convert values to ids
        # - BookingCode
        booking_code = BCM.get_booking_code_from_desc(CM.get_config_item(CF_SEARCH_BOOKING_CODE))
        if booking_code:
            if booking_code == LEEG:
                self._add_where_att(FD.Counter_account_id, 'int', 0, relation=oper.GT)
                Id = 0
            else:
                Id = self._db.fetch_id(
                    Table.BookingCode, where=[Att(FD.Booking_code, booking_code)])
            self._add_where_att(FD.Booking_id, 'int', Id)
        # - CounterAccount
        counter_account = CM.get_config_item(CF_SEARCH_COUNTER_ACCOUNT)
        if counter_account:
            Id = 0 if counter_account == LEEG else \
                self._db.fetch_id(
                    Table.CounterAccount, where=[Att(FD.Counter_account_number, counter_account)])
            self._add_where_att(FD.Counter_account_id, 'int', Id)
        # Nothing specified
        if self._dialog_mode and dialog and not self._where_atts and not self._dialog.confirm(
                popup_key=f'{PGM}..get_where_from_config-2',
                text='Er zijn geen zoekcriteria opgegeven.\n\nDoorgaan?',
                hide_option=False):  # Canceled
            return None
        return self._where_atts

    def _add_where_att(self, name, typ, value, relation=None):
        """ isinstance does not work, bool is interpreted as int """
        if name and (
                (typ == 'str' and value) or
                (typ == 'float' and value != EMPTY) or  # Id can be 0
                (typ == 'int' and value is not None and value > -1) or  # Id can be 0
                (typ == 'bool' and value is True)):
            att = self._model.get_att(Table.TransactionEnriched, name, value=value, relation=relation)
            if value == LEEG:
                att.value = EMPTY
            elif value == NIET_LEEG:
                att.value = EMPTY
                att.relation = SQLOperator.NE
            self._where_atts.append(copy(att))

    @staticmethod
    def _wildcard(value):
        """ Search all text containing the search term. Exact search is not supported."""
        if value:
            value = value.replace('*', '%')
            if '%' not in value:
                value = f'%{value}%'
        return value

    @staticmethod
    def _get_int_value(value, zero_is_None=False) -> int or None:
        return None if not isInt(value) or (int(value) == 0 and zero_is_None) else int(value)

    def get_total(self):
        self._total = round(sum(r[self._te_dict[FD.Amount_signed]] for r in self._rows), 2)
        return FloatToStr(str(self._total))

    def get_year_rows(self, year=None):
        where = None if not year else [Att(FD.Year, year)]
        return self._db.fetch(TABLE, where=where)
