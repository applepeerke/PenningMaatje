import PySimpleGUI as sg

from src.DL.Config import EXPAND, \
    STATUS_MESSAGE, CF_OUTPUT_DIR, CF_INPUT_DIR, \
    CF_AUTO_CLOSE_TIME_S, CF_BACKUP_RETENTION_MONTHS, FRAME_CONFIG_MAIN, CMD_HELP_WITH_OUTPUT_DIR, \
    CMD_HELP_WITH_INPUT_DIR, FRAME_VARIOUS, FRAME_CONFIG_BUTTONS, CMD_FACTORY_RESET, CMD_LAYOUT_OPTIONS, \
    CF_AMOUNT_THRESHOLD_TO_OTHER
from src.DL.Table import Table
from src.VL.Data.Constants.Color import TABLE_COLOR_SELECTED_ROW, TABLE_COLOR_BACKGROUND, TABLE_COLOR_TEXT
from src.VL.Data.Constants.Const import FRAME_CONFIG_ACCOUNT, TABLE_JUSTIFY
from src.VL.Views.BaseView import BaseView, CM
from src.GL.Const import EMPTY


class ConfigView(BaseView):

    def __init__(self, model):
        super().__init__()
        self._model = model

    def get_view(self) -> list:
        VM_AC = self._model.account_model

        x_DI = max(len(self._get_label(CF_OUTPUT_DIR)),
                   len(self._get_label(CF_INPUT_DIR)), )
        x_CX = max(len(self._get_label(CF_AUTO_CLOSE_TIME_S)),
                   len(self._get_label(CF_BACKUP_RETENTION_MONTHS)),
                   len(self._get_label(CF_AMOUNT_THRESHOLD_TO_OTHER)),
                   )

        self._statusbar_width = max(x_DI, x_CX)
        x_dir = max(len(CM.get_config_item(CF_OUTPUT_DIR)), len(CM.get_config_item(CF_INPUT_DIR)))

        # Layout
        view_layout = [
            # - "Basis folder [inputBox met pad] [Browse] [?]"
            self.frame(FRAME_CONFIG_MAIN, [
                self.multi_frame(CF_OUTPUT_DIR, [
                    self.inbox(CF_OUTPUT_DIR, x=x_DI, x2=x_dir, folder_browse=True),
                    self.frame(
                        'Help bij output folder',
                        [[self.button(CMD_HELP_WITH_OUTPUT_DIR, button_text='?', transparent=True, p=0)]],
                        border_width=1)
                ], p=0),
                # - "Folder met bankafschriften  [Combo met paden] [?]"
                self.multi_frame(CF_INPUT_DIR, [
                    self.inbox(CF_INPUT_DIR, x=x_DI, x2=x_dir, folder_browse=True),
                    self.frame(
                        'Help bij input folder',
                        [[self.button(CMD_HELP_WITH_INPUT_DIR, button_text='?', transparent=True, p=0)]],
                        border_width=1)
                ], p=0),
            ], border_width=1, expand_x=True),
            # Accounts
            self.frame(FRAME_CONFIG_ACCOUNT, [
                [sg.Table(k=self.key_of(Table.Account),
                          values=VM_AC.rows,
                          headings=VM_AC.header,
                          visible_column_map=VM_AC.visible_column_map,
                          col_widths=VM_AC.col_widths,
                          auto_size_columns=False,
                          justification=TABLE_JUSTIFY,
                          num_rows=min(max(VM_AC.table_height, 1), VM_AC.num_rows),
                          selected_row_colors=TABLE_COLOR_SELECTED_ROW,
                          enable_click_events=True,
                          background_color=TABLE_COLOR_BACKGROUND,
                          text_color=TABLE_COLOR_TEXT,
                          font=self.get_font('TABLE'),
                          expand_x=True, expand_y=True),
                 ],
            ], border_width=1, expand_x=True, expand_y=True),

            # Various
            self.frame(FRAME_VARIOUS, [
                self.frame(CF_AMOUNT_THRESHOLD_TO_OTHER,
                           [self.combo(CF_AMOUNT_THRESHOLD_TO_OTHER, [x for x in range(0, 50, 5)], x=x_CX)], p=5),
                self.frame(CF_AUTO_CLOSE_TIME_S,
                           [self.combo(CF_AUTO_CLOSE_TIME_S, [x for x in range(0, 10, 1)], x=x_CX)], p=5),
                self.frame(CF_BACKUP_RETENTION_MONTHS,
                           [self.combo(CF_BACKUP_RETENTION_MONTHS, [x for x in range(1, 12, 1)], x=x_CX)], p=5),
            ], border_width=1, expand_x=True),
            self.multi_frame(FRAME_CONFIG_BUTTONS, [
                self.button_frame(CMD_FACTORY_RESET),
                self.button_frame(CMD_LAYOUT_OPTIONS),
            ]),
        ]

        # The window layout - defines the entire window
        view = [
            [view_layout],
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5), size=(self._statusbar_width, 1), expand_x=True,
                          relief=sg.RELIEF_SUNKEN)],
            [sg.Text(key=EXPAND, font='ANY 1', pad=(0, 0))]
        ]
        return view
