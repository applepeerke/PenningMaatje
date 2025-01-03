from src.DL.DBDriver.Att import Att
from src.DL.IO.BaseIO import BaseIO
from src.DL.Lexicon import OPENING_BALANCE
from src.DL.Model import FD, Model
from src.DL.Objects.OpeningBalance import OpeningBalance
from src.DL.Table import Table
from src.GL.Enums import ResultCode
from src.GL.Functions import toFloat
from src.GL.Result import Result

TABLE = Table.OpeningBalance
PGM = 'OpeningBalanceIO'

d = Model().get_colno_per_att_name(TABLE, zero_based=False)


class OpeningBalanceIO(BaseIO):

    def __init__(self):
        super().__init__(TABLE)

    def insert(self, obj: OpeningBalance) -> bool:
        """ Avoid duplicates """
        where = [Att(FD.Year, obj.year)]
        return self._insert(obj, where, pgm=PGM)

    def _error(self, action):
        self._result = Result(
            ResultCode.Error,
            f'{OPENING_BALANCE} "{self._object.year}" kon niet worden {action}')

    @staticmethod
    def row_to_obj(row) -> OpeningBalance:
        return OpeningBalance(
            year=row[d[FD.Year]],
            opening_balance=toFloat(row[d[FD.Opening_balance]])
        ) if row else OpeningBalance()

    def _get_pk(self, obj):
        return [Att(FD.Year, obj.year)]

    def _get_all_values(self) -> list:
        values = self._get_pk(self._object)
        values.extend([Att(FD.Opening_balance, self._object.opening_balance)])
        return values

    def get_opening_balance(self, year=0):
        # Get the opening balance for the year
        opening_balance = self._db.fetch_value(TABLE, name=FD.Opening_balance, where=[Att(FD.Year, year)])
        return opening_balance if opening_balance is not None else 0.0
