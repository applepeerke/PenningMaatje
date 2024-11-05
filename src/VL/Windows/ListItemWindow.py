#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.VL.Data.Constants.Enums import WindowType
from src.VL.Windows.BaseWindow import BaseWindow


class ListItemWindow(BaseWindow):

    def __init__(self, name, title, command):
        super().__init__(name, title, WindowType.ListItem)
        self._command = command

    def _event_handler(self, event, values):
        pass

    def _set_close_window(self):
        """
        Close detail window when:
         - Close asked for (e.g. after edit), or
         - Button clicked, or
         - Retry (E.g. Show new theme in Layout options).
         N.B. Prevent closing when input has been changed.
        """
        if self._result.CL or self._result.GO or self._result.CN or self._result.RT:
            self._close_window = True

