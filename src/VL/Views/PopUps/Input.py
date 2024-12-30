import os

import PySimpleGUI as sg

from src.DL.Objects.Window import Window
from src.VL.Data.Constants.Color import COLOR_LABEL_DISABLED, STATUSBAR_COLOR_INFO
from src.VL.Data.Constants.Const import CMD_OK, STATUS_MESSAGE, CMD_HELP_INPUT_BOX, PATH_WIDTH_MIN
from src.DL.Lexicon import CONFIG
from src.VL.Data.WTyp import WTyp
from src.VL.Functions import get_name_from_key, get_width, help_message, is_help_available
from src.VL.Views.BaseView import BaseView
from src.GL.BusinessLayer.ConfigManager import get_label
from src.GL.Const import EMPTY
from src.GL.Functions import is_valid_file
from src.GL.Result import Result
from src.GL.Validate import normalize_dir
from src.VL.Windows.General.MessageBox import MessageBox

FRAME_HELP = 'Help bij input box'


class Input(BaseView):

    def get_view(self) -> list:
        pass

    def __init__(self, relative_location=(None, None)):
        super().__init__()
        self._selected_folder = None
        self._selected_path = None
        if relative_location != (None, None):
            self._relative_location = relative_location

    def get_input(self, label, title='Specificeer', dft=None, unit_test=False) -> str:
        if not label:
            return EMPTY
        if unit_test:
            return dft
        return self._process_box(label, title, dft=dft)

    def get_folder(self, key) -> str:
        """ use set_folder without setting the folder in config """
        self.set_folder_in_config(key, Result(), set_folder=False)
        return self._selected_folder

    def get_path(self, key) -> str:
        """ use set_path without setting the path in config """
        self.set_path_in_config(key, set_path=False)
        return self._selected_path

    def set_folder_in_config(self, key, result: Result = None, version=EMPTY, set_folder=True) -> bool:
        """ Key: E.g. CF_WORKING_DIR """
        # Optionally first show result from parent while loop
        if not result.OK:
            MessageBox().message_box(result.get_messages_as_message(), severity=result.severity)
        # Go!
        dft = self.get_setting(key) or EMPTY
        if self._session.unit_test and dft:
            return True
        while True:  # Required
            label = get_label(key)
            text = f'Kies de {label}' if 'folder' in label.lower() else f'Kies de folder met {label}'
            input_value = self._process_box(key, text, folder_browse=True, dft=dft, version=version)
            if input_value is None:  # closed
                break
            if input_value and os.path.isdir(input_value):
                if set_folder:
                    self.set_setting(key, normalize_dir(input_value))
                else:
                    self._selected_folder = input_value
                return True
        return False

    def set_path_in_config(self, key, optional=False, set_path=True) -> bool:
        """ Key: E.g. CF_IMPORT_BOOKINGS_PATH """
        dft = self.get_setting(key) or EMPTY
        label = f'Dit kun je ook later instellen in tab {CONFIG}.' if optional else EMPTY
        input_value = self._process_box(key, f'Kies het bestand met {get_label(key)}', file_browse=True, dft=dft,
                                        label=label, optional=optional)
        if is_valid_file(input_value):
            if set_path:
                self.set_setting(key, input_value)
            else:
                self._selected_path = input_value
            return True
        return False

    def _process_box(self, input_key, window_title, folder_browse=False, file_browse=False, dft=EMPTY, label=EMPTY,
                     optional=False, version=EMPTY) -> str:
        """ A value is required, unless optional or the box window is closed. """
        if optional:
            window_title = f'{window_title} (optioneel)'
        layout = self._get_window(input_key, folder_browse, file_browse, dft, label, version)
        window = Window(window_title, layout, relative_location=self._relative_location).instance()

        while True:
            event, values = window.read()  # type: str, dict
            event_key = get_name_from_key(event)
            input_value = None

            if event == sg.WIN_CLOSED:
                break

            # Button clicks
            # - Help
            if event_key == CMD_HELP_INPUT_BOX:
                help_message(input_key)
                continue
            # - OK
            if event_key == CMD_OK:
                input_value = values.get(self.gui_key(input_key, WTyp.IN))
                if input_value or optional or input_value == dft:
                    break
            # - Browse
            elif event_key == input_key:
                window[STATUS_MESSAGE].update(value=EMPTY)
                continue

            # Required: message
            message = self._get_text_invalid_input(input_value, folder_browse)
            window[STATUS_MESSAGE].update(value=message)

        window.close()
        # Reset location
        self._relative_location = (None, None)
        return input_value

    @staticmethod
    def _get_text_invalid_input(input_value, folder_browse):
        item_type = 'Folder' if folder_browse else 'Bestand'
        message = f'Een waarde is verplicht.' if not input_value else f'{item_type} bestaat niet. '
        browse_text = f'Druk op "Browse" om een {item_type} te kiezen.' if folder_browse else EMPTY
        message = f'{message}{browse_text}'
        return message

    def _get_window(self, gui_key, folder_browse=False, file_browse=False, dft=None, label=EMPTY, version=EMPTY) \
            -> list:
        x = max(get_width(self._get_label(gui_key)), len(label))
        x2 = 132 if dft is None else len(dft)
        if not x2 and (folder_browse or file_browse):
            x2 = PATH_WIDTH_MIN
        lists = [self.multi_frame('InputBox_input_help', [
            self.inbox(gui_key, dft=dft, x=x, x2=x2, folder_browse=folder_browse, file_browse=file_browse,
                       evt=True),
            self.frame(FRAME_HELP, [
                [self.button(CMD_HELP_INPUT_BOX, button_text='?', transparent=True, p=0)]
            ], p=0, border_width=1, visible=is_help_available(gui_key))
        ], p=0)]
        if label:
            lists.append([self.label(label)])
        lists.append(
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, size=(90, 1), expand_x=True, relief=sg.RELIEF_SUNKEN,
                          text_color=STATUSBAR_COLOR_INFO)]
        )
        lists.append(self.frame('OKButton', [[self.button(CMD_OK)]], justify='right', expand_x=True,  p=2))
        if version:
            lists.append(self.frame(
                'frame_version', [[self.label(version, text_color=COLOR_LABEL_DISABLED)]],
                justify='right', expand_x=True, p=0, border_width=0, font=self.get_font(addition=-2)))
        return [self.frame('InputBox', lists, p=0)]
