#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Config import CF_IMPORT_PATH_BOOKINGS, CF_IMPORT_PATH_COUNTER_ACCOUNTS, \
    configDef, LEEG, CF_IMPORT_PATH_SEARCH_TERMS
from src.DL.DBDriver.Enums import FetchMode
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY
from src.GL.Enums import Color, MessageSeverity
from src.GL.Result import Result
from src.GL.Validate import toBool
from src.VL.Data.Constants.Const import PROTECTED_BOOKINGS, NIET_LEEG

model = Model()
CM = ConfigManager()

PGM = 'BookingCodeCache'


class Singleton:
    """ Singleton """

    class BookingCodeCache(object):

        @property
        def booking_codes(self):
            return self._booking_codes

        @property
        def formatted_booking_descriptions(self):
            return self._formatted_booking_descriptions

        def __init__(self):
            self._booking_codes = set()
            self._formatted_booking_descriptions = set()
            self._booking_codes_including_not_protected = []
            self._formatted_descriptions_including_not_protected = []
            self._formatted_descriptions = []
            self._protected_maingroup_booking_codes = {}
            self._ids_by_key = {}
            self._ids_by_code = {}

            # Atts
            self._types_by_id = {}
            self._maingroups_by_id = {}
            self._subgroups_by_id = {}
            self._codes_by_id = {}

            # Logical key
            self._codes_by_lk = {}
            self._seqno_by_lk = {}

            self._initialized = False
            self._result = Result()

        def initialize(self, force=False):
            if self._initialized and not force:
                return

            d = model.get_colno_per_att_name(Table.BookingCode, zero_based=False)
            rows = Session().db.fetch(Table.BookingCode, mode=FetchMode.WholeTable)
            if not rows:
                return

            self._initialized = True

            [self._process_booking_row(row, d) for row in rows]
            self._formatted_descriptions = [
                self._get_formatted_desc(booking_code) for booking_code in self._booking_codes]

            self._booking_codes_including_not_protected = sorted([row[d[FD.Booking_code]] for row in rows])
            self._formatted_descriptions_including_not_protected = [
                self._get_formatted_desc(booking_code) for booking_code in self._booking_codes_including_not_protected]
            self._protected_maingroup_booking_codes = {maingroup: EMPTY for maingroup in PROTECTED_BOOKINGS}

        def get_booking_code(self, name, comment, remark=None) -> str:
            self.initialize()

            booking_code = self.get_booking_code_from_item(name)
            if not booking_code:
                booking_code = self.get_booking_code_from_item(comment)
            if not booking_code and remark:
                booking_code = self.get_booking_code_from_item(remark)
            return booking_code

        def get_booking_code_from_item(self, item) -> str:
            """ Get the booking_code present in the 1st matching item """
            booking_codes = [booking_code for booking_code in self._booking_codes
                             if len(booking_code) > 2 and booking_code in item]
            return booking_codes[0] if booking_codes else EMPTY

        def _process_booking_row(self, row, d):
            type = row[d[FD.Booking_type]]
            maingroup = row[d[FD.Booking_maingroup]]
            subgroup = row[d[FD.Booking_subgroup]]
            seqno = int(row[d[FD.SeqNo]])
            lk = self.get_lk(type, maingroup, subgroup)

            booking_code = row[d[FD.Booking_code]]
            protected = toBool(row[d[FD.Protected]])
            # Dicts
            self._types_by_id[row[0]] = type
            self._maingroups_by_id[row[0]] = maingroup
            self._subgroups_by_id[row[0]] = subgroup

            self._codes_by_id[row[0]] = booking_code
            self._codes_by_lk[lk] = booking_code
            self._seqno_by_lk[lk] = seqno
            self._ids_by_code[booking_code] = row[0]

            # Sets (after dicts, to be able to get the description)
            self._booking_codes.add(booking_code)
            self._formatted_booking_descriptions.add(self._get_formatted_desc(booking_code))
            if protected:
                self._protected_maingroup_booking_codes[maingroup] = booking_code

        def get_booking_code_descriptions(self, include_protected=False):
            self.initialize()  # 1st time
            return self._formatted_descriptions if include_protected \
                else self._formatted_descriptions_including_not_protected

        def _get_formatted_desc(self, booking_code) -> str:
            return (f'{self.get_value_from_booking_code(booking_code, FD.Booking_maingroup)} '
                    f'{self.get_value_from_booking_code(booking_code, FD.Booking_subgroup)}')

        def get_code_from_combo_desc(self, formatted_desc) -> str:
            """ SearchView combo booking description has a formatted description without the code. """
            # Special values for Empty-booking-code mode
            if formatted_desc in (LEEG, NIET_LEEG):
                return formatted_desc

            for lk, code in self._codes_by_lk.items():
                keys = lk.split('|')
                if (formatted_desc.startswith(keys[1]) and
                        (keys[2] and formatted_desc.endswith(keys[2]) or
                         (not keys[2] and formatted_desc.strip() == keys[1].strip()))):
                    return code
            return EMPTY

        @staticmethod
        def get_lk(booking_type, maingroup, subgroup):
            return f'{booking_type}|{maingroup}|{subgroup}'

        def get_booking_code_from_lk(self, booking_type, maingroup, subgroup) -> str:
            lk = self.get_lk(booking_type, maingroup, subgroup)
            booking_code = self._codes_by_lk.get(lk, EMPTY)
            # Items without maingroup (like "Overboeking") may get type as maingroup (like "Overboeking Overboeking")
            if not booking_code and not maingroup and not subgroup:
                lk = self.get_lk(booking_type, booking_type, subgroup)
                booking_code = self._codes_by_lk.get(lk, EMPTY)
                # Still no code, get the highest level (e.g. "5"; do not select "5.1")
                if not booking_code:
                    for k, v in self._codes_by_lk.items():
                        if k.startswith(booking_type) and len(v) == 1:
                            return v
            return booking_code

        def get_seqno_from_lk(self, lk) -> int:
            return self._seqno_by_lk.get(lk, 9999)

        def get_value_from_id(self, ID, att_name, dft=EMPTY) -> EMPTY:
            """ Get a value from the id """
            if ID == 0:
                return dft
            self.initialize()  # 1st time
            if att_name == FD.Booking_type:
                return self._types_by_id.get(ID, dft)
            elif att_name == FD.Booking_maingroup:
                return self._maingroups_by_id.get(ID, dft)
            elif att_name == FD.Booking_subgroup:
                return self._subgroups_by_id.get(ID, dft)
            elif att_name == FD.Booking_code:
                return self._codes_by_id.get(ID, dft)
            elif att_name == FD.Booking_description:
                booking_code = self._codes_by_id.get(ID, dft)
                return self._get_formatted_desc(booking_code)
            else:
                return dft

        def get_value_from_booking_code(self, booking_code, att_name, dft=EMPTY) -> EMPTY:
            """ Get a value from the id """
            self.initialize()  # 1st time
            ID = self.get_id_from_code(booking_code)
            return self.get_value_from_id(ID, att_name, dft)

        def get_id_from_code(self, booking_code) -> int:
            """ Get the id from the booking code """
            self.initialize()  # 1st time
            return self._ids_by_code.get(booking_code, 0)

        def get_protected_booking_code(self, protected_maingroup) -> list:
            """ Get booking code from protected maingroup """
            self.initialize()  # 1st time
            return self._protected_maingroup_booking_codes[protected_maingroup]

        def get_codes_from_ids(self, ids):
            """ Get the booking codes from the specified ids """
            self.initialize()  # 1st time
            return [self.get_value_from_id(ID, FD.Booking_code, dft=LEEG) for ID in ids]

        def is_valid_config(self) -> Result:
            self._result = Result()
            self._check_config_item(CF_IMPORT_PATH_BOOKINGS)
            self._check_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS)
            self._check_config_item(CF_IMPORT_PATH_SEARCH_TERMS)
            return self._result

        def _check_config_item(self, key):
            if CM.get_config_item(key):
                return
            self._result.add_message(
                f'{Color.ORANGE}Waarschuwing{Color.NC} - '
                f'{configDef.get(key).label} is leeg.', MessageSeverity.Warning)

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.BookingCodeCache()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
