#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from typing import Callable

from src.Base import Base
from src.DL.DBDriver.AttType import AttType
from src.VL.Data.Constants.Const import CMD_CANCEL, CMD_OK
from src.VL.Data.DataDriver import Singleton as DataDriver
from src.VL.Functions import get_name_from_key
from src.VL.Views.PopUps.PopUp import PopUp
from src.GL.Const import EMPTY
from src.GL.Enums import ActionCode, MessageSeverity
from src.GL.Functions import maybeFloat
from src.GL.Result import Result, log
from src.GL.Validate import isInt, isDate, isAlphaNumeric, isDateOrNone

DD = DataDriver()


class BaseController(Base):

    @property
    def result(self):
        return self._result

    """
    Setters
    """
    @result.setter
    def result(self, value):
        self._result = value

    def __init__(self, diagnostic_mode=False):
        super().__init__()
        self._diagnostic_mode = diagnostic_mode
        self._result = Result()
        self._dialog = PopUp()
        self._event_key = None
        self._log_started = False

    def handle_event(self, event):
        self._result = Result()
        self._event_key = get_name_from_key(event)
        # - CANCEL
        if self._event_key == CMD_CANCEL:
            self._result = Result(action_code=ActionCode.Cancel)
        # - OK
        elif self._event_key == CMD_OK:
            self._result = Result(action_code=ActionCode.Go)

    def _maintain_list(self, window: Callable):
        """
        While list size changes (add or delete item), restart the list.
        Otherwise, when list is empty it will appear too small.
        """
        while True:
            W = window()
            W.display()
            if not W.result.RT:
                self._result = W.result
                break
    """
    Validations
    """
    # - Required (multiple errors)
    def _isSpecifiedInAtt(self, att) -> bool:
        if not att.value:
            self._add_validation_error(
                att.name, att.value, f'Een waarde voor "{att.name}" is verplicht.', multiple_errors=True)
            return False
        return True

    # - Required
    def _isSpecified(self, name, value, att_type: AttType = None):
        if (not value
                or (isinstance(value, int) and value == 0)
                or (isinstance(value, str) and value == '0' and att_type == AttType.Int)
                or (isinstance(value, float) and value == 0)):
            self._add_validation_error(name, value, f'Een waarde voor "{name}" is verplicht.')

    def _isInValues(self, name, value, values):
        if value not in values:
            self._add_validation_error(name, value, f'Waarde "{value}" voor "{name}" is ongeldig.')

    # - AlphaNumeric`
    def _isAlphaNumeric(self, name, value, text=None):
        if not isAlphaNumeric(value):
            self._add_validation_error(name, value, text)

    # - Int
    def _isInt(self, name, value, text=None, from_value=None, to_value=None):
        """ Test if value = int with optional range (for e.g. year) """
        if (not isInt(str(value))
                or from_value is not None and int(value) < from_value
                or to_value is not None and int(value) > to_value):
            self._add_validation_error(name, value, text)

    # - Float (amount)
    def _isFloat(self, name, value, text=None):
        if not maybeFloat(value):
            self._add_validation_error(name, value, text)

    # - Date
    def _isDate(self, name, value, text=None, required=True):
        if (required and not isDate(value)) or (not required and not isDateOrNone(value)):
            self._add_validation_error(name, value, text)

    def _is_valid_empty(self, name, value, required=False) -> bool:
        if not value and required:
            self._add_error(f'Een waarde voor {name} is verplicht.')
            return False
        return True
    """
    Messages
    """
    def _diag_message(self, text):
        if not self._diagnostic_mode:
            return
        diag_text = f'-- {text} --'
        if not log(diag_text, log_started=self._log_started):
            print(diag_text)

    def _add_validation_error(self, name, value, text=EMPTY, multiple_errors=False):
        # 1 error per
        if self._result.OK or multiple_errors:
            self._add_error(text or f'{name} "{value}" is ongeldig.')

    def _add_error(self, text):
        self._result.add_message(text, severity=MessageSeverity.Error)
