#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.DBDriver.Att import Att
from src.DL.IO.OpeningBalanceIO import OpeningBalanceIO
from src.DL.Model import FD
from src.DL.Objects.OpeningBalance import OpeningBalance
from src.DL.Table import Table
from src.VL.Controllers.ListItemController import ListItemController
from src.VL.Data.Constants.Const import CMD_OK
from src.DL.Lexicon import OPENING_BALANCE, YEAR
from src.VL.Data.WTyp import WTyp
from src.VL.Models.ListItemModel import ListItemModel
from src.VL.Views.OpeningBalanceView import OpeningBalanceView
from src.VL.Windows.ListItemWindow import ListItemWindow


class OpeningBalanceWindow(ListItemWindow):

    def __init__(self, command, Id):
        super().__init__('OpeningBalanceWindow', f'{OPENING_BALANCE} {command}', command)
        # MVC
        self._model = ListItemModel(Table.OpeningBalance, command, obj=OpeningBalanceIO().id_to_obj(Id))
        self._view = OpeningBalanceView(self._model)
        self._controller = ListItemController(
            obj_name=OPENING_BALANCE,
            model=self._model,
            table_name=Table.OpeningBalance,
            io=OpeningBalanceIO,
            required=[Att(FD.Year, self._model.object.year)],
            pk=[Att(FD.Year, self._model.object.year)]
        )

    def _event_handler(self, event, values):
        # Set model
        if event == self.gui_key(CMD_OK, WTyp.BT):
            self._model.object = OpeningBalance(
                year=values.get(self.gui_key(YEAR, WTyp.IN)),
                opening_balance=values.get(self.gui_key(OPENING_BALANCE, WTyp.IN)),
            )
        # Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result
        self._set_close_window()
