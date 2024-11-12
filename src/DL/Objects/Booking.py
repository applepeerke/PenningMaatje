from src.DL.DBDriver.Att import Att
from src.DL.Model import FD
from src.DL.Objects.BaseObject import BaseObject
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache

BCM = BookingCache()


class Booking(BaseObject):

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
    def seqno(self):
        return self._seqno

    @property
    def booking_id(self):
        return self._booking_id

    @property
    def protected(self):
        return self._protected

    """
    Setters
    """

    @protected.setter
    def protected(self, value):
        self._protected = value

    def __init__(self,
                 booking_type=EMPTY,
                 booking_maingroup=EMPTY,
                 booking_subgroup=EMPTY,
                 booking_code=EMPTY,
                 seqno=0,
                 protected=False,
                 booking_id=EMPTY):
        self._booking_type = booking_type
        self._booking_maingroup = booking_maingroup
        self._booking_subgroup = booking_subgroup
        self._booking_code = booking_code
        self._seqno = seqno
        self._protected = protected
        self._booking_id = BCM.get_id_from_code(booking_code) if not booking_id else booking_id
        super().__init__(Table.BookingCode)

    def _set_attributes(self):
        self._attributes = {
            FD.Booking_type: self._model.get_att(self._table_name, FD.Booking_type, self._booking_type),
            FD.Booking_maingroup: self._model.get_att(self._table_name, FD.Booking_maingroup, self._booking_maingroup),
            FD.Booking_subgroup: self._model.get_att(self._table_name, FD.Booking_subgroup, self._booking_subgroup),
            FD.Booking_code: self._model.get_att(self._table_name, FD.Booking_code, self._booking_code),
            FD.SeqNo: self._model.get_att(self._table_name, FD.SeqNo, self._seqno),
            FD.Protected: self._model.get_att(self._table_name, FD.Protected, self._protected),
        }

    def get_pk(self):
        return [
            Att(FD.Booking_type, self._booking_type),
            Att(FD.Booking_maingroup, self._booking_maingroup),
            Att(FD.Booking_subgroup, self._booking_subgroup)
        ]
