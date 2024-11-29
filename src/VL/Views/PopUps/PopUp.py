import PySimpleGUI as sg

from src.BL.Functions import get_icon
from src.DL.Config import CF_POPUP_INPUT_VALUE
from src.DL.Objects.Window import Window
from src.GL.Const import EMPTY
from src.GL.Enums import ActionCode
from src.GL.Result import Result
from src.VL.Data.Constants.Color import COLOR_LABEL_DISABLED, TEXT_COLOR, COLOR_BACKGROUND
from src.VL.Data.Constants.Const import CMD_OK, CMD_CANCEL
from src.VL.Functions import get_name_from_key, get_name_from_text, get_width
from src.VL.Views.BaseView import BaseView, CM

BLOCK_OPTION_TEXT = 'Toon deze popup niet opnieuw.'
BLOCK_TITLE = 'popup-title'
BLOCK_BUTTONS = 'popup-buttons'


class PopUp(BaseView):

    @property
    def result(self):
        return self._result

    def get_view(self) -> list:
        pass

    def __init__(self):
        super().__init__()
        self._result = Result()
        self._hidden_popup_value = False
        self._text = EMPTY
        self._x = len(BLOCK_OPTION_TEXT)
        self._y = 1

    def display(self, title='Popup', text=EMPTY):
        # UT: return the session value
        if self._session.unit_test:
            return self._session.unit_test_auto_continue

        # Show the popup.
        location = self._get_location(title)
        window = Window(title, self._get_window(text, buttons=False), location=location).instance()
        while True:
            event, values = window.read()  # type: str, dict
            if event == sg.WIN_CLOSED:
                self._set_location(title, location)
                break
            # Location
            location = window.current_location()
        window.close()

    def confirm(self, popup_key, text, title='Bevestig', hide_option=True, user_input=True) -> bool:
        # UT: return the session value
        if self._session.unit_test:
            return self._session.unit_test_auto_continue

        self._hidden_popup_value = self._initialize_hidden_popup(popup_key)
        # User has told popup to hide, then always confirmed.
        if hide_option and self._hidden_popup_value:
            return True

        # PopUp with user input (default)
        if user_input:
            answer = self._dialog(text, title)

        # Confirm popup
        else:
            answer = True if sg.PopupYesNo(
                f'\n{text}\n', title=title, grab_anywhere=True, keep_on_top=True, font=self.get_font(),
                icon=get_icon(), location=self._get_location(title)) == 'Yes' \
                else False

        # Store hide option
        if hide_option:
            self._update_hidden_popup(popup_key, self._hidden_popup_value)

        return answer

    def _dialog(self, text, title) -> bool:
        answer = False
        self._hide_next_time = False
        input_value = CM.get_config_item(CF_POPUP_INPUT_VALUE)
        input_value_prv = input_value

        # Get sg window, layout populated by model
        location = self._get_location(title)

        window = Window(title, self._get_window(text), location=location).instance()

        while True:
            event, values = window.read()  # type: str, dict
            event_key = get_name_from_key(event)

            if event == sg.WIN_CLOSED:
                self._set_location(title, location)
                self._result = Result(action_code=ActionCode.Close)
                break

            if event == CF_POPUP_INPUT_VALUE:
                input_value = CM.get_config_item(CF_POPUP_INPUT_VALUE)

            # Location
            location = window.current_location()

            # Set in config (for now in Dialog this applies only to radio-button choices)
            self._set_radio_button(event_key, values.get(event))

            # Button clicks
            if event_key == CMD_OK:
                # Input value changed: then retry. Otherwise, it will be a Go.
                action_code = ActionCode.Retry if input_value and input_value != input_value_prv else ActionCode.Go
                self._result = Result(action_code=action_code)
                answer = True
                break
            elif event_key == CMD_CANCEL:
                answer = False
                self._result = Result(action_code=ActionCode.Cancel)
                break
            # Checkbox clicks
            elif event_key == get_name_from_text(BLOCK_OPTION_TEXT):
                self._hidden_popup_value = values.get(event)

        window.close()
        return answer

    def _get_window(self, text, buttons=True) -> list:
        self._text = text
        self._x = max(get_width(self._get_label(text)), len(BLOCK_OPTION_TEXT))
        self._y = text.count('\n') + 1
        return [self.frame(
            'PoUpBox',
            self._get_popup_layout(buttons=buttons),
            p=0)]

    def _get_popup_layout(self, block_name=None, buttons=True) -> list:
        block_title = [
            self.multi_line(BLOCK_TITLE, dft=self._text, x=self._x, y=self._y, no_scrollbar=True, disabled=True,
                            text_color=TEXT_COLOR, background_color=COLOR_BACKGROUND)]
        block_buttons = self.multi_frame(
                BLOCK_BUTTONS, [[self.button(CMD_OK)], [self.button(CMD_CANCEL)]])
        block_option = self.cbx(BLOCK_OPTION_TEXT, x=self._x, label_color=COLOR_LABEL_DISABLED)
        if block_name == BLOCK_TITLE:
            return [block_title]
        elif block_name == BLOCK_BUTTONS and buttons:
            return [block_buttons]
        elif block_name == BLOCK_OPTION_TEXT:
            return [block_option]
        elif buttons:
            return [block_title, block_buttons, block_option]
        else:
            return [block_title, block_option]
