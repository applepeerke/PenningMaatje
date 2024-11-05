import PySimpleGUI as sg

from src.DL.Model import FD
from src.VL.Data.Constants.Color import STATUSBAR_COLOR_ERROR, COLOR_BACKGROUND_DISABLED
from src.VL.Data.Constants.Const import CMD_OK, STATUS_MESSAGE, CMD_CANCEL, \
    SEARCH_TERM, SEARCH_TERM_BOOKING_DESCRIPTION
from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Models.SearchTermModel import SearchTermModel
from src.VL.Views.BaseView import BaseView
from src.GL.Const import EMPTY
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache

BKM = BookingCache()

PGM = 'SearchTermView'


class SearchTermView(BaseView):

    def __init__(self, model: SearchTermModel):
        super().__init__()
        self._model = model

    def get_view(self) -> list:
        booking_descriptions = [x for x in BKM.get_booking_code_descriptions(include_protected=True)]
        x_desc = max(len(d) for d in booking_descriptions)
        x = max(
            len(SEARCH_TERM),
            len(SEARCH_TERM_BOOKING_DESCRIPTION),
        )

        self._statusbar_width = max(x_desc, 45)
        lists = [
            self.inbox(SEARCH_TERM, dft=self._model.object.search_term, x=x,
                       disabled=self._model.command not in (BoxCommand.Rename, BoxCommand.Add)),
            # In sg, booking must be a unique name, so CAT can not be used.
            self.combo(SEARCH_TERM_BOOKING_DESCRIPTION, sorted(booking_descriptions),
                       dft=BKM.get_value_from_booking_code(self._model.object.booking_code, FD.Booking_description),
                       x=x, background_color=COLOR_BACKGROUND_DISABLED,
                       disabled=self._model.command not in (BoxCommand.Update, BoxCommand.Add)),
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, size=(
                self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN,
                          text_color=STATUSBAR_COLOR_ERROR)],
            self.multi_frame('Buttons', [[self.button(CMD_OK)], [self.button(CMD_CANCEL)]])
        ]
        return [self.frame('CRUDBox', lists, p=0)]
