import PySimpleGUI as sg

from src.DL.Config import CF_BOOKING_TYPE, CF_BOOKING_PROTECTED, CF_BOOKING_COUNT, \
    CF_BOOKING_MAINGROUP, CF_BOOKING_SUBGROUP, CF_BOOKING_CODE, CF_BOOKING_SEQNO
from src.DL.Table import Table
from src.VL.Data.Constants.Color import STATUSBAR_COLOR_ERROR, COLOR_BACKGROUND_DISABLED
from src.VL.Data.Constants.Const import CMD_OK, STATUS_MESSAGE, CMD_CANCEL
from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Models.BookingCodeModel import BookingCodeModel
from src.VL.Views.BaseView import BaseView
from src.GL.Const import EMPTY

TABLE = Table.BookingCode


class BookingCodeView(BaseView):

    def __init__(self, model: BookingCodeModel):
        super().__init__()
        self._model = model
        self._booking = model.object

    def get_view(self) -> list:
        self._CM.set_config_item(CF_BOOKING_TYPE, self._booking.booking_type)
        self._CM.set_config_item(CF_BOOKING_MAINGROUP, self._booking.booking_maingroup)
        self._CM.set_config_item(CF_BOOKING_SUBGROUP, self._booking.booking_subgroup)
        self._CM.set_config_item(CF_BOOKING_CODE, self._booking.booking_code)
        self._CM.set_config_item(CF_BOOKING_SEQNO, self._booking.seqno)
        self._CM.set_config_item(CF_BOOKING_PROTECTED, self._booking.protected)

        x = max(
            len(CF_BOOKING_TYPE),
            len(CF_BOOKING_MAINGROUP),
            len(CF_BOOKING_SUBGROUP),
            len(CF_BOOKING_CODE),
            len(CF_BOOKING_SEQNO),
            len(CF_BOOKING_COUNT)
        )
        self._statusbar_width = x
        mode_new = self._model.command in (BoxCommand.Add, BoxCommand.Rename)
        mode_new_or_chg = self._model.command in (BoxCommand.Rename, BoxCommand.Add, BoxCommand.Update)
        lists = [self.combo(CF_BOOKING_TYPE, [x for x in self._model.booking_types], x=x,
                            background_color=COLOR_BACKGROUND_DISABLED,
                            disabled=not mode_new),
                 self.inbox(CF_BOOKING_MAINGROUP, x=x, disabled=not mode_new),
                 self.inbox(CF_BOOKING_SUBGROUP, x=x, disabled=not mode_new_or_chg),
                 self.inbox(CF_BOOKING_CODE, x=x, disabled=not mode_new_or_chg),
                 self.inbox(CF_BOOKING_SEQNO, x=x, disabled=not mode_new_or_chg),
                 self.frame(CF_BOOKING_COUNT, [
                     self.inbox(CF_BOOKING_COUNT, x=x, disabled=True)], p=0),
                 [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, size=(
                     self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN,
                               text_color=STATUSBAR_COLOR_ERROR)],
                 self.multi_frame('Buttons', [[self.button(CMD_OK)], [self.button(CMD_CANCEL)]])
                 ]
        return [self.frame('CRUDBox', lists, p=0)]
