#!/usr/bin/env python3
from src.Base import Base
from src.VL.Functions import get_name_from_text, gui_name_types, gui_values
from src.GL.Const import EMPTY
from src.GL.GeneralException import GeneralException


class BaseGUI(Base):

    def __init__(self, pane_name=None):
        super().__init__()
        self._pane_name = pane_name

    def gui_key(self, text, prefix, use_window_name=False) -> str:
        name = get_name_from_text(text)
        if not name:
            return EMPTY
        k = f'{self._pane_name}|{name}_{prefix}' if use_window_name and self._pane_name else f'{name}_{prefix}'
        gui_name_types[name] = prefix
        return k

    def set_gui_value_keys(self, k, widget_type):
        """ Keep only information (not labels etc.) from SimpleGuiManager"""
        k = f'{self._pane_name}|{k}' if self._pane_name else k
        if k in gui_values and widget_type != gui_values[k]:
            raise GeneralException(f'{__name__}: Key "{k}" already exists as a gui-value.')
        gui_values[k] = widget_type

    def key_of(self, text, use_window_name=False):
        k = f'{self._pane_name}|{text}' if use_window_name and self._pane_name else text
        if k not in gui_values:
            return k
        return self.gui_key(text, gui_values[k])
