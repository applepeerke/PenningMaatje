# ---------------------------------------------------------------------------------------------------------------------
# Month.py
#
# Author      : Peter Heijligers
# Description : Maand
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-31 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.AttType import AttType
from src.DL.Model import FD
from src.DL.Objects.Year import Year
from src.DL.Table import Table


class Month(Year):

    @property
    def maand(self):
        return self._month

    def __init__(self, year: int, month: int):
        super().__init__(year, Table.Month)
        self._month = month
        self._attributes[FD.Month] = Att(FD.Month, self._month, type=AttType.Int)
