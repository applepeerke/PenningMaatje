from src.GL.Const import EMPTY
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache

BCM = BookingCodeCache()


class CounterAccount(object):

    @property
    def counter_account_number(self):
        return self._counter_account_number

    @property
    def name(self):
        return self._account_name

    @property
    def first_comment(self):
        return self._first_comment

    @property
    def booking_code(self):
        return self._booking_code

    @property
    def booking_id(self):
        return self._booking_id

    def __init__(self, counter_account_number, account_name, first_comment=EMPTY, booking_code=EMPTY, booking_id=0):
        self._counter_account_number = counter_account_number
        self._account_name = account_name
        self._first_comment = first_comment
        self._booking_code = booking_code
        self._booking_id = BCM.get_id_from_code(booking_code) if booking_id == 0 else booking_id
