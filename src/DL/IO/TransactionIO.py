from abc import ABC

from src.DL.Config import CF_REMARKS
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD
from src.DL.Table import Table
from src.GL.GeneralException import GeneralException
from src.VL.Data.Constants.Const import LEEG, OTHER_COSTS, OTHER_REVENUES
from src.VL.Data.Constants.Enums import Pane
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Const import EMPTY, MUTATION_PGM_TE
from src.GL.Validate import isInt

CM = ConfigManager()

PGM = MUTATION_PGM_TE
TABLE = Table.TransactionEnriched


class TransactionIO(BaseIO, ABC):

    @property
    def total_amount(self):
        return self._total_amount

    @property
    def month_max(self):
        return self._month_max

    def __init__(self):
        super().__init__(TABLE)
        self._te_def = self._model.get_colno_per_att_name(TABLE, zero_based=False)
        self._year_def = self._model.get_colno_per_att_name(Table.Year, zero_based=False)
        self._month_def = self._model.get_colno_per_att_name(Table.Month, zero_based=False)
        self._yy = 0
        self._mm = 0
        self._EOF = False
        self._completion_message = EMPTY
        self._total_amount = 0.0
        self._month_max = 0

    def save_pending_remarks(self) -> bool:
        """
        Called when another event than "remarks" is triggered.
        BEFORE a new CF_ID is set in the config.
        """
        pending_remarks = CM.get_config_item(CF_REMARKS)
        pending_Id = CM.get_config_item(f'CF_ID_{Pane.TE}')
        if not pending_remarks or not isInt(pending_Id) or pending_Id == 0:
            return False

        # If emptied, really set it to empty.
        if pending_remarks == LEEG:
            pending_remarks = EMPTY

        # Update pending remark
        self._db.update(TABLE, values=[Att(FD.Remarks, pending_remarks)], where=[Att(FD.ID, pending_Id)], pgm=PGM)

        # Initialize remark
        CM.set_config_item(CF_REMARKS, EMPTY)
        return True

    def update_booking(self, values, where) -> int:
        if self._db.update(TABLE, where=where, values=values, pgm=MUTATION_PGM_TE):
            return self._db.count(TABLE, where=where)
        return 0

    def get_realisation_data(self, year) -> list:
        """ @return: [type, maingroup, subgroup, amount]"""
        self._total_amount = 0.0
        d = {}
        b_def = self._model.get_colno_per_att_name(Table.BookingCode, zero_based=False)
        mutations = self._db.select(TABLE, where=[Att(FD.Year, year)])
        for m_row in mutations:
            self._month_max = max(self._month_max, m_row[self._te_def[FD.Month]])
            booking_id = m_row[self._te_def[FD.Booking_id]]
            if not booking_id:
                booking_maingroup = OTHER_COSTS if m_row[self._te_def[FD.Amount_signed]] < 0 else OTHER_REVENUES
                booking_id = self._db.fetch_id(Table.BookingCode, where=[Att(FD.Booking_maingroup, booking_maingroup)])
                if not booking_id:
                    raise GeneralException(
                        f'{PGM}: Gereserveerde boeking {booking_maingroup} is niet gevonden in tabel {Table.BookingCode}.')
            b_row = self._db.fetch_one(Table.BookingCode, where=[Att(FD.ID, booking_id)])
            amount = m_row[self._te_def[FD.Amount_signed]]
            self._total_amount += amount
            key = (f'{b_row[b_def[FD.Booking_type]]}|'
                   f'{b_row[b_def[FD.Booking_maingroup]]}|'
                   f'{b_row[b_def[FD.Booking_subgroup]]}')
            if key in d:
                d[key] += amount
            else:
                d[key] = amount

        return [self._add_condensed_row(key, amount) for key, amount in d.items()]

    @staticmethod
    def _add_condensed_row(key, amount):
        cr = key.split('|')
        cr.append(amount)
        return cr

    def get_transactions(self, year, month_from, month_to) -> list:
        """
        Either for 1 month or for multiple months (e.g. quarterly).
        Sorted on date (asc).
        """
        where = [Att(FD.Year, year)]
        if month_from == month_to:
            where.extend([Att(FD.Month, month_from)])
        else:
            where.extend([
                Att(FD.Month, month_from, relation=SQLOperator().GE),
                Att(FD.Month, month_to, relation=SQLOperator().LE)
            ])
        rows = self._db.select(TABLE, where=where, order_by=[[Att(FD.Date), 'ASC']])
        self._total_amount = sum(row[self._te_def[FD.Amount_signed]] for row in rows)
        return rows
