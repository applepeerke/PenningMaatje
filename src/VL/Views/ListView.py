import PySimpleGUI as sg

from src.DL.Config import EXPAND, STATUS_MESSAGE
from src.VL.Data.Constants.Color import TABLE_COLOR_SELECTED_ROW, TABLE_COLOR_BACKGROUND, TABLE_COLOR_TEXT
from src.VL.Data.Constants.Const import CMD_NEW, FRAME_PANE_CRUD, NEW, UPDATE, DELETE, RENAME, \
    CMD_RENAME, CMD_UPDATE, CMD_DELETE, TABLE_JUSTIFY
from src.VL.Views.BaseView import BaseView
from src.GL.Const import EMPTY


class ListView(BaseView):
    """ Used for Booking and SearchTerms"""

    @property
    def model(self):
        return self._model

    def __init__(self, pane_name, model):
        super().__init__(pane_name)
        self._model = model

    def get_view(self) -> list:
        self._statusbar_width = 30
        view_layout = [
            self.multi_frame(FRAME_PANE_CRUD, [
                self.frame('CRUD_tabel', [
                            # Buttons
                            self.multi_frame('CRUD_buttons', [
                                self.frame('CRUD_new',
                                           [[self.button(CMD_NEW, p=0, button_text=NEW)]],
                                           border_width=1, p=0, relief=sg.RELIEF_RAISED),
                                self.frame('CRUD_update',
                                           [[self.button(CMD_UPDATE, p=0, button_text=UPDATE)]],
                                           border_width=1, p=0, relief=sg.RELIEF_RAISED),
                                self.frame('CRUD_delete',
                                           [[self.button(CMD_DELETE, p=0, button_text=DELETE)]],
                                           border_width=1, p=0, relief=sg.RELIEF_RAISED),
                                self.frame('CRUD_rename',
                                           [[self.button(CMD_RENAME, p=0, button_text=RENAME)]],
                                           border_width=1, p=0, relief=sg.RELIEF_RAISED),
                            ], p=0),
                            [sg.Table(k=self.key_of(self._model.table_name), values=self._model.rows,
                                      headings=self._model.header,
                                      visible_column_map=self._model.visible_column_map,
                                      col_widths=self._model.col_widths,
                                      auto_size_columns=False,
                                      justification=TABLE_JUSTIFY,
                                      num_rows=min(max(self._model.table_height, 1), self._model.num_rows),
                                      selected_row_colors=TABLE_COLOR_SELECTED_ROW, enable_click_events=True,
                                      background_color=TABLE_COLOR_BACKGROUND, text_color=TABLE_COLOR_TEXT,
                                      font=self.get_font('TABLE'))]],
                           border_width=1),
            ], border_width=1),
        ]

        # The window layout - defines the entire window
        view = [
            [view_layout],
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5), size=(self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN)],
            [sg.Text(key=EXPAND, font='ANY 1', pad=(0, 0))]
        ]
        return view
