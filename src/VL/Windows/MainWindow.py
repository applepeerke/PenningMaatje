#!/usr/bin/env python3
from src.DL.Config import CF_IBAN, CF_REMARKS, CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.Table import Table
from src.VL.Controllers.MainController import MainController
from src.VL.Data.Constants.Color import TEXT_COLOR
from src.VL.Data.Constants.Const import TAB_LOG, FRAME_TOP_RIGHT, FRAME_TOP_BUTTONS_OPTIONAL, \
    FRAME_PANE_YEAR_MONTH, FRAME_PANE_TRANSACTIONS, FRAME_PANE_TRANSACTION, \
    CMD_SEARCH, DATE, FRAME_TX_DATETIME, \
    CMD_CONSISTENCY, CMD_RESTORE, FRAME_TRANSACTION_BOOKING, CMD_UNDO, CMD_EXPORT
from src.VL.Data.Constants.Enums import WindowType, Pane
from src.DL.Lexicon import ACCOUNT_NUMBER, COUNTER_ACCOUNT, CMD_IMPORT_TE, NAME, MUTATION_TYPE, \
    TRANSACTION_CODE, AMOUNT, REMARKS, TRANSACTION_DATE, TRANSACTION_TIME, COMMENTS
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import get_name_from_key, get_name_from_text, set_focus_on_row
from src.VL.Models.MainModel import MainModel
from src.VL.Views.MainView import MainView
from src.VL.Windows.BaseWindow import BaseWindow
from src.GL.Const import EMPTY, APP_TITLE
from src.GL.Result import Result


