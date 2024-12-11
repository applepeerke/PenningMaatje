import PySimpleGUI as sg

from src.DL.Objects.Window import Window
from src.VL.Data.Constants.Color import COLOR_LABEL_DISABLED, TEXT_COLOR, COLOR_BACKGROUND
from src.VL.Data.Constants.Const import CMD_OK
from src.VL.Functions import get_name_from_key, get_name_from_text, get_width
from src.VL.Views.BaseView import BaseView
from src.GL.BusinessLayer.SessionManager import Singleton as Session

option_text = 'Toon deze popup niet opnieuw.'


class Info(BaseView):

    def get_view(self) -> list:
        pass

    def __init__(self):
        super().__init__()
        self._hidden_popup_value = False

    def info(self, popup_key, text, title='Info', hide_option=True):

        self._hidden_popup_value = self._initialize_hidden_popup(popup_key)

        # Info with hide-option
        if hide_option:
            # User has told popup to hide, then always confirmed.
            if self._hidden_popup_value is True:
                return True
            else:
                # Otherwise show the popup.
                self._box_with_hide_option(text, title)
                self._update_hidden_popup(popup_key, self._hidden_popup_value)
        else:
            sg.PopupOK(
                f'\n{text}\n', title=title, grab_anywhere=True, keep_on_top=True, font=self.get_font(),
                icon=self._session.get_icon(),
                location=self._get_location(title))

    def _box_with_hide_option(self, text, title):
        self._hide_next_time = False

        # Get sg window, layout populated by model
        location = self._get_location(title)

        window = Window(title, self._get_window(text), location=location).instance()

        while True:
            event, values = window.read()  # type: str, dict
            event_key = get_name_from_key(event)

            if event == sg.WIN_CLOSED:
                self._set_location(title, location)
                break

            # Location
            location = window.current_location()

            # Button clicks
            if event_key == CMD_OK:
                break
            # Checkbox clicked
            elif event_key == get_name_from_text(option_text):
                self._hidden_popup_value = values.get(event)

        window.close()

    def _get_window(self, text) -> list:
        x = max(get_width(self._get_label(text)), len(option_text))
        y = text.count('\n') + 1
        lists = [
            [self.multi_line('Box-text', dft=text, x=x, y=y, no_scrollbar=True, disabled=True,
                             text_color=TEXT_COLOR, background_color=COLOR_BACKGROUND)],
            self.multi_frame('OKButton', [[self.button(CMD_OK)]]),
            self.cbx(option_text, x=x, label_color=COLOR_LABEL_DISABLED)]
        return [self.frame('Box', lists, p=0)]
