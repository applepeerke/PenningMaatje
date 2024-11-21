from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.GL.Const import EMPTY


class OpeningBalance(BaseObject):

    @property
    def year(self):
        return self._year

    @property
    def opening_balance(self):
        return self._opening_balance

    def __init__(self, year=EMPTY, opening_balance=0.0):
        self._year = year
        self._opening_balance = opening_balance
        super().__init__(Table.OpeningBalance)

    def _set_attributes(self):
        self._attributes = {
            FD.Year:  self._model.get_att(self._table_name, FD.Year, self._year),
            FD.Opening_balance: self._model.get_att(self._table_name, FD.Opening_balance, self._opening_balance)
        }
