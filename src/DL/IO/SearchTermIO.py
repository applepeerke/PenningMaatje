from src.DL.DBDriver.Att import Att
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD, Model
from src.DL.Objects.SearchTerm import SearchTerm
from src.DL.Table import Table
from src.DL.Lexicon import SEARCH_TERM, BOOKING_CODE
from src.GL.Enums import ResultCode
from src.GL.Result import Result

TABLE = Table.SearchTerm
PGM = 'SearchTermIO'

d = Model().get_colno_per_att_name(TABLE, zero_based=False)


class SearchTermIO(BaseIO):

    def __init__(self):
        super().__init__(TABLE)

    def insert(self, obj: SearchTerm) -> bool:
        """ Avoid duplicates """
        where = [Att(FD.SearchTerm, obj.search_term)]
        return self._insert(obj, where, pgm=PGM)

    def _error(self, action):
        self._result = Result(
            ResultCode.Error,
            f'{SEARCH_TERM} "{self._object.search_term}" {BOOKING_CODE} "{self._object.booking_code}" '
            f'kon niet worden {action}')

    @staticmethod
    def row_to_obj(row) -> SearchTerm:
        return SearchTerm(
            search_term=row[d[FD.SearchTerm]],
            booking_code=row[d[FD.Booking_code]]
        ) if row else SearchTerm()

    def _get_all_values(self) -> list:
        values = self._get_pk(self._object)
        values.extend([Att(FD.Booking_code, self._object.booking_code)])
        return values

    def _get_pk(self, obj):
        return [Att(FD.SearchTerm, obj.search_term)]
