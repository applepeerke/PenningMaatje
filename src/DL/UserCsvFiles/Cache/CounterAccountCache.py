#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Functions import get_BBAN_from_IBAN
from src.DL.DBDriver.Enums import FetchMode
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.GL.BusinessLayer.SessionManager import Singleton as Session


class Singleton:
    """ Singleton """

    class CounterAccountCache(object):

        @property
        def booking_codes(self):
            return self._booking_codes

        def __init__(self):
            self._booking_codes = {}
            self._ibans_by_id = {}
            self._bbans_by_id = {}
            self._ids_by_iban = {}
            self._initialized = False

        def initialize(self, force=False):
            if self._initialized and not force:
                return

            self._initialized = True
            model = Model()
            d = model.get_colno_per_att_name(Table.CounterAccount, zero_based=False)
            rows = Session().db.fetch(Table.CounterAccount, mode=FetchMode.WholeTable)

            for row in rows:
                iban = row[d[FD.Counter_account_number]]
                bban = self.get_BBAN_from_IBAN(iban)
                Id = row[0]
                # Boeking
                if bban not in self._booking_codes:
                    self._booking_codes[bban] = row[d[FD.Booking_code]]
                self._ibans_by_id[Id] = iban
                self._bbans_by_id[Id] = bban
                self._ids_by_iban[row[d[FD.Counter_account_number]]] = Id

        def get_bban_from_id(self, ID) -> int:
            self.initialize()  # 1st time
            return self._bbans_by_id.get(ID, EMPTY)

        def get_iban_from_id(self, ID) -> int:
            self.initialize()  # 1st time
            return self._ibans_by_id.get(ID, EMPTY)

        def get_id_from_iban(self, IBAN) -> int:
            self.initialize()  # 1st time
            return self._ids_by_iban.get(IBAN, 0)

        def get_BBAN_from_IBAN(self, value):
            self.initialize()
            return get_BBAN_from_IBAN(value)

        def get_booking_code(self, bban):
            self.initialize()
            return self.booking_codes.get(bban, EMPTY)

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.CounterAccountCache()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
