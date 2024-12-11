#!/usr/bin/env python3
import PySimpleGUI as sg

from src.Base import Base
from src.DL.Config import ALPHA_CHANNEL, EXPAND


class Window(Base):

    def __init__(self, title, layout, location=(0, 0), modal=False, relative_location=(0, 0), keep_on_top=True):
        super().__init__()
        self._window = sg.Window(
            title,
            layout,
            font=self._CM.get_font(),
            alpha_channel=ALPHA_CHANNEL,
            text_justification='left',
            resizable=True,
            finalize=True,
            icon=self._session.get_icon(),
            modal=modal,
            keep_on_top=keep_on_top,
            location=location,
            relative_location=relative_location
        )
        if EXPAND in self._window.key_dict:
            self._window[EXPAND].expand(True, True, True)

    def instance(self):
        return self._window
