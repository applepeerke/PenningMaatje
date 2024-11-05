# ---------------------------------------------------------------------------------------------------------------------
# Maand.py
#
# Author      : Peter Heijligers
# Description : Maand
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-31 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table


class Year(BaseObject):

    @property
    def year(self):
        return self._year

    @property
    def overbooking(self):
        return self._overbooking

    @property
    def costs(self):
        return self._costs

    @property
    def revenues(self):
        return self._revenues

    @property
    def balance(self):
        return self._balance

    @property
    def balance_corrected(self):
        return self._balance_corrected
    """ 
    Setters 
    """

    @overbooking.setter
    def overbooking(self, value):
        self._overbooking = value

    @costs.setter
    def costs(self, value):
        self._costs = value

    @revenues.setter
    def revenues(self, value):
        self._revenues = value

    @balance.setter
    def balance(self, value):
        self._balance = value

    @balance_corrected.setter
    def balance_corrected(self, value):
        self._balance_corrected = value

    @balance_corrected.setter
    def balance_corrected(self, value):
        self._balance_corrected = value

    def __init__(self, year: int, table_name=None):
        self._year = year
        self._overbooking = 0.00
        self._costs = 0.00
        self._revenues = 0.00
        self._balance = 0.00
        self._correction = 0.00
        self._balance_corrected = 0.00
        super().__init__(table_name or Table.Year)  # Can be Year or Month

    def _set_attributes(self):
        self._attributes = {
            FD.Year: self._model.get_att(self._table_name, FD.Year, self._year),
            FD.Overbooking: self._model.get_att(self._table_name, FD.Overbooking, self._overbooking),
            FD.Costs: self._model.get_att(self._table_name, FD.Costs, self._costs),
            FD.Revenues: self._model.get_att(self._table_name, FD.Revenues, self._revenues),
            FD.Balance: self._model.get_att(self._table_name, FD.Balance, self._balance),
            FD.Balance_corrected: self._model.get_att(self._table_name, FD.Balance_corrected, self._balance_corrected)
        }
