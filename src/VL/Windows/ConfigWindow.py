#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Config import CF_TOOL_TIP, CF_INPUT_DIR, CF_OUTPUT_DIR
from src.VL.Controllers.ConfigController import ConfigController
from src.VL.Data.Constants.Enums import WindowType
from src.VL.Data.WTyp import WTyp
from src.VL.Models.ConfigModel import ConfigModel
from src.VL.Views.ConfigView import ConfigView
from src.VL.Windows.BaseWindow import BaseWindow


class ConfigWindow(BaseWindow):

    @property
    def model(self):
        return self._model

    def __init__(self):
        """ TransActionIO is a plugin """
        super().__init__('ConfigWindow', 'ConfiguratieScherm', WindowType.Detail_with_statusbar)
        self._do_import = False
        # MVC
        self._model = ConfigModel()
        self._view = ConfigView(self._model)
        self._controller = ConfigController(self._model)

    def _get_window(self, **kwargs):
        return super()._get_window(keep_on_top=not self._CM.get_config_item(CF_TOOL_TIP, True), **kwargs)

    def _event_handler(self, event, values):

        # Handle event
        self._controller.handle_event(event)
        self._result = self._controller.result
        if not self._result.OK:
            return

        # Set GUI
        self._window[self._view.gui_key(CF_OUTPUT_DIR, WTyp.IN)].update(value=self._CM.get_config_item(CF_OUTPUT_DIR))
        self._window[self._view.gui_key(CF_INPUT_DIR, WTyp.IN)].update(value=self._CM.get_config_item(CF_INPUT_DIR))
