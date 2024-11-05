import PySimpleGUI as sg

from src.DL.Table import Table
from src.VL.Data.Constants.Color import TABLE_COLOR_SELECTED_ROW, TABLE_COLOR_BACKGROUND, TABLE_COLOR_TEXT
from src.VL.Data.Constants.Const import TABLE_JUSTIFY
from src.VL.Models.Panes.TransactionsEnriched import TransactionsEnriched
from src.VL.Views.PopUps.PopUp import PopUp, BLOCK_TITLE


class PopUpWithTransactions(PopUp):

    def __init__(self, where):
        super().__init__()
        self._model = TransactionsEnriched()
        rows = self._model.DD.fetch_set(Table.TransactionEnriched, where=where)
        self._model.set_data(rows)

    def _get_popup_layout(self, block_name=None, hide_option=False, buttons=True) -> list:
        block_transactions = [
                self.frame('Popup_with_transactions', [
                    [sg.Table(k=self.key_of(Table.TransactionEnriched),
                              values=self._model.rows,
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
        # Transacties
        layout.extend(block_transactions)
        return layout
