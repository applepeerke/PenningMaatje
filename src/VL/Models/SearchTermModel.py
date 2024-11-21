from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Data.DataDriver import Singleton as DataDriver
from src.VL.Models.ListItemModel import ListItemModel

TABLE = Table.SearchTerm
DD = DataDriver()
BCM = BookingCodeCache()


class SearchTermModel(ListItemModel):

    @property
    def booking_descriptions(self):
        return self._booking_descriptions

    @property
    def transaction_count(self):
        return self._transaction_count

    def __init__(self, command: BoxCommand, obj):
        super().__init__(TABLE, command, obj)
        # Populate model attributes
        self._booking_descriptions = BCM.formatted_booking_descriptions
        self._transaction_count = DD.get_transaction_count(TABLE, BCM.get_id_from_code(self._object.booking_code))
