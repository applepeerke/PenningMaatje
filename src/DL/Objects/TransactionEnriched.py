# ---------------------------------------------------------------------------------------------------------------------
# TransactionEnriched.py
#
# Author      : Peter Heijligers
# Description : TransactionEnriched
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-01 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.Lexicon import AMOUNT_PLUS, AMOUNT_MINUS
from src.GL.Const import EMPTY

ACM = CounterAccountCache()


class TransactionEnriched(BaseObject):

    @property
    def account_bban(self):
        return self._account_bban

    @property
    def date(self):
        return self._date

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def name(self):
        return self._name

    @property
    def transaction_code(self):
        return self._transaction_code

    @property
    def amount_signed(self):
        return self._amount_signed

    @property
    def comments(self):
        return self._comments

    @property
    def counter_account_number(self):
        return self._counter_account_number

    @property
    def counter_account_bban(self):
        return self._counter_account_bban

    @property
    def transaction_type(self):
        return self._transaction_type


    @property
    def remarks(self):
        return self._remarks

    @property
    def transaction_date(self):
        return self._transaction_date

    @property
    def transaction_time(self):
        return self._transaction_time

    def __init__(self, account_bban, date, name, amount_signed=0.0, comments=EMPTY, counter_account_number=EMPTY,
                 transaction_code=EMPTY, transaction_type=EMPTY, remarks=EMPTY, transaction_date=EMPTY, transaction_time=EMPTY):
        self._account_bban = account_bban
        self._date = date
        self._year = int(str(date)[:4])
        self._month = int(str(date)[4:6])
        self._name = name
        self._add_sub = AMOUNT_PLUS if amount_signed >= 0 else AMOUNT_MINUS
        self._amount = amount_signed if amount_signed >= 0 else amount_signed * -1
        self._amount_signed = amount_signed
        self._comments = comments
        self._counter_account_number = counter_account_number
        self._counter_account_bban = ACM.get_BBAN_from_IBAN(counter_account_number)
        self._transaction_code = transaction_code
        self._transaction_type = transaction_type
        self._remarks = remarks
        self._transaction_date = transaction_date
        self._transaction_time = transaction_time
        super().__init__(Table.TransactionEnriched)

    def _set_attributes(self):
        self._attributes = {
            FD.Account_bban: self._model.get_att(self._table_name, FD.Account_bban, self._account_bban),
            FD.Date: self._model.get_att(self._table_name, FD.Date, self._date),
            FD.Year: self._model.get_att(self._table_name, FD.Year, self._year),
            FD.Month: self._model.get_att(self._table_name, FD.Month, self._month),
            FD.Name: self._model.get_att(self._table_name, FD.Name, self._name),
            FD.Transaction_code: self._model.get_att(self._table_name, FD.Transaction_code, self._transaction_code),
            FD.Add_Sub: self._model.get_att(self._table_name, FD.Add_Sub, self._add_sub),
            FD.Amount: self._model.get_att(self._table_name, FD.Amount, self._amount),
            FD.Amount_signed: self._model.get_att(self._table_name, FD.Amount_signed, self._amount_signed),
            FD.Comments: self._model.get_att(self._table_name, FD.Comments, self._comments),
            FD.Counter_account_number: self._model.get_att(
                self._table_name, FD.Counter_account_number, self._counter_account_number),
            FD.Counter_account_bban: self._model.get_att(
                self._table_name, FD.Counter_account_bban, self._counter_account_bban),
            FD.Transaction_type: self._model.get_att(self._table_name, FD.Transaction_type, self._transaction_type),
            FD.Remarks: self._model.get_att(self._table_name, FD.Remarks, self._remarks),
            FD.Transaction_date: self._model.get_att(self._table_name, FD.Transaction_date, self._transaction_date),
            FD.Transaction_time: self._model.get_att(self._table_name, FD.Transaction_time, self._transaction_time),
        }
