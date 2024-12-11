from src.DL.Config import configDef
from src.DL.Objects.ConfigItem import ConfigItem
from src.VL.Data.Constants.Color import STATUSBAR_COLOR_BACKGROUND, STATUSBAR_COLOR_INFO, \
    STATUSBAR_COLOR_WARNING, STATUSBAR_COLOR_ERROR
from src.VL.Data.Constants.Const import STATUS_MESSAGE
from src.GL.Const import EMPTY, BLANK
from src.GL.Enums import MessageSeverity, ColorTableau

gui_name_types = {}
gui_values = {}


def get_name_from_key(k, ignore_types: list = None) -> str:
    """
    Examples:
        'CHECK_ONLY_CB' -> 'CHECK_ONLY'
        'CF_TOTAL_REVENUES_COLOR' -> 'TOTAL_REVENUES_COLOR'
    """
    if isinstance(k, tuple):  # Table row
        return k[0]
    # Special case: Calendar widget is empty, date is in WTyp.IN, not in WTyp.CA.
    # In that case return the whole key.
    if ignore_types:
        for i in ignore_types:
            if k and k.endswith(i):
                return k
    p = k.find('|') + 1 if k else -1  # No "|", then p=0, else skip "|".
    q = k.rfind('_') if k else -1
    return k[p:q] if q > 0 else k


def get_capitalized_from_key(k) -> str:
    """ Example: 'CHECK_ONLY_CB:' -> 'Check only' """
    if not isinstance(k, str):
        return k
    result = get_name_from_key(k)
    if result:
        result = result.replace('_', BLANK)
    return result.capitalize() if result else k


def get_name_from_text(text, LC=False) -> str:
    """ Example: 'Check only: ' -> 'CHECK_ONLY' """
    if not text or not isinstance(text, str):
        return text
    text = text.replace(BLANK, '_').replace(':', EMPTY)
    if text and text[0] == '_':
        text = text[1:]
    if text and text[-1] == '_':
        text = text[:-1]
    if not text:
        return EMPTY
    return text.lower() if LC else text.upper()


def get_col_widths(data, col_widths=None, col_width_max=80, font_size: int = 0) -> dict:
    """
    data: DB detail rows, including Id and audit data.
    col_widths:
        {No : col_width } or None.
        A col_width is defined in the model (optional attribute). Default col_width=0.
    """
    col_widths = {} if not col_widths else col_widths
    if not data or len(data) < 1:  # No details
        return col_widths

    # Determine maximum col_widths encountered (with a maximum of col_width_max).
    col_widths_result = {}
    for row in data:  # Every data row
        for i in range(len(row)):
            # Static col_width if specified as > 0.
            col_w = col_widths.get(i)
            if col_w and col_w > 0:
                col_widths_result[i] = col_w
            # Dynamic col_width if it is not specified.
            elif isinstance(row[i], str):
                max_w = col_widths_result.get(i) or 0
                col_widths_result[i] = max(min(col_width_max, len(row[i]) + 1), max_w)
            # Other non-string like Id and audit dates
            else:
                col_widths_result[i] = 0
    # Font correction
    for i in range(len(data[0])):
        if col_widths_result[i] > 0 and font_size > 0:
            diff = 12 - font_size
            if diff > 0:
                col_widths_result[i] += diff

    return col_widths_result


def progress_meter(i, max_len, key, title, message_1=EMPTY, message_2=EMPTY) -> bool:
    import PySimpleGUI as sg
    if not sg.one_line_progress_meter(
            key, i + 1, max_len, title, message_1, message_2, orientation='h', no_titlebar=True,
            grab_anywhere=True, bar_color=('white', 'red')):
        return False
    return True


def help_message(key):
    from src.VL.Windows.General.MessageBox import MessageBox
    item = configDef.get(key, ConfigItem())
    message = item.tooltip or 'Er is geen help tekst gevonden.'
    title = item.label or 'Helptekst'
    MessageBox().message_box(message, title=title, severity=MessageSeverity.Completion)


def is_help_available(key) -> bool:
    item = configDef.get(key, ConfigItem())
    return True if item.tooltip else False


def status_message(window=None, message=EMPTY, severity=None):
    if not window or STATUS_MESSAGE not in window.AllKeysDict:
        return
    if severity == MessageSeverity.Warning:
        text_color = STATUSBAR_COLOR_WARNING
    elif severity == MessageSeverity.Error:
        text_color = STATUSBAR_COLOR_ERROR
    else:
        text_color = STATUSBAR_COLOR_INFO

    window[STATUS_MESSAGE].update(
        remove_lf(message), text_color=text_color, background_color=STATUSBAR_COLOR_BACKGROUND)


def remove_lf(line) -> str:
    return line.replace('\n', BLANK)


def get_width(text):
    lines = text.split('\n')
    return max(len(line) for line in lines)


def set_focus_on_row(window_table, current_row_no):
    if not window_table or current_row_no < 0:
        return
    # Re-Grab table focus using ttk
    window_table.SetFocus(force=True)
    children = window_table.Widget.get_children()
    if not children:
        return
    # No. of rows may have been changed in empty_booking mode
    if len(children) < current_row_no + 1:
        current_row_no = 0
    table_row = children[current_row_no]
    window_table.Widget.selection_set(table_row)  # move selection
    window_table.Widget.focus(table_row)  # move focus
    window_table.Widget.see(table_row)  # scroll to show it


def map_tableau_color(color_name) -> str:
    return ColorTableau.mapping[color_name] \
        if color_name and color_name in ColorTableau.mapping \
        else EMPTY
