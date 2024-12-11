from abc import ABC

from src.DL.Config import CF_REMARKS
from src.DL.DBDriver.Att import Att
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD
from src.DL.Table import Table
from src.GL.Const import EMPTY, MUTATION_PGM_TE
from src.GL.Validate import isInt
from src.VL.Data.Constants.Const import LEEG
from src.VL.Data.Constants.Enums import Pane

PGM = MUTATION_PGM_TE
TABLE = Table.TransactionEnriched


class TransactionIO(BaseIO, ABC):

    def __init__(self):
        super().__init__(TABLE)
        self._te_def = self._model.get_colno_per_att_name(TABLE, zero_based=False)
        self._year_def = self._model.get_colno_per_att_name(Table.Year, zero_based=False)
        self._month_def = self._model.get_colno_per_att_name(Table.Month, zero_based=False)
        self._yy = 0
        self._mm = 0
        self._EOF = False
        self._completion_message = EMPTY

    def save_pending_remarks(self) -> bool:
        """
        Called when another event than "remarks" is triggered.
        BEFORE a new CF_ID is set in the config.
        """
        pending_remarks = self._CM.get_config_item(CF_REMARKS)
        pending_Id = self._CM.get_config_item(f'CF_ID_{Pane.TE}')
        if not pending_remarks or not isInt(pending_Id) or pending_Id == 0:
            return False

        # If emptied, really set it to empty.
        if pending_remarks == LEEG:
            pending_remarks = EMPTY

        # Update pending remark
        self._db.update(TABLE, values=[Att(FD.Remarks, pending_remarks)], where=[Att(FD.ID, pending_Id)], pgm=PGM)

        # Initialize remark
        self._CM.set_config_item(CF_REMARKS, EMPTY)
        return True

    def update_booking(self, values, where) -> int:
        if self._db.update(TABLE, where=where, values=values, pgm=MUTATION_PGM_TE):
            return self._db.count(TABLE, where=where)
        return 0
