#!/usr/bin/env python3

import PySimpleGUI as sg

from src.DL.Objects.Window import Window
from src.VL.BaseGUI import BaseGUI
from src.VL.Data.Constants.Enums import WindowType
from src.VL.Functions import get_name_from_key, status_message
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity, ActionCode, ResultCode
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import isInt
PGM = 'BaseWindow'


class BaseWindow(BaseGUI):

    @property
    def result(self):
        return self._result

    @property
    def title(self):
        return self._title

    @property
    def window_type(self):
        return self._window_type

    @property
    def close_requested(self):
        return self._close_window

    @property
    def location(self):
        return self._location

    @property
    def statusbar_width(self):
        return self._statusbar_width

    def __init__(self, name, title, window_type=None):
        super().__init__()
        self._name = name
        self._title = title
        self._window_type = window_type
        self._window = None
        self._location = (0, 0)
        self._view = None
        self._close_clicked = False
        self._close_window = False
        self._Id = 0
        self._result = Result()
        self._event_value_previous = EMPTY
        self._CM = ConfigManager()
        self._session = Session()
        self._statusbar_width = 0

    def handle_unittest_event(self, event, values):
        """ Only for unittest to create events without display """
        self._event_handler(event, values)

    def display(self):

        # Populate model
        self._preparation()

        # Get sg window, layout populated by model
        self._location = self._CM.get_location(self._name)
        self._window = self._get_window(location=self._location)

        # ____________________
        #  E V E N T   L O O P
        # --------------------

        while True:
            self._result = Result()

            # Set appearance - before event
            self._appearance_before()

            # Unit test: 1-time (for coverage)
            if self._session.unit_test:
                break

            event, values = self._window.read()

            # Window handling
            # - Closed
            if event == sg.WIN_CLOSED:
                # NB: Window location cannot be retrieved here anymore.
                self._CM.set_location(self._name, self._location)
                self._close_clicked = True
                self._result = Result(ResultCode.Canceled)
                break

            # - Location
            self._location = self._window.current_location()

            # Event handling
            event_key = get_name_from_key(event)
            if not event_key:
                raise GeneralException('Actie kon niet herleid worden.')

            # - Set in config
            self._event_value_previous = self._CM.get_config_item(event_key)
            try:
                self._CM.set_config_item(event_key, values.get(event))
            except GeneralException as ge:
                self._result = Result(ResultCode.Error, ge.message)

            # - Handle event
            if self._result.OK:
                self._event_handler(event, values)
                # Continue in Main after pressing Cancel in a sub display
                if self._result.CN and self._window_type == WindowType.Main:
                    self._result = Result()

            # Event aftercare
            # - Retry: Restart app
            if self._result.RT or self._result.EX:
                break

            # - Error: Restore value in config
            if not self._result.OK and self._event_value_previous:
                self._CM.set_config_item(event_key, self._event_value_previous)

            # - Close requested from within event
            if self._close_window or self._result.CN:
                self._CM.set_location(self._name, self._location)
                break

            # Set appearance - after event
            self._appearance_after(event_key)

            # Output
            self._message()

        self._window.close()

    def _is_row_clicked(self, event) -> bool:
        if isinstance(event, tuple) and len(event) == 3:
            # Clicked on 1st row in empty list (None, 0) or on header (-1, 0)
            if not isInt(event[2][0]) or event[2][0] == -1:
                return False
            self._Id = int(event[2][0]) + 1
            return True
        return False

    def _preparation(self):
        pass

    def _get_window(self, **kwargs):
        window = Window(self._title, layout=self._view.get_view(), **kwargs).instance()
        self._statusbar_width = max(self._view.statusbar_width, 45)
        return window

    def _event_handler(self, event, values):
        raise NotImplementedError(f'{PGM}: Method "_event_handler" has not been implemented in window "{self._window}"')

    def _appearance_before(self):
        pass

    def _appearance_after(self, event_key):
        pass

    def _message(self, min_severity=MessageSeverity.Warning) -> bool:
        """ Status or box message. """
        # Detail window has no status bar, always box message.
        if self._window_type not in WindowType.has_statusbar:
            return self._result.get_box_message(min_severity)

        confirmed = True

        if self._result.action_code == ActionCode.Cancel:
            status_message(self._window, self._result.text)
        elif not self._result.text and not self._result.messages:
            status_message(self._window)
        elif (not self._result.text
              and len(self._result.messages) == 1
              and len(self._result.messages[0].message) <= self._statusbar_width):
            status_message(self._window, self._result.messages[0].message, self._result.severity)
        # Box message
        # or (len(self._result.messages) == 1 and self._result.messages[0].severity > 10) \
        elif self._result.text.endswith('?') \
                or len(self._result.messages) > 1 \
                or (self._result.severity >= min_severity and not self._result.severity == MessageSeverity.Completion):
            status_message(self._window)
            confirmed = self._result.get_box_message(min_severity)
        # Status message
        else:
            if self._result.text:
                status_message(self._window, self._result.text, self._result.severity)
            elif len(self._result.messages) > 0:
                status_message(self._window, self._result.messages[0].message, self._result.severity)
            else:
                status_message(self._window, EMPTY, self._result.severity)
        return confirmed
