#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import PySimpleGUI as sg

from src.DL.Config import CF_ROWS_YEAR, \
    CF_ROWS_MONTH, CF_ROWS_TRANSACTION, CF_TOOL_TIP, CF_ROWS_BOOKING, CF_ROWS_SEARCH_TERM, CF_THEME, CF_FONT, \
    CF_FONT_SIZE, CF_COL_OVERBOOKING, CF_COL_SALDO_MINUS_CORRECTION, CF_ROWS_COMBO_MAX
from src.VL.Data.Constants.Color import DEFAULT_THEME
from src.VL.Data.Constants.Enums import WindowType, Pane
from src.VL.Functions import get_name_from_key
from src.VL.Models.LayoutOptionsModel import LayoutOptionsModel
from src.VL.Views.LayoutOptionsView import LayoutOptionsView
from src.VL.Windows.BaseWindow import BaseWindow
from src.VL.Windows.General.Boxes import info_box
from src.GL.Const import EMPTY
from src.GL.Enums import ActionCode
from src.GL.Result import Result

RQD = 'RQD'
OPT = 'OPT'


class LayoutOptionsWindow(BaseWindow):

    def __init__(self):
        super().__init__('LayoutWindow', Pane.LO, WindowType.Detail)
        # MVC
        self._model = LayoutOptionsModel()
        self._view = LayoutOptionsView()

        # Set config before image.
        # - Restart Required
        # - Restart Optional
        self._restart_dict = {RQD: {}, OPT: {}}
        self._set_value_before(CF_ROWS_YEAR, OPT)
        self._set_value_before(CF_ROWS_MONTH, OPT)
        self._set_value_before(CF_ROWS_TRANSACTION, OPT)
        self._set_value_before(CF_ROWS_BOOKING, OPT)
        self._set_value_before(CF_ROWS_SEARCH_TERM, OPT)
        self._set_value_before(CF_ROWS_COMBO_MAX, OPT)
        self._set_value_before(CF_COL_OVERBOOKING, RQD)
        self._set_value_before(CF_COL_SALDO_MINUS_CORRECTION, RQD)
        self._set_value_before(CF_TOOL_TIP, OPT)

    def _set_value_before(self, cf_code, return_value):
        self._restart_dict[return_value][cf_code] = self._CM.get_config_item(cf_code, EMPTY)

    def _get_window(self, **kwargs):
        return super()._get_window(keep_on_top=not self._CM.get_config_item(CF_TOOL_TIP, True), **kwargs)

    def _event_handler(self, event, values):
        self._result = Result()
        event_key = get_name_from_key(event)
        if event_key not in (CF_THEME, CF_FONT, CF_FONT_SIZE):
            return

        value = values.get(event)
        # Color theme selected: set new color theme, optionally reset to default
        if event_key == CF_THEME:
            value = value or DEFAULT_THEME
            sg.theme(value)

        # Set value in config
        self._CM.set_config_item(event_key, value)

        self._result = Result(action_code=ActionCode.Retry)
        self._close_window = True

    def restart_app(self) -> bool:
        """
        Restart if:
            o Columns to display are changed or
            o User changed number of pane rows.
        Inform to restart if:
            o Tooltip changed.
        return: TRUE if required, or else FALSE if optional item changed. Else None.
        """
        if self._has_a_value_changed(RQD):
            return True
        elif self._has_a_value_changed(OPT):
            info_box('Om de wijzigingen te zien moet de app opnieuw gestart worden.')
            return False
        else:
            return False

    def _has_a_value_changed(self, rqd_opt) -> bool:
        return True if any(
            value != self._CM.get_config_item(key) for key, value in self._restart_dict[rqd_opt].items()
        ) else False
