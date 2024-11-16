from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.GL.Const import EMPTY


class Account(BaseObject):

    @property
    def bban(self):
        return self._bban

    @property
    def iban(self):
        return self._iban

    @property
    def description(self):
        return self._description

    """
    Setters
    """

    @description.setter
    def description(self, value):
        self._description = value

    def __init__(self, bban, iban=EMPTY, description=EMPTY):
        self._bban = bban
        self._iban = iban
        self._description = description
        super().__init__(Table.Account)

    def _set_attributes(self):
        self._attributes = {
            FD.Bban: self._model.get_att(self._table_name, FD.Bban, self._bban),
            FD.Iban: self._model.get_att(self._table_name, FD.Iban, self._iban),
            FD.Description: self._model.get_att(self._table_name, FD.Description, self._description),
        }
