import PySimpleGUI as sg

from src.DL.Config import CF_AUTO_CLOSE_TIME_S
from src.VL.Data.Constants.Color import *
from src.VL.Data.Constants.Const import POPUP_WIDTH_MAX, POPUP_AUTO_CLOSE_DEFAULT
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.Functions import remove_color_code
from src.GL.Validate import toBool, isInt
from src.VL.Views.PopUps.Info import Info

CM = ConfigManager()


def message_box(
        message, cont_text=False, title=None, severity=MessageSeverity.Info, auto_close_duration=None,
        key=None) -> bool:
    """
    Returns confirmation on a message
    """
    session = Session()

    if not message:
        return False  # No confirmation

    title = MessageSeverity.get_title(severity, title)
    message = remove_color_code(str(message))

    # Calculate width from the message
    max_length, count = 0, 0
    escape = False
    length = len(message)
    for i in range(length):
        if escape:
            escape = False
            if message[i] == 'n':
                max_length = count if count > max_length else max_length
                count = 0
        if message[i] == '\\':
            escape = True
        else:
            count += 1
    # Last time
    max_length = count if count > max_length else max_length
    width = max_length if 0 < max_length < POPUP_WIDTH_MAX else POPUP_WIDTH_MAX

    auto_close = False
    if auto_close_duration is not None and auto_close_duration == 0:
        value = auto_close_duration
    else:
        value = CM.get_config_item(CF_AUTO_CLOSE_TIME_S)
    auto_close_duration = int(value) if isInt(value) else POPUP_AUTO_CLOSE_DEFAULT

    # Question?
    question = True if message.replace('\n', EMPTY).endswith('?') else False
    if not question and cont_text:
        question = True
        message = f'{message}\n\nDoorgaan?'

    # Button color
    if severity == MessageSeverity.Completion:
        button_color = (BUTTON_COLOR_TEXT, COLOR_COMPLETION)
    elif severity == MessageSeverity.Error:
        button_color = (BUTTON_COLOR_TEXT, COLOR_ERROR)
    elif severity == MessageSeverity.Warning:
        button_color = (BUTTON_COLOR_TEXT, COLOR_WARNING)
    elif severity == MessageSeverity.Info:
        button_color = (BUTTON_COLOR_TEXT, COLOR_OK)
        auto_close = True if auto_close_duration > 0 else False
    else:
        button_color = None

    # Unit test: Skip PopUp
    if session.unit_test:
        return session.unit_test_auto_continue if question else False

    # Question
    if question:
        answer = sg.PopupYesNo(message, title=title, button_color=button_color, font=CM.get_font(),
                               background_color=POPUP_COLOR_BACKGROUND, text_color=TEXT_COLOR, keep_on_top=True,
                               line_width=width, icon=session.get_icon())
        answer = toBool(answer)
        return answer
    # Not a question
    else:
        if key and severity == MessageSeverity.Info:
            Info().info(key, title=title, text=message)
        else:
            sg.Popup(message, title=title, button_color=button_color, font=CM.get_font(),
                     background_color=POPUP_COLOR_BACKGROUND, text_color=TEXT_COLOR, keep_on_top=True,
                     auto_close=auto_close, auto_close_duration=auto_close_duration, line_width=width, icon=session.get_icon())
        return False  # Do not confirm
