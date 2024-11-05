from src.GL.Const import EMPTY


class Account(object):

    @property
    def bban(self):
        return self._bban

    @property
    def iban(self):
        return self._iban

    def __init__(self, bban, iban=EMPTY):
        self._bban = bban
        self._iban = iban