class MainWindow(BaseWindow):

    @property
    def model(self):  # Unit test
        return self._model

    def __init__(self, unit_test=False, diagnostic_mode=False):
        super().__init__('MainWindow', APP_TITLE, WindowType.Main)
        # MVC - C which populates M, populated M is needed to create V.
        self._model = MainModel()
        self._controller = MainController(self._model, self, unit_test, diagnostic_mode)
        self._view = MainView(self._model)
        self._transactionsIO = TransactionsIO()

    def display(self):
        # Check for initialization failure
        self._result = self._controller.result
        if not self._result.OK:
            return
        super().display()
        # Close
        result = self._controller.result
        if self._close_clicked or result.EX or result.RT:
            self._controller.close()
            self._result = result if result.EX or result.RT else self._controller.result

    def _preparation(self):
        """ 1. Build the panes. """
        self._controller.start_up()
        self._model.dashboard_refreshed = True

    def _get_window(self, **kwargs):
        """ 2. Create sg window """
        return super()._get_window(keep_on_top=False)

    def _appearance_before(self):
        """ 3.1 First step in the event loop """
        has_data = self._controller.has_data()
        has_undo = self._controller.has_undo()
        # Dashboard content
        if has_data and self._model.dashboard_refreshed:
            self._model.dashboard_refreshed = False
            self._set_dashboard()
        # - Dashboard panes
        # Tabs
        self._window[TAB_LOG].update(visible=self._controller.has_log_data())
        # Dashboard
        # - Top
        self._window[self.gui_key(FRAME_TOP_RIGHT, WTyp.FR)].update(visible=has_data)
        self._window[self.gui_key(FRAME_TOP_BUTTONS_OPTIONAL, WTyp.FR)].update(visible=has_data)
        self._window[self.gui_key(CMD_UNDO, WTyp.BT)].update(visible=has_undo)
        # - Accounts
        self._window[self.gui_key(CF_IBAN, WTyp.CO)].update(disabled=len(self._model.account_numbers) < 2)
        # - Panes
        self._window[self.gui_key(FRAME_PANE_YEAR_MONTH, WTyp.FR)].update(visible=has_data)
        self._window[self.gui_key(FRAME_PANE_TRANSACTIONS, WTyp.FR)].update(visible=has_data)
        self._window[self.gui_key(FRAME_PANE_TRANSACTION, WTyp.FR)].update(visible=has_data)

    def _event_handler(self, event, values):
        """ 3.2 Handle event """
        self._result = Result()

        # Handle event
        event_key = get_name_from_key(event)

        # - Search window needs main-window to update the dashboard
        if event_key == CMD_SEARCH:
            self._disable_booking(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION, WTyp.CO, True)

        # - Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result

        # - Set log
        if event_key in (
                CMD_IMPORT_TE,
                CMD_CONSISTENCY,
                CMD_RESTORE
        ) and self._controller.db_started:
            self._set_log_pane()

    def _appearance_after(self, event_key):
        # Remarks being edited: Only check if emptied. No visibility actions.
        if event_key == get_name_from_text(CF_REMARKS):
            self._controller.check_emptied_remarks()
            return

        elif event_key == CMD_SEARCH:
            self._disable_booking(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION, WTyp.CO, False)
        elif event_key == CMD_EXPORT:
            return  # No visibility actions (otherwise crash after plot).

        # Transaction pane: Refresh transactions in window
        self.refresh_transactions_from_model()

    def _set_dashboard(self):
        # Iban
        self._window[self._view.gui_key(CF_IBAN, WTyp.CO)].update(value=self._CM.get_config_item(CF_IBAN))
        # Set view rows
        self._window[Table.Year].update(values=self._model.models[Pane.YS].rows)
        self._window[Table.Month].update(values=self._model.models[Pane.MS].rows)
        self._window[Table.TransactionEnriched].update(values=self._model.models[Pane.TE].rows)
        # Set view focus
        set_focus_on_row(self._window[Table.Year], self._CM.get_config_item(f'CF_ROW_NO_{Pane.YS}', 0))
        set_focus_on_row(self._window[Table.Month], self._CM.get_config_item(f'CF_ROW_NO_{Pane.MS}', 0))
        set_focus_on_row(self._window[Table.TransactionEnriched], self._CM.get_config_item(f'CF_ROW_NO_{Pane.TE}', 0))
        self.refresh_transaction_pane()

    def _disable_booking(self, key, type, disable=True):
        self._window[self.gui_key(key, type)].update(disabled=disable)

    def refresh_transaction_pane(self):
        model = self._model.models[Pane.TX]
        self._window[self.gui_key(ACCOUNT_NUMBER, WTyp.IN)].update(value=model.account_number)
        self._window[self.gui_key(DATE, WTyp.IN)].update(value=model.date)
        # BookingCodes
        # - values
        self._window[self.gui_key(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION, WTyp.CO)].update(
            values=model.booking_descriptions)
        # - value: after setting the values!
        self._window[self.gui_key(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION, WTyp.CO)].update(
            value=model.booking_description)
        self._window[self.gui_key(COUNTER_ACCOUNT, WTyp.IN)].update(value=model.counter_account)
        self._window[self.gui_key(NAME, WTyp.IN)].update(value=model.name)
        self._window[self.gui_key(MUTATION_TYPE, WTyp.IN)].update(value=model.mutation_type)
        self._window[self.gui_key(TRANSACTION_CODE, WTyp.IN)].update(value=model.transaction_code)
        self._window[self.gui_key(AMOUNT, WTyp.IN)].update(value=model.amount)
        # "Bijzonderheden"
        self._window[self.gui_key(REMARKS, WTyp.LA)].update(text_color=TEXT_COLOR)
        self._window[self.gui_key(CF_REMARKS, WTyp.ML)].update(value=model.remarks)
        self._window[self.gui_key(COMMENTS, WTyp.ML)].update(value=model.comments)
        # Visibility
        if model.transaction_date:
            self._toggle_visible(FRAME_TX_DATETIME, WTyp.FR, visible=True)
            self._window[self.gui_key(TRANSACTION_DATE, WTyp.IN)].update(value=model.transaction_date)
            self._window[self.gui_key(TRANSACTION_TIME, WTyp.IN)].update(value=model.transaction_time)
        else:
            self._toggle_visible(FRAME_TX_DATETIME, WTyp.FR, visible=False)
        self._toggle_visible(
            FRAME_TRANSACTION_BOOKING, WTyp.FR,
            visible=model.booking_description != EMPTY or self._CM.is_search_for_empty_booking_mode)
        self._window[self.gui_key(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION, WTyp.CO)].update(
            disabled=model.counter_account == EMPTY and not self._CM.is_search_for_empty_booking_mode)

    def _set_log_pane(self):
        self._model.refresh_log()
        rows = self._model.models[Table.Log].rows
        self._window[TAB_LOG].update(visible=len(rows) > 0)
        if len(rows) > 0:
            self._window[Table.Log].update(values=rows)

    def _toggle_visible(self, key, widget_type, visible):
        self._window[self.gui_key(key, widget_type)].update(visible=visible)

    def refresh_transactions_from_model(self):
        """
        Set appearance of Transactions and Transaction panes
        - after booking update in a search-for-transactions-without-booking mode
        - after remarks db change
        - after search
        """
        rows = self._model.models[Pane.TE].rows
        if not rows:
            return

        row_no = self._CM.get_config_item(f'CF_ROW_NO_{Pane.TE}', 0)
        # Transactions window - Rows
        self._window[Table.TransactionEnriched].update(values=rows)
        # Transactions window - Focus
        self._CM.set_config_item(f'CF_ROW_NO_{Pane.TE}', row_no)
        set_focus_on_row(self._window[Table.TransactionEnriched], row_no)
        # Transaction pane - Model
        self.model.set_transaction_pane(current_row_no=row_no)
        # Transaction pane - Refresh
        self.refresh_transaction_pane()
