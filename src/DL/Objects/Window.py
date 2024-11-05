#!/usr/bin/env python3
import PySimpleGUI as sg

from src.BL.Functions import get_icon
from src.DL.Config import ALPHA_CHANNEL, EXPAND
from src.GL.BusinessLayer.ConfigManager import ConfigManager


class Window:

    def __init__(self, title, layout, location=(0, 0), modal=False, relative_location=(0, 0), keep_on_top=True):
        CM = ConfigManager()
        self._window = sg.Window(
            title,
            layout,
            font=CM.get_font(),
            alpha_channel=ALPHA_CHANNEL,
            text_justification='left',
            resizable=True,
            finalize=True,
            icon=get_icon(),
            modal=modal,
            keep_on_top=keep_on_top,
            location=location,
            relative_location=relative_location
        )
        if EXPAND in self._window.key_dict:
            self._window[EXPAND].expand(True, True, True)

    def instance(self):
        return self._window
