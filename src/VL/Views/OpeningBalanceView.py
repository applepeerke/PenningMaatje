import PySimpleGUI as sg

from src.VL.Models.ListItemModel import ListItemModel
from src.DL.Lexicon import OPENING_BALANCE, YEAR
from src.GL.Const import EMPTY
from src.VL.Data.Constants.Color import STATUSBAR_COLOR_ERROR, COLOR_BACKGROUND_DISABLED
from src.VL.Data.Constants.Const import CMD_OK, STATUS_MESSAGE, CMD_CANCEL
from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Views.BaseView import BaseView

PGM = 'OpeningBalanceView'


class OpeningBalanceView(BaseView):

    def __init__(self, model: ListItemModel):
        super().__init__()
        self._model = model

    def get_view(self) -> list:
        x = max(
            len(OPENING_BALANCE),
            len(YEAR),
        )

        self._statusbar_width = max(x, 45)
        lists = [
            self.inbox(YEAR, dft=self._model.object.year, x=x,
                       disabled=self._model.command not in (BoxCommand.Rename, BoxCommand.Add)),
            # In sg, booking must be a unique name, so CAT can not be used.
            self.inbox(OPENING_BALANCE, dft=self._model.object.opening_balance, x=x,
                       background_color=COLOR_BACKGROUND_DISABLED,
                       disabled=self._model.command not in (BoxCommand.Update, BoxCommand.Add)),
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, size=(
                self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN,
                          text_color=STATUSBAR_COLOR_ERROR)],
            self.multi_frame('Buttons', [[self.button(CMD_OK)], [self.button(CMD_CANCEL)]])
        ]
        return [self.frame('CRUDBox', lists, p=0)]