from src.DL.Config import CF_ROWS_TRANSACTION
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.VL.Models.BaseModelTable import BaseModelTable
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache

TE_dict = Model().get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
BCM = BookingCodeCache()

PGM = 'TransactionsEnriched'


class TransactionsEnriched(BaseModelTable):

    def __init__(self):
        super().__init__(Table.TransactionEnriched)
        self._num_rows = int(self._CM.get_config_item(CF_ROWS_TRANSACTION, 5))
        self._db_row = []
        self._db_index = 0

    def _substitute_not_in_db(self, db_row, att):
        if att.in_db is True:
            self._db_index += 1
            return db_row[self._db_index]

        # Get Booking code from Id
        if att.name == FD.Booking_code:
            return BCM.get_value_from_id(db_row[TE_dict[FD.Booking_id]], FD.Booking_code)
        else:
            raise NotImplementedError(f'{PGM}: Attribute "{att.name}" is not supported.')
