#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Config import CF_BOOKING_SEQNO, CF_BOOKING_TYPE, CF_BOOKING_MAINGROUP, \
    CF_BOOKING_SUBGROUP, CF_BOOKING_CODE, CF_BOOKING_PROTECTED
from src.DL.IO.BookingIO import BookingIO
from src.DL.Objects.Booking import Booking
from src.VL.Controllers.BookingCodeController import BookingCodeController
from src.VL.Data.Constants.Const import CMD_OK
from src.VL.Data.WTyp import WTyp
from src.VL.Models.BookingCodeModel import BookingCodeModel
from src.VL.Views.BookingCodeView import BookingCodeView
from src.VL.Windows.ListItemWindow import ListItemWindow


class BookingCodeWindow(ListItemWindow):

    def __init__(self, command, Id):
        super().__init__('BookingWindow', f'Boeking {command}', command)
        # MVC
        self._model = BookingCodeModel(command, obj=BookingIO().id_to_obj(Id))
        self._view = BookingCodeView(self._model)
        self._controller = BookingCodeController(self._model)

    def _event_handler(self, event, values):
        # Set model
        if event == self.gui_key(CMD_OK, WTyp.BT):
            self._model.object = Booking(
                booking_type=values.get(self.gui_key(CF_BOOKING_TYPE, WTyp.CO)),
                booking_maingroup=values.get(self.gui_key(CF_BOOKING_MAINGROUP, WTyp.IN)),
                booking_subgroup=values.get(self.gui_key(CF_BOOKING_SUBGROUP, WTyp.IN)),
                booking_code=values.get(self.gui_key(CF_BOOKING_CODE, WTyp.IN)),
                seqno=values.get(self.gui_key(CF_BOOKING_SEQNO, WTyp.IN)),
                protected=values.get(self.gui_key(CF_BOOKING_PROTECTED, WTyp.IN))
            )
        # Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result
        self._set_close_window()
