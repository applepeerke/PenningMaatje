#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.DBDriver.Att import Att
from src.DL.IO.SearchTermIO import SearchTermIO
from src.DL.Model import FD
from src.DL.Objects.SearchTerm import SearchTerm
from src.DL.Table import Table
from src.VL.Controllers.ListItemController import ListItemController
from src.VL.Data.Constants.Const import CMD_OK, SEARCH_TERM_BOOKING_DESCRIPTION
from src.DL.Lexicon import SEARCH_TERM
from src.VL.Data.WTyp import WTyp
from src.VL.Models.SearchTermModel import SearchTermModel
from src.VL.Views.SearchTermView import SearchTermView
from src.VL.Windows.ListItemWindow import ListItemWindow
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache

BCM = BookingCache()


class SearchTermWindow(ListItemWindow):

    def __init__(self, command, Id):
        super().__init__('SearchTermWindow', f'Zoekterm {command}', command)
        # MVC
        self._model = SearchTermModel(command, obj=SearchTermIO().id_to_obj(Id))
        self._view = SearchTermView(self._model)
        self._controller = ListItemController(
            obj_name=SEARCH_TERM,
            model=self._model,
            table_name=Table.SearchTerm,
            io=SearchTermIO,
            required=[
                Att(FD.SearchTerm, self._model.object.search_term),
                Att(FD.Booking_code, self._model.object.booking_code)
            ],
            pk=[Att(FD.SearchTerm, self._model.object.search_term)]
        )

    def _event_handler(self, event, values):
        # Set model
        if event == self.gui_key(CMD_OK, WTyp.BT):
            self._model.object = SearchTerm(
                search_term=values.get(self.gui_key(SEARCH_TERM, WTyp.IN)),
                booking_code=BCM.get_booking_code_from_desc(
                    values.get(self.gui_key(SEARCH_TERM_BOOKING_DESCRIPTION, WTyp.CO))),
            )
        # Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result
        self._set_close_window()
