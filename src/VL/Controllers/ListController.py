#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from typing import Callable

from src.VL.Controllers.BaseController import BaseController
from src.VL.Data.Constants.Const import CMD_NEW, CMD_UPDATE, CMD_DELETE, CMD_RENAME
from src.VL.Data.Constants.Enums import BoxCommand
from src.GL.Enums import ResultCode, ActionCode
from src.GL.Result import Result

PGM = 'ListController'


class ListController(BaseController):

    def __init__(self, item_window: Callable):
        super().__init__()
        self._item_window = item_window

    def handle_event(self, event, Id=0):
        # Handle CANCEL and OK
        super().handle_event(event)
        if not self._result.OK:
            return

        # CRUD action
        if self._event_key == CMD_NEW:
            command = BoxCommand.Add
        elif self._event_key == CMD_UPDATE:
            command = BoxCommand.Update
        elif self._event_key == CMD_DELETE:
            command = BoxCommand.Delete
        elif self._event_key == CMD_RENAME:
            command = BoxCommand.Rename
        else:
            raise NotImplementedError(f'{PGM}: Event {self._event_key} is not implemented.')

        # No line selected yet
        if Id == 0 and command != BoxCommand.Add:
            self._result = Result(ResultCode.Warning, 'Selecteer eerst een regel voor deze actie.')
            return

        # Edit
        self._edit_item(command, Id)

    def _edit_item(self, command, Id):
        """ Button clicked, and a list item has been selected """
        if not self._can_be_selected(command, Id):
            return
        # Detail window
        Item_window = self._item_window(command, Id)
        Item_window.display()
        self._result = Item_window.result
        if self._result.CL:
            self._result = Result(action_code=ActionCode.Go)  # Reset Close

        # Redisplay the list if an item has been added or deleted.
        if self._result.OK and command in (BoxCommand.Add, BoxCommand.Delete):
            self._result = Result(action_code=ActionCode.Retry)

    @staticmethod
    def _can_be_selected(command, Id) -> bool:
        return True
