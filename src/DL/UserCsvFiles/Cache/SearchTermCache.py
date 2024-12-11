#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-02-12 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.Base import Base
from src.DL.DBDriver.Enums import FetchMode
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.Const import EMPTY

TABLE = Table.SearchTerm


class Singleton:
    """ Singleton """

    class SearchTermCache(Base):

        @property
        def search_terms(self):
            return self._search_terms

        def __init__(self):
            super().__init__()
            self._search_terms = {}
            self._initialized = False

        def initialize(self, force=False):
            if self._initialized and not force:
                return

            self._initialized = True
            model = Model()
            d = model.get_colno_per_att_name(TABLE, zero_based=False)

            # Get the {searchterm : booking_code} mapping.
            rows = self._session.db.fetch(TABLE, mode=FetchMode.WholeTable)
            self._search_terms = {
                row[d[FD.SearchTerm]].lower(): row[d[FD.Booking_code]]
                for row in rows
            }

        def get_booking_code(self, name, comment, remark=None) -> str:
            self.initialize()

            booking_code = self.get_booking_code_from_item(name)
            if not booking_code:
                booking_code = self.get_booking_code_from_item(comment)
            if not booking_code and remark:
                booking_code = self.get_booking_code_from_item(remark)
            return booking_code

        def get_booking_code_from_item(self, item) -> str:
            """ Get the booking_code belonging to the 1st matching search term """
            booking_codes = [
                booking_code for search_term, booking_code in self._search_terms.items()
                if search_term in item.lower()
            ]
            return booking_codes[0] if booking_codes else EMPTY

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.SearchTermCache()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
