from src.DL.DBDriver.Att import Att
from src.DL.Model import FD
from src.DL.Objects.CounterAccount import CounterAccount
from src.DL.Table import Table
from src.DL.IO.BaseIO import BaseIO

PGM = 'CounterAccountIO'
TABLE = Table.CounterAccount


class CounterAccountIO(BaseIO):

    def __init__(self):
        super().__init__(TABLE)

    def insert(self, obj: CounterAccount) -> bool:
        """ Avoid duplicates """
        where = [Att(FD.Counter_account_number, obj.counter_account_number)]
        return self._insert(obj, where, pgm=PGM)

