import PySimpleGUI as sg

from src.DL.Config import (
    CF_SEARCH_YEAR, CF_SEARCH_MONTH, CF_SEARCH_COUNTER_ACCOUNT, CF_SEARCH_AMOUNT, CF_SEARCH_AMOUNT_TO,
    CF_SEARCH_TRANSACTION_CODE, CF_SEARCH_TEXT, CF_SEARCH_AMOUNT_TOTAL, FRAME_SEARCH_DISPLAY, CMD_SEARCH,
    CMD_SEARCH_RESET, FRAME_SEARCH_TOTAL, EXPAND, FRAME_SEARCH_REFRESH_BUTTON, STATUS_MESSAGE, CMD_HELP_WITH_SEARCH,
    CF_SEARCH_REMARKS, CF_SEARCH_BOOKING_CODE, CF_IMAGE_SUBSAMPLE)
from src.VL.Data.Constants.Color import TOTAL_COLOR
from src.VL.Data.Constants.Const import FRAME_SEARCH_BOOKING_CODE
from src.VL.Views.BaseView import BaseView, CM
from src.GL.Const import EMPTY

amount_width = 12


class SearchView(BaseView):

    def __init__(self, model):
        super().__init__()
        self._model = model

    def get_view(self) -> list:
        x_TX = max(len(self._get_label(CF_SEARCH_YEAR)),
                   len(self._get_label(CF_SEARCH_MONTH)),
                   len(self._get_label(CF_SEARCH_COUNTER_ACCOUNT)),
                   len(self._get_label(CF_SEARCH_TRANSACTION_CODE)),
                   len(self._get_label(CF_SEARCH_AMOUNT)),
                   len(self._get_label(CF_SEARCH_AMOUNT_TO)),
                   len(self._get_label(CF_SEARCH_BOOKING_CODE)),
                   len(self._get_label(CF_SEARCH_TEXT)),
                   len(self._get_label(CF_SEARCH_REMARKS))
                   )
        self._statusbar_width = x_TX
        # Layout
        view_layout = [
            # Zoeken
            self.frame(FRAME_SEARCH_DISPLAY, [
                self.combo(CF_SEARCH_YEAR, self._model.years, dft=EMPTY, x=x_TX),
                self.combo(CF_SEARCH_MONTH, self._model.months, dft=EMPTY, x=x_TX),
                self.combo(CF_SEARCH_COUNTER_ACCOUNT, self._model.counter_account_numbers, x=x_TX),
                self.combo(CF_SEARCH_TRANSACTION_CODE, self._model.transaction_codes, x=x_TX),
                self.frame(FRAME_SEARCH_BOOKING_CODE, [
                    self.combo(CF_SEARCH_BOOKING_CODE, sorted(self._model.booking_description_searchables), x=x_TX),
                ], border_width=0, p=0),
                self.inbox(CF_SEARCH_TEXT, x=x_TX),
                self.cbx(CF_SEARCH_REMARKS, x=x_TX),
                self.inbox(CF_SEARCH_AMOUNT, x=x_TX),
                self.inbox(CF_SEARCH_AMOUNT_TO, x=x_TX),
                self.frame(FRAME_SEARCH_TOTAL,
                           [self.inbox(CF_SEARCH_AMOUNT_TOTAL, x=x_TX, x2=amount_width, disabled=True,
                                       label_color=TOTAL_COLOR, expand_x=True)
                            ], p=0),
                # Zoek buttons
                self.multi_frame('Search_buttons', [
                    self.frame('Zoek_button', [[self.button(
                        CMD_SEARCH, button_text=EMPTY,
                        image_filename=self._model.image_magnifying_glass, transparent=True, p=0,
                        image_subsample=CM.get_config_item(CF_IMAGE_SUBSAMPLE)
                    )]], border_width=1, p=2, relief=sg.RELIEF_RAISED),
                    self.frame(FRAME_SEARCH_REFRESH_BUTTON, [[self.button(
                        CMD_SEARCH_RESET, button_text=EMPTY,
                        image_filename=self._model.image_refresh, transparent=True, p=0,
                        image_subsample=CM.get_config_item(CF_IMAGE_SUBSAMPLE)
                    )]], border_width=1, p=2, relief=sg.RELIEF_RAISED),
                    self.frame('Help', [[self.button(
                        CMD_HELP_WITH_SEARCH, button_text='?', transparent=True, p=5, font=self.get_font(addition=8)
                    )]], p=0, border_width=1)
                ], p=2, justify='L', expand_x=True),
            ], p=2, expand_x=True),
        ]

        # The window layout - defines the entire window
        view = [
            [view_layout],
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5),
                          size=(self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN)],
            [sg.Text(key=EXPAND, font='ANY 1', pad=(0, 0))]
        ]
        return view
