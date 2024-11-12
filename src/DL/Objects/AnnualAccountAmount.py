from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache

BCM = BookingCache()


class AnnualAccountAmount(BaseObject):

    @property
    def year(self):
        return self._year

    @property
    def booking_type(self):
        return self._booking_type

    @property
    def booking_maingroup(self):
        return self._booking_maingroup

    @property
    def booking_subgroup(self):
        return self._booking_subgroup

    @property
    def booking_code(self):
        return self._booking_code

    @property
    def amount_realisation(self):
        return self._amount_realisation

    @property
    def amount_budget_this_year(self):
        return self._amount_budget_this_year

    @property
    def amount_budget_previous_year(self):
        return self._amount_budget_previous_year

    def __init__(self,
                 year=0,
                 booking_type=EMPTY,
                 booking_maingroup=EMPTY,
                 booking_subgroup=EMPTY,
                 amount_realisation=0.0,
                 amount_budget_this_year=0.0,
                 amount_budget_previous_year=0.0):
        self._year = year
        self._booking_type = booking_type
        self._booking_maingroup = booking_maingroup
        self._booking_subgroup = booking_subgroup
        self._booking_code = BCM.get_booking_code_from_lk(
            booking_type, booking_maingroup, booking_subgroup)

        self._amount_realisation = amount_realisation
        self._amount_budget_this_year = amount_budget_this_year
        self._amount_budget_previous_year = amount_budget_previous_year

        super().__init__(Table.AnnualAccount)

    def _set_attributes(self):
        self._attributes = {
            FD.Year: self._model.get_att(self._table_name, FD.Year, self._year),
            FD.Booking_type: self._model.get_att(self._table_name, FD.Booking_type, self._booking_type),
            FD.Booking_maingroup: self._model.get_att(self._table_name, FD.Booking_maingroup, self._booking_maingroup),
            FD.Booking_subgroup: self._model.get_att(self._table_name, FD.Booking_subgroup, self._booking_subgroup),
            FD.Booking_code: self._model.get_att(self._table_name, FD.Booking_code, self._booking_code),
            FD.Amount_realisation: self._model.get_att(self._table_name, FD.Amount_realisation, self._amount_realisation),
            FD.Amount_budget_this_year: self._model.get_att(
                self._table_name, FD.Amount_budget_this_year, self._amount_budget_this_year),
            FD.Amount_budget_previous_year: self._model.get_att(
                self._table_name, FD.Amount_budget_previous_year, self._amount_budget_previous_year)
        }