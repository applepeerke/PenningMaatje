#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

from src.DL.Config import CMD_HELP_WITH_SEARCH, \
    CMD_SEARCH_RESET, CMD_SEARCH
from src.VL.Controllers.BaseController import BaseController
from src.VL.Functions import help_message
from src.GL.BusinessLayer.ConfigManager import ConfigManager

CM = ConfigManager()

PGM = 'SearchController'


class SearchController(BaseController):

    def __init__(self, model, transactionIO):
        super().__init__()
        self._model = model
        self._transactions_IO = transactionIO

    def handle_event(self, event):
        super().handle_event(event)
        if not self._result.OK:
            return

        # Button clicks
        if self._event_key == CMD_HELP_WITH_SEARCH:
            help_message(CMD_HELP_WITH_SEARCH)
        elif self._event_key == CMD_SEARCH:
            self._result = self._transactions_IO.search()

        elif self._event_key == CMD_SEARCH_RESET:
            CM.initialize_search_criteria()

    def get_combo_data(self, name) -> list:
        return self._model.DD.get_combo_items(name)
