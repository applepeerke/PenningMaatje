#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Table import Table
from src.VL.Controllers.ListController import ListController
from src.VL.Data.Constants.Enums import WindowType, Pane
from src.DL.Lexicon import SEARCH_TERMS, MAINTAIN, BOOKING_CODES
from src.VL.Functions import set_focus_on_row
from src.VL.Models.ListModel import ListModel
from src.VL.Views.ListView import ListView
from src.VL.Windows.BaseWindow import BaseWindow
from src.VL.Windows.BookingWindow import BookingWindow
from src.VL.Windows.SearchTermWindow import SearchTermWindow
from src.GL.Validate import isInt


class ListWindow(BaseWindow):

    @property
    def row_no(self):
        return self._row_no

    def __init__(self, view, controller):
        super().__init__(view.model.title, view.model.title, WindowType.List)
        # MVC
        self._model = view.model
        self._view = view
        self._controller = controller
        self._row_no = 0

    def _event_handler(self, event, values):
        window_table = self._window[self.key_of(self._model.table_name)]

        # Row selected
        if isinstance(event, tuple) and len(event) == 3:
            # Clicked on 1st row in empty list (None, 0) or on header (-1, 0)
            if not isInt(event[2][0]) or event[2][0] == -1:
                return
            self._row_no = event[2][0]
            self._set_focus(window_table)
            return

        # Other events
        self._controller.handle_event(event, self._Id)
        self._result = self._controller.result
        if not self._result.OK:
            return

        # Edit done: Update window rows
        self._model.set_data(self._model.DD.fetch_set(self._model.table_name, where=self._model.pk))
        window_table.update(values=self._model.rows)
        self._set_focus(window_table)

    def _set_focus(self, window_table):
        """
        Set row focus. Also reset the Id for when a row was deleted.
        Rows contain header only (if no details) or else details only. So 1 row at a minimum.
        After delete row_no may not exist anymore.
        """
        # Correction for detail-row-no if only 1 row is present (maybe header or detail)
        if len(self._model.rows) > 1:
            current_row_no = self._row_no
        elif len(self._model.rows) == 1 and isInt(self._model.rows[0][0]):
            current_row_no = 0
        else:
            current_row_no = -1
        set_focus_on_row(window_table, current_row_no)
        # Prevent index error after deletion of a row
        row_no = min(self._row_no, len(self._model.rows) - 1)
        self._Id = self._model.rows[row_no][0] if current_row_no > -1 else 0


"""
Sub classes
"""


class BookingsWindow(ListWindow):

    def __init__(self):
        super().__init__(
            view=ListView(Pane.BS, ListModel(Table.Booking, f'{MAINTAIN} {BOOKING_CODES}')),
            controller=ListController(BookingWindow)
        )


class SearchTermsWindow(ListWindow):

    def __init__(self):
        super().__init__(
            view=ListView(Pane.SS, model=ListModel(Table.SearchTerm, f'{MAINTAIN} {SEARCH_TERMS}')),
            controller=ListController(SearchTermWindow)
        )
