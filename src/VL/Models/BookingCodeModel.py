from src.DL.DBDriver.Att import Att
from src.DL.Model import FD
from src.DL.Table import Table
from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Models.ListItemModel import ListItemModel
from src.VL.Data.DataDriver import Singleton as DataDriver

TABLE = Table.BookingCode
DD = DataDriver()


class BookingCodeModel(ListItemModel):

    @property
    def booking_types(self):
        return self._booking_types

    @property
    def transaction_count(self):
        return self._transaction_count

    def __init__(self, command: BoxCommand, obj):
        super().__init__(TABLE, command, obj)
        # Populate model attributes
        self._booking_types = self._session.db.select(
            Table.FlatFiles, name=FD.Value, where=[Att(FD.Key, FD.Booking_type)])
        self._transaction_count = DD.get_transaction_count(TABLE, self._object.booking_code)
