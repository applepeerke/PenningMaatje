import PySimpleGUI as sg

from src.DL.Config import CF_POPUP_INPUT_VALUE
from src.DL.Table import Table
from src.VL.Data.Constants.Color import TABLE_COLOR_SELECTED_ROW, TABLE_COLOR_BACKGROUND, TABLE_COLOR_TEXT
from src.VL.Data.Constants.Const import TABLE_JUSTIFY
from src.VL.Models.Panes.TransactionsEnriched import TransactionsEnriched
from src.VL.Views.PopUps.PopUp import PopUp, BLOCK_TITLE, BLOCK_BUTTONS, BLOCK_OPTION_TEXT
from src.GL.BusinessLayer.ConfigManager import CF_RADIO_ONLY_THIS_ONE, CF_RADIO_ALL


class DialogWithTransactions(PopUp):

    def __init__(self, where, has_radio=False, input_label=None):
        super().__init__()
        self._has_radio = has_radio
        self._input_label = input_label
        self._model = TransactionsEnriched()
        rows = self._model.DD.fetch_set(Table.TransactionEnriched, where=where)
        self._model.set_data(rows)

    def _get_popup_layout(
            self, block_name=None, hide_option=False, buttons=True) -> list:
        block_input = [
                self.frame('Dialog_input', [
                    self.inbox(CF_POPUP_INPUT_VALUE, label_name=self._input_label, x2=85, evt=True),
                ], border_width=1, expand_y=True, expand_x=True),
            ]
        block_radio = [
                self.frame('Dialog_radio_buttons', [
                    self.radio(key=CF_RADIO_ALL, group_id=1),
                    self.radio(key=CF_RADIO_ONLY_THIS_ONE, group_id=1),
                ], border_width=1, expand_y=True, expand_x=True),
            ]
        block_transactions = [
                self.frame('Dialog_with_transactions', [
                    [sg.Table(k=self.key_of(Table.TransactionEnriched), values=self._model.rows,
                              headings=self._model.header,
                              visible_column_map=self._model.visible_column_map,
                              col_widths=self._model.col_widths,
                              auto_size_columns=False,
                              justification=TABLE_JUSTIFY,
                              num_rows=min(max(self._model.table_height, 1), self._model.num_rows),
                              selected_row_colors=TABLE_COLOR_SELECTED_ROW,
                              enable_click_events=True,
                              background_color=TABLE_COLOR_BACKGROUND,
                              text_color=TABLE_COLOR_TEXT,
                              font=self.get_font('TABLE'),
                              expand_y=True,
                              expand_x=True)]
                ], border_width=1, expand_y=True, expand_x=True),
            ]
        layout = []
        # Title
        layout.extend(super()._get_popup_layout(BLOCK_TITLE))
        # Input
        if self._input_label:
            layout.extend(block_input)
        # Radio buttons
        if self._has_radio:
            layout.extend(block_radio)
        # Buttons OK/CANCEL
        layout.extend(super()._get_popup_layout(BLOCK_BUTTONS))
        # Option to hide next time
        if hide_option:
            layout.extend(super()._get_popup_layout(BLOCK_OPTION_TEXT))
        # Transacties
        layout.extend(block_transactions)
        return layout
