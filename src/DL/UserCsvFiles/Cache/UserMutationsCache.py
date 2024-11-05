#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY, USER_MUTATIONS_FILE_NAME, EXT_CSV

model = Model()
row_def = Model().get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
TABLE = Table.TransactionEnriched


def get_te_key(account_number_bban, date, counter_account_number, comments) -> str:
    """
    Get the TE-row pk-values separated by "|". Date in yyyymmdd.
    """
    # Validation
    if not account_number_bban or not date or (not counter_account_number and not comments):
        return EMPTY
    return f'{account_number_bban}|{date}|{counter_account_number}|{comments}'


class Singleton:
    """ Singleton """

    class UserMutationsCache(object):
        """
        During import of bank transactions csv files,
        the user-assigned transaction bookings and remarks must be retrieved.
        This is done from here.
        """

        @property
        def booking_codes(self):
            return self._booking_codes

        @property
        def remarks_by_te_key(self):
            return self._remarks_by_te_key

        def __init__(self):
            self._booking_codes = set()
            self._remarks_by_te_key = {}
            self._mutations_by_te_key = {}
            self._initialized = False

        def get_booking_code(self, account_number_bban, date, counter_account_number, comments) -> str:
            """ return: booking from cache if this exists, else empty. """
            self.initialize()  # 1st time
            te_key = get_te_key(account_number_bban, date, counter_account_number, comments)
            row = self._mutations_by_te_key.get(te_key, EMPTY)
            return row[row_def[FD.Booking_id]] if row else EMPTY

        def get_remarks(self, te_key) -> str:
            self.initialize()  # 1st time
            return self._remarks_by_te_key.get(te_key, EMPTY)

        def initialize(self, force=False):
            if self._initialized and not force:
                return

            self._initialized = True
            self._booking_codes = set()
            user_mutations_path = f'{Session().backup_dir}{USER_MUTATIONS_FILE_NAME}{EXT_CSV}' \
                if Session().backup_dir else EMPTY

            # Populate cache
            [self._populate_cache(row) for row in CsvManager().get_rows(data_path=user_mutations_path)]

        def _populate_cache(self, row):
            # Logical ids - Whole row
            te_key = get_te_key(
                    account_number_bban=row[row_def[FD.Account_bban]],
                    date=row[row_def[FD.Date]],
                    counter_account_number=row[row_def[FD.Counter_account_number]],
                    comments=row[row_def[FD.Comments]])
            self._mutations_by_te_key[te_key] = row

            # Booking codes
            self._booking_codes.add(row[row_def[FD.Booking_id]])

            # Remarks
            remarks = row[row_def[FD.Remarks]]
            if remarks:
                self._remarks_by_te_key[te_key] = remarks

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.UserMutationsCache()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
