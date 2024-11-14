import base64
import re

from src.DL.Lexicon import ANNUAL_ACCOUNT, PERIODIC_ACCOUNTS, PERIODIC_ACCOUNT
from src.DL.Model import EMPTY
from src.GL.Const import BLANK, EXT_CSV
from src.GL.Functions import is_valid_file
from src.GL.Validate import isInt


def get_icon():
    from src.GL.BusinessLayer.SessionManager import Singleton as Session
    icon = f'{Session().images_dir}Logo.png'
    icon = icon if is_valid_file(icon) else None
    if not icon:
        return None
    with open(icon, 'rb') as f:
        result = base64.b64encode(f.read())
    return result


def get_fonts() -> list:
    from tkinter import Tk, font
    root = Tk()
    font_tuple = font.families()
    root.destroy()
    return [font for font in font_tuple]


def get_image_path(image_name):
    from src.GL.BusinessLayer.SessionManager import Singleton as Session
    return f'{Session().images_dir}{image_name}'


def get_BBAN_from_IBAN(value):
    if not value or isInt(value):  # Already BBAN
        return value

    soph_value = value.replace(BLANK, EMPTY)  # "NL 12 INGB 3456789" => "NL12INGB3456789"
    if not value or not re.search(r'^[A-Z]{2}\d{2}[A-Z]{4}\d{5,}$', soph_value):
        return value

    p = len(soph_value) - 1
    while p > -1 and soph_value[p].isdigit():
        p -= 1
    return soph_value[p + 1:].lstrip('0')


def sophisticate_account_number(value):
    """ return: input value if it can not be sophisticated. """
    names = value.split()  # Split on blank
    # Normal account number
    if len(names) <= 1:
        return value
    # BIC element
    elif any([re.search(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?', name) for name in names]):
        # Filter out BIC
        names = [name for name in names if not re.search(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?', name)]
    return EMPTY.join(names)


def get_annual_account_filename(year, max_month, title=None):
    title = ANNUAL_ACCOUNT if not title else title
    return f'{title} {year} tm maand {max_month}{EXT_CSV}'


def get_periodical_account_filename(year, title=None):
    return f'{PERIODIC_ACCOUNT} {year} tm maand {title}{EXT_CSV}'