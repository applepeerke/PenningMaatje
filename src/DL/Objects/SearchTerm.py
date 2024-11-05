from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.GL.Const import EMPTY


class SearchTerm(BaseObject):

    @property
    def search_term(self):
        return self._search_term

    @property
    def booking_code(self):
        return self._booking_code

    def __init__(self, search_term=EMPTY, booking_code=EMPTY):
        self._search_term = search_term
        self._booking_code = booking_code
        super().__init__(Table.SearchTerm)

    def _set_attributes(self):
        self._attributes = {
            FD.SearchTerm:  self._model.get_att(self._table_name, FD.SearchTerm, self._search_term),
            FD.Booking_code: self._model.get_att(self._table_name, FD.Booking_code, self._booking_code)
        }
