import PySimpleGUI as sg

from src.DL.Config import CF_COMBO_SUMMARY, CF_SUMMARY_YEAR
from src.DL.Enums.Enums import Summary
from src.DL.Model import FD
from src.VL.Data.Constants.Const import CMD_OK, CMD_CANCEL, STATUS_MESSAGE
from src.VL.Data.DataDriver import Singleton as DataDriver
from src.VL.Views.BaseView import BaseView
from src.GL.Const import EMPTY

DD = DataDriver()


class SummaryView(BaseView):

    def __init__(self):
        super().__init__()

    def get_view(self) -> list:
        combo_key = 'Kies het soort overzicht'
        x = len(combo_key)
        self._statusbar_width = x
        lists = [
            self.frame('input', [
                self.combo(CF_COMBO_SUMMARY, items=Summary.values(), x=x, evt=True),
                self.frame(CF_SUMMARY_YEAR, [
                    self.combo(CF_SUMMARY_YEAR, items=DD.get_combo_items(FD.Year), x=x)
                ], p=0),
            ]),
            self.multi_frame('Buttons', [[self.button(CMD_OK), self.button(CMD_CANCEL)]], justify='right',
                             expand_x=True, p=2)
        ]

        return [
            [self.frame('SelectionBox', lists, p=0)],
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5), size=(self._statusbar_width, 1), expand_x=True,
                          relief=sg.RELIEF_SUNKEN)],
        ]
