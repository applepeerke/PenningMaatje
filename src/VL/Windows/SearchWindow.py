#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Config import CF_SEARCH_AMOUNT, \
    CF_SEARCH_AMOUNT_TO, CF_SEARCH_YEAR, CF_SEARCH_MONTH, CF_SEARCH_TEXT, CF_SEARCH_COUNTER_ACCOUNT, \
    CF_SEARCH_TRANSACTION_CODE, CMD_SEARCH, CF_SEARCH_REMARKS, CF_SEARCH_BOOKING_CODE
from src.DL.Config import CMD_SEARCH_RESET, CMD_EXPORT, FRAME_SEARCH_TOTAL, CF_SEARCH_AMOUNT_TOTAL
from src.DL.Model import Model
from src.DL.Table import Table
from src.VL.Controllers.SearchController import SearchController
from src.VL.Data.Constants.Enums import WindowType, Pane
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import get_name_from_key
from src.VL.Models.SearchModel import SearchModel
from src.VL.Views.SearchView import SearchView
from src.VL.Windows.BaseWindow import BaseWindow
from src.GL.Const import EMPTY


class SearchWindow(BaseWindow):

    def __init__(self, main_model, main_window):
        """ TransActionIO is a plugin """
        super().__init__('SearchWindow', 'Zoekscherm', WindowType.Detail_with_statusbar)
        self._main_models = main_model.models
        self._main_window = main_window
        self._transactionsIO = TransactionsIO()
        # MVC
        self._model = SearchModel()
        self._view = SearchView(self._model)
        self._controller = SearchController(self._model, self._transactionsIO)

    def _event_handler(self, event, values):

        # Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result
        if not self._result.OK:
            return

        # Set view in main window
        event_key = get_name_from_key(event)
        if event_key == CMD_SEARCH:
            self._set_main_view()

        elif event_key == CMD_SEARCH_RESET:
            self._clear_window()

        # Close the window after search or export.
        if event_key == CMD_SEARCH \
                or event_key == CMD_EXPORT:
            self._close_window = True

    def _set_main_view(self):
        # Total amount
        self._CM.set_config_item(CF_SEARCH_AMOUNT_TOTAL, self._transactionsIO.total)
        self._window[self._view.gui_key(CF_SEARCH_AMOUNT_TOTAL, WTyp.IN)].update(value=self._transactionsIO.total)
        # Update main models: transactions and transaction pane
        self._update_main()

    def _appearance_before(self):
        self._window[self.gui_key(FRAME_SEARCH_TOTAL, WTyp.FR)].update(
            visible=len(self._main_models[Pane.TE].rows) > 0)
        # Disabled
        self._window[self.gui_key(CMD_SEARCH_RESET, WTyp.BT)].update(
            disabled=not self._CM.is_any_search_criterium_specified())

    def _update_main(self):
        if not self._transactionsIO.rows or not self._main_window:
            return
        # Update Transactions pane: set header, formatted rows and focus
        table_name = Table.TransactionEnriched
        rows = [Model().get_report_colhdg_names(table_name)]
        rows.extend(self._transactionsIO.rows)
        self._main_models[Pane.TE].set_data(rows)
        self._main_window.refresh_transactions_from_model()

    def _clear_window(self):
        self._window[self.gui_key(CF_SEARCH_YEAR, WTyp.CO)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_MONTH, WTyp.CO)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_COUNTER_ACCOUNT, WTyp.CO)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_BOOKING_CODE, WTyp.CO)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_TRANSACTION_CODE, WTyp.CO)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_TEXT, WTyp.IN)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_REMARKS, WTyp.CB)].update(value=False)
        self._window[self.gui_key(CF_SEARCH_AMOUNT, WTyp.IN)].update(value=EMPTY)
        self._window[self.gui_key(CF_SEARCH_AMOUNT_TO, WTyp.IN)].update(value=EMPTY)
