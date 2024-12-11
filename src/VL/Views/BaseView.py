#!/usr/bin/env python3

from typing import Any, Callable

import PySimpleGUI as sg

from src.DL.Config import get_label as get_config_label, CF_THEME
from src.VL.BaseGUI import BaseGUI
from src.VL.Data.Constants.Color import *
from src.VL.Data.Constants.Const import X1, P1, Y1, P
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import gui_name_types, get_name_from_text
from src.GL.Const import EMPTY, NONE, BLANK
from src.GL.Functions import format_date
from src.GL.GeneralException import GeneralException
from src.GL.Validate import toBool, normalize_dir

PGM = 'BaseView'


def width(items) -> int or None:
    if not items:
        return None
    w = 0
    for i in items:
        if len(str(i)) > w:
            w = len(str(i))
    return w if w > 0 else None


def get_button_text(text, button_text):
    if button_text is not None:
        result = button_text
    elif text:
        text = text.replace('_', BLANK)
        result = text.capitalize()
    else:
        return '*ERROR'
    return result


class BaseView(BaseGUI):

    @property
    def window_name(self):
        return self._pane_name

    @property
    def window_location(self):
        return self._location

    @property
    def window_size(self):
        return self._size

    @property
    def statusbar_width(self):
        return self._statusbar_width

    @property
    def relative_location(self):
        return self._relative_location

    """
    Setters
    """

    @relative_location.setter
    def relative_location(self, value):
        self._relative_location = value

    def __init__(self, pane_name=None):
        super().__init__(pane_name)
        self._pane_name = pane_name
        self._set_theme()
        self._window = None
        self._relative_location = 0, 0

        self._location = 0, 0
        self._size = 0, 0
        self._statusbar_width = 0

    def get_view(self) -> list:
        raise NotImplementedError(f'{PGM}: Method "get_view" has not been implemented for pane "{self._pane_name}".')

    def get_tooltip(self, key):
        return self._CM.get_tooltip(key)

    def _set_theme(self):
        theme = self._CM.get_config_item(CF_THEME, DEFAULT_THEME)
        if str(theme) in sg.theme_list():
            sg.theme(theme)
        else:
            self._CM.set_config_item(CF_THEME, DEFAULT_THEME)
            sg.theme(DEFAULT_THEME)

    """
    G e n e r i c
    """

    def label(self, name, x=X1, k=None, tip=None, text_color=None, font=None):
        key_name = k or name
        return sg.Text(self._get_label(name), k=self.gui_key(key_name, WTyp.LA),
                       size=(x, Y1), p=P1, tooltip=tip or self.get_tooltip(name),
                       text_color=text_color, font=font)

    def button(self, text, x=X1, font=None, button_text=None, tip=True, visible=True, image_filename=None,
               image_subsample=1, transparent=False, p=P1):
        self.set_gui_value_keys(text, WTyp.BT)
        return sg.Button(
            button_text=get_button_text(text, button_text), k=self.gui_key(text, WTyp.BT), size=(x, Y1), p=p, font=font,
            disabled_button_color=COLOR_BUTTON_DISABLED, tooltip=self.get_tooltip(text) if tip else None,
            visible=visible, image_filename=image_filename, image_subsample=image_subsample,
            button_color=(COLOR_FOREGROUND, COLOR_BACKGROUND_HIGHLIGHTED_ROW) if transparent else None)

    def multi_frame(self, key, content: list, title=EMPTY, border_width=0, relief=None, visible=True, p=P,
                    justify='right', expand_y=False, expand_x=False) -> list:
        elems = []
        for item in content:
            if not isinstance(item, list):
                item = [item]
            for i in range(len(item)):
                elems.append(item[i])
        return [sg.Frame(title, [elems], k=self.gui_key(key, WTyp.FR), p=p, border_width=border_width,
                         relief=relief, visible=visible, element_justification=justify, expand_x=expand_x,
                         expand_y=expand_y)]

    def frame(self, key, content: list, title=EMPTY, border_width=0, relief=None, visible=True, p=P, justify='left',
              expand_y=False, expand_x=False, font=None) -> list:
        font = self._CM.get_font(addition=4) if not font else font
        return [
            sg.Frame(title, content, k=self.gui_key(key, WTyp.FR), p=p, border_width=border_width, relief=relief,
                     visible=visible, element_justification=justify, expand_x=expand_x, expand_y=expand_y, font=font)]

    def button_frame(self, key, title=None, p=2) -> list:
        return self.frame(key, content=[[self.button(key, button_text=title)]], border_width=3, p=p,
                          relief=sg.RELIEF_RAISED)

    def lbl_cal(self, key, x=X1, dft=None, expand_x=False, evt=True, date_format='%Y-%m-%d', m_d_y=None,
                disabled=False, location=(0, 0)):
        """ label - input """
        # Unfortunately Location parameter can not be set dynamically...
        # dft = yyyymmdd (from config)
        dft = None if dft == NONE else self.get_setting(key)
        # Convert to MDY for calendar display
        if dft and not m_d_y:
            date = format_date(dft, 'YMD')
            if date:
                m_d_y = (int(date[5:7]), int(date[8:]), int(date[:4]))
        if not m_d_y:
            m_d_y = (None, None, None)
        # Convert to DMY for output # Todo
        # For CalendarButton, only format='%Y-%m-%d' seems to work.
        dft = format_date(dft, 'YMD', output_format='DMY')
        result = [self.label(name=key, x=x, tip=self.get_tooltip(key)),
                  self._input_text(key, dft, x, evt, expand_x, disabled=disabled),
                  sg.CalendarButton('Calendar', k=self.gui_key(key, WTyp.CA), format=date_format,
                                    default_date_m_d_y=m_d_y, disabled=disabled, location=location)]
        return result

    def cbx(self, key, x=X1, dft: bool = False, evt=True, disabled=False, tip=True, label_color=None):
        """ check box """
        result, dft = self._get_box_label_and_default(key, WTyp.CB, dft, x, disabled)
        if not isinstance(dft, bool):
            dft = False
        return [sg.Checkbox(
            text=self._get_label(key), text_color=label_color, k=self.gui_key(key, WTyp.CB), default=dft, size=(x, Y1),
            enable_events=evt, p=P1, tooltip=self.get_tooltip(key) if tip else None, disabled=disabled)]

    def radio(self, key, group_id, x=X1, dft: bool = False, evt=True, disabled=False, tip=True, label_color=None):
        """ radio button """
        result, dft = self._get_box_label_and_default(key, WTyp.RA, dft, x, disabled)
        if not isinstance(dft, bool):
            dft = False
        return [sg.Radio(
            text=self._get_label(key), group_id=group_id, text_color=label_color, k=self.gui_key(key, WTyp.RA),
            default=dft, size=(x, Y1), enable_events=evt, p=P1, tooltip=self.get_tooltip(key) if tip else None)]
    # Boxes with separate label

    # noinspection PyTypeChecker
    def inbox(self, key, x=X1, dft=None, expand_x=False, x2=X1, evt=True, folder_browse=False, file_browse=False,
              disabled=False, font=None, label_only=False, label_color=None, label_name=None, background_color=None,
              text_color=None, format_function=None):
        """ label """
        if label_only:
            return [self.label(name=dft, k=key, x=x, text_color=label_color, font=font)]
        """ label - input - file/folder browse"""
        target = self.gui_key(key, WTyp.IN)
        result, dft = self._get_box_label_and_default(key, WTyp.IN, dft, x, disabled, font, label_name)
        # Optionally format the value
        dft = format_function(dft) if format_function and isinstance(format_function, Callable) else dft
        if not label_only:
            readonly = True if folder_browse or file_browse else False
            result.append(
                self._input_text(key, dft, x2, evt, expand_x, disabled, readonly, background_color, text_color))
        if folder_browse:
            dft = self._get_valid_folder_name(key, dft)
            result.append(sg.FolderBrowse(
                target=target, initial_folder=dft, k=self.gui_key(f'{key}_BTN', WTyp.DB), enable_events=evt))
        elif file_browse:
            dft = self._get_valid_folder_name(key, dft)
            result.append(sg.FileBrowse(
                target=target, initial_folder=dft, k=self.gui_key(f'{key}_BTN', WTyp.FB), enable_events=evt))
        return result

    # noinspection PyTypeChecker
    def combo(self, key, items=None, x=X1, dft=None, evt=True, extra_label=None, extra_label_key=None,
              button_text=None, disabled=False, max=None, background_color=None, text_color=None,
              font=None):
        """ combo box """
        max = self._CM.get_combo_max() if max is None else max
        dft = items[0] if dft is None and len(items) == 1 else dft  # Single value
        result, dft = self._get_box_label_and_default(key, WTyp.CO, dft, x, disabled, font=font)
        background_color = background_color if background_color else COLOR_BACKGROUND_DISABLED if disabled else None
        text_color = text_color if text_color else COLOR_TEXT_DISABLED if disabled else None
        result.append(sg.Combo(
            items, k=self.gui_key(key, WTyp.CO), default_value=dft, enable_events=evt, disabled=disabled,
            background_color=background_color, text_color=text_color, size=(width(items), min(len(items), max)),
            readonly=True, font=font))
        return self._add_extras(result, extra_label, extra_label_key, button_text)

    # noinspection PyTypeChecker
    def options(self, key, items=None, x=X1, dft=None, evt=True, extra_label=None, extra_label_key=None,
                button_text=None, dft_none_is_all=False, disabled=False, max=10, no_label=False):
        """ List box """
        result, dft = self._get_box_label_and_default(key, WTyp.LB, dft, x, disabled)
        default_values = items if dft_none_is_all else dft
        result = [] if no_label else result
        result.append(sg.Listbox(
            items, k=self.gui_key(key, WTyp.LB), default_values=default_values, enable_events=evt,
            disabled=disabled, select_mode='extended', size=(width(items), min(len(items), max))))
        return self._add_extras(result, extra_label, extra_label_key, button_text)

    def multi_line(self, key, dft=None, x=X1, y=Y1, p=P1, evt=False, expand_x=False, disabled=False, text_color=None,
                   background_color=None, no_scrollbar=False):
        # evt = False if disabled else evt
        text_color = COLOR_LABEL_DISABLED if not text_color and disabled else text_color
        background_color = COLOR_BACKGROUND_DISABLED if not background_color and disabled else background_color
        self.set_gui_value_keys(key, WTyp.ML)
        return sg.Multiline(
            size=(x, y), k=self.gui_key(key, WTyp.ML), default_text=dft, enable_events=evt, p=p, expand_x=expand_x,
            disabled=disabled, background_color=background_color, text_color=text_color, no_scrollbar=no_scrollbar)

    @staticmethod
    def _get_label(text):
        label = get_config_label(text)
        return label or text

    def get_font(self, font_type=None, addition=0) -> tuple:
        return self._CM.get_font(font_type, addition)

    def _initialize_hidden_popup(self, popup_key):
        return self._CM.initialize_hidden_popup(popup_key)

    def _update_hidden_popup(self, popup_key, hidden_popup_value):
        return self._CM.update_hidden_popup(popup_key, hidden_popup_value)

    def _get_location(self, title):
        return self._CM.get_location(title)

    def _set_location(self, title, location):
        return self._CM.set_location(title, location)

    def _set_radio_button(self, key, value):
        return self._CM.set_radio_button(key, value)

    # Private
    def _get_box_label_and_default(
            self, key, box_type, dft, x, disabled=False, font=None, label_name=None) -> (Any, list):
        """
        dft: Return Setting-value if "key" is the name of setting, or Passed value.
        """
        text_color = COLOR_LABEL_DISABLED if disabled else None
        self.set_gui_value_keys(key, box_type)
        value = self.get_setting(key)
        # No internal values
        if value and isinstance(value, str) and value.startswith('*') and value.endswith('*'):
            value = EMPTY
        dft = dft if value is None else value  # value may be "False" in a cbx!
        return [self.label(
            name=label_name or key, x=x, tip=self.get_tooltip(key), text_color=text_color, font=font)], dft

    def _add_extras(self, result: list, extra_label, extra_label_key=None, button_text=None) -> list:
        if extra_label:
            self.set_gui_value_keys(extra_label_key or extra_label, WTyp.LA)
            result.append(self.label(name=extra_label, k=extra_label_key))
        if button_text:
            result.append(self.button(button_text))
        return result

    def _input_text(self, key, dft=None, x=X1, evt=False, expand_x=False, disabled=False, readonly=False,
                    background_color=None, text_color=None):
        evt = False if disabled else evt
        self.set_gui_value_keys(key, WTyp.IN)
        return sg.InputText(size=(x, Y1), k=self.gui_key(key, WTyp.IN), default_text=dft, enable_events=evt,
                            p=P1, readonly=readonly, background_color=background_color, text_color=text_color,
                            expand_x=expand_x, disabled=disabled, disabled_readonly_text_color=COLOR_TEXT_DISABLED,
                            disabled_readonly_background_color=COLOR_BACKGROUND_DISABLED)

    def set_disabled(self, window, widget_label, disabled=True):
        self.set_property(window, widget_label, disabled=disabled)

    def set_visible(self, window, widget_label, visible=False):
        self.set_property(window, widget_label, visible=visible)

    def set_property(self, window, widget_label, widget_type=None, **kwargs):
        if not widget_type:
            widget_type = gui_name_types.get(get_name_from_text(widget_label))
        if widget_type == WTyp.LA:
            self._set_property_label(window, widget_label, **kwargs)
        elif widget_type == WTyp.CO:
            self._set_property_label(window, widget_label, **kwargs)
            window[self.gui_key(widget_label, WTyp.CO)].update(**kwargs)
        elif widget_type == WTyp.IN:
            self._set_property_label(window, widget_label, **kwargs)
            window[self.gui_key(widget_label, WTyp.IN)].update(**kwargs)
        elif widget_type == WTyp.CA:
            self._set_property_label(window, widget_label, **kwargs)
            window[self.gui_key(widget_label, WTyp.CA)].update(**kwargs)
        elif widget_type == WTyp.CB:
            window[self.gui_key(widget_label, WTyp.CB)].update(**kwargs)
        elif widget_type == WTyp.FR:
            window[self.gui_key(widget_label, WTyp.FR)].update(**kwargs)
        elif widget_type == WTyp.BT:
            window[self.gui_key(widget_label, WTyp.BT)].update(**kwargs)
        else:
            raise GeneralException(f'{__name__}: Unsupported widget type "{widget_type}" for "{widget_label}"')

    def _set_property_label(self, window, widget_label, **kwargs):
        if 'visible' in kwargs:
            window[self.gui_key(widget_label, WTyp.LA)].update(visible=kwargs['visible'])
        if 'text' in kwargs:
            window[self.gui_key(widget_label, WTyp.LA)].update(value=kwargs['text'])

    def get_setting(self, k):
        setting = self._CM.get_config_item(k)
        # Checkbox must be boolean
        if not setting or isinstance(setting, bool):
            return setting
        if isinstance(setting, str) and setting.lower() in ('yes', 'no', 'true', 'false'):
            return toBool(setting)
        else:
            return setting

    def set_setting(self, k, value):
        self._CM.set_config_item(k, value)

    def default(self, setting):
        return self.get_setting(setting)

    def _get_valid_folder_name(self, key, dft):
        if key.endswith('_soph'):
            key = key.rstrip('_soph')
            dft = self.get_setting(key)
        return normalize_dir(dft)
