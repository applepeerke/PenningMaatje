#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

from src.DL.DBDriver.Att import Att
from src.DL.IO.BookingIO import BookingIO
from src.DL.Model import FD
from src.DL.Table import Table
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager
from src.VL.Controllers.ListItemController import ListItemController
from src.VL.Data.Constants.Enums import BoxCommand
from src.DL.Lexicon import BOOKING_CODE
from src.VL.Models.BookingModel import BookingModel
from src.GL.Const import EMPTY


class BookingController(ListItemController):

    def __init__(self, model: BookingModel):
        super().__init__(
            obj_name=BOOKING_CODE,
            model=model,
            table_name=Table.Booking,
            io=BookingIO,
            required=[
                Att(FD.Booking_type, model.object.booking_type),
                Att(FD.Booking_maingroup, model.object.booking_maingroup)
            ],
            pk=[Att(FD.Booking_type), Att(FD.Booking_maingroup), Att(FD.Booking_subgroup)]
        )
        self._UM = UserCsvFileManager()

    def edit(self):
        super().edit()
        if not self._result.OK or self._model.command not in (BoxCommand.Delete, BoxCommand.Rename):
            return

        # Delete/Rename: Update booking code in csv files of most recent backup/restore folder.
        to_name = EMPTY if self._model.command == BoxCommand.Delete else self._model.object.booking_code
        self._result = self._UM.rename_and_clean_booking_in_user_csv_files(
            from_name=self._model.object_old.booking_code, to_name=to_name)
