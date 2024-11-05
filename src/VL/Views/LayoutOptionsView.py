import PySimpleGUI as sg

from src.DL.Config import EXPAND, \
    STATUS_MESSAGE, CF_TOOL_TIP, \
    CF_VERBOSE, CF_ROWS_YEAR, CF_ROWS_MONTH, CF_ROWS_TRANSACTION, CF_AUTO_CLOSE_TIME_S, CF_BACKUP_RETENTION_MONTHS, \
    FRAME_LAYOUT, CF_SHOW_ALL_POPUPS, CF_ROWS_BOOKING, CF_ROWS_SEARCH_TERM, CF_THEME, CF_FONT, CF_FONT_SIZE, \
    CF_FONT_TABLE, CF_FONT_TABLE_SIZE, FRAME_LAYOUT_OPTIONAL_COLUMNS, CF_COL_OVERBOOKING, \
    CF_COL_SALDO_MINUS_CORRECTION, CF_ROWS_COMBO_MAX, CF_COL_COSTS, \
    CF_COL_REVENUES
from src.VL.Models.LayoutOptionsModel import LayoutOptionsModel
from src.VL.Views.BaseView import BaseView, CM
from src.GL.Const import EMPTY

themes = [EMPTY]
themes.extend(sg.theme_list())


class LayoutOptionsView(BaseView):

    def __init__(self):
        super().__init__()
        self._model = LayoutOptionsModel()

    def get_view(self) -> list:
        x_CX = max(len(self._get_label(CF_COL_OVERBOOKING)),
                   len(self._get_label(CF_COL_COSTS)),
                   len(self._get_label(CF_COL_REVENUES)),
                   len(self._get_label(CF_COL_SALDO_MINUS_CORRECTION)),
                   len(self._get_label(CF_TOOL_TIP)),
                   len(self._get_label(CF_VERBOSE)),
                   len(self._get_label(CF_SHOW_ALL_POPUPS)),
                   len(self._get_label(CF_ROWS_YEAR)),
                   len(self._get_label(CF_ROWS_MONTH)),
                   len(self._get_label(CF_ROWS_TRANSACTION)),
                   len(self._get_label(CF_ROWS_BOOKING)),
                   len(self._get_label(CF_ROWS_SEARCH_TERM)),
                   len(self._get_label(CF_AUTO_CLOSE_TIME_S)),
                   len(self._get_label(CF_BACKUP_RETENTION_MONTHS)),
                   )
        self._statusbar_width = x_CX
        # Dashboard
        vm_layout = [
            # Zoeken
            self.frame(FRAME_LAYOUT, [
                self.frame(FRAME_LAYOUT_OPTIONAL_COLUMNS, [
                    self.cbx(CF_COL_OVERBOOKING, x=x_CX),
                    self.cbx(CF_COL_COSTS, x=x_CX),
                    self.cbx(CF_COL_REVENUES, x=x_CX),
                    self.cbx(CF_COL_SALDO_MINUS_CORRECTION, x=x_CX),
                ], border_width=1, expand_x=True),
                self.cbx(CF_TOOL_TIP, x=x_CX),
                self.cbx(CF_VERBOSE, x=x_CX),
                self.cbx(CF_SHOW_ALL_POPUPS, x=x_CX),
                self.combo(CF_ROWS_YEAR, [x for x in range(1, 15, 1)], x=x_CX),
                self.combo(CF_ROWS_MONTH, [x for x in range(1, 12, 1)], x=x_CX),
                self.combo(CF_ROWS_TRANSACTION, [x for x in range(5, 50, 1)], x=x_CX),
                self.combo(CF_ROWS_BOOKING, [x for x in range(5, 50, 1)], x=x_CX),
                self.combo(CF_ROWS_SEARCH_TERM, [x for x in range(5, 50, 1)], x=x_CX),
                self.combo(CF_ROWS_COMBO_MAX, [x for x in range(10, 50, 1)], x=x_CX),
                self.combo(CF_THEME, themes, x=x_CX),
                self.combo(CF_FONT, self._model.fonts, x=x_CX),
                self.combo(CF_FONT_SIZE, [x for x in range(9, 21, 1)], x=x_CX),
                self.combo(CF_FONT_TABLE, self._model.fonts, x=x_CX,
                           font=CM.get_config_item(CF_FONT_TABLE)),
                self.combo(CF_FONT_TABLE_SIZE, [x for x in range(9, 21, 1)], x=x_CX,
                           font=CM.get_config_item(CF_FONT_TABLE_SIZE))
            ], border_width=1, expand_x=True),
            ]

        # The window layout - defines the entire window
        layout = [
            [vm_layout],
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5), size=(
                self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN)],
            [sg.Text(key=EXPAND, font='ANY 1', pad=(0, 0))]
        ]
        return layout
