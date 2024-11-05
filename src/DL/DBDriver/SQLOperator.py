# ---------------------------------------------------------------------------------------------------------------------
# SQLOperator.py
#
# Author      : Peter Heijligers
# Description : SQL operators
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-01-05 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------


class SQLOperator(object):

    @property
    def EQ(self):
        return self._EQ

    @property
    def LT(self):
        return self._LT

    @property
    def GT(self):
        return self._GT

    @property
    def GE(self):
        return self._GE

    @property
    def LE(self):
        return self._LE

    @property
    def NE(self):
        return self._NE

    @property
    def LIKE(self):
        return self._LIKE

    def __init__(self):
        self._EQ = '='
        self._LT = '<'
        self._GT = '>'
        self._LE = '<='
        self._GE = '>='
        self._NE = '<>'
        self._LIKE = ' LIKE '
