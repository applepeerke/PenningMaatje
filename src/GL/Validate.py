#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

import os
import platform
import re

from PenningMaatje import slash
from src.DL.DBDriver.Const import DB_TRUE, DB_FALSE
from src.VL.Data.Constants.Const import LEEG
from src.GL.Const import EMPTY
from src.GL.Enums import ColorTableau

valid = False
current = False

alphanum = re.compile(r'^[\w -_]$')
booking_code = re.compile(r'^[\w.]$')
path_name = re.compile(r'^[\w -_.#$&/\\]$', re.IGNORECASE)
dir_name = re.compile(r'^[\w -_.#$&/\\]$', re.IGNORECASE)
file_name = re.compile(r'^[\w -_.#$&]$', re.IGNORECASE)
csv_text = re.compile(r'^[\w -_.,\'"*#@$%()^&!+?:;/\\]$', re.IGNORECASE)
amount = re.compile(r'^[,.\d-]$')
date = re.compile(r'^[\d-]$')
account = re.compile(r'^[A-Z\d ]$')
like_account = re.compile(r'^[A-Z\d -]$')

""" 
Transformations 
"""


def normalize_dir(dirname, create=False):
    if not dirname:
        return EMPTY
    dirname = format_os(dirname)
    if create and not os.path.isdir(dirname):
        try:
            os.makedirs(dirname)
        except NotADirectoryError:
            raise
    return dirname if dirname[-1] in ('/', '\\') else f'{dirname}{slash()}'


def format_os(path_part):
    # On Windows, use backslash.
    if platform.system() == 'Windows':
        path_part = str(path_part).replace('/', '\\')
    return path_part


def isIntOrNone(value):
    if not value:
        return True
    return isInt


def isDateOrNone(value):
    if not value or value == '0':
        return True
    return isDate(value)


def isInt(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def isCommaRepresentation(value):
    return True if value in (',', '.') else False


def isTrue(value: str):
    if not isinstance(value, str):
        return value
    return False if not value or value.lower() in ('false', '0') else True


def isBool(value) -> bool:
    if isinstance(value, bool):
        return True


def isColorTableauKey(key):
    return key in ColorTableau().mapping


def isList(value) -> bool:
    if isinstance(value, list):
        return True


def toBool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, str) and value:
        return False if value.lower() in ('false', 'no', 'n', 'nee') else True
    else:
        return default


def toBool_DB(value) -> str:
    return DB_TRUE if value in (True, '1') else DB_FALSE


def isAlphaNumeric(value, maxLen=0):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    return all(alphanum.match(x) for x in value)


def isAlphaNumericOrEmpty(value, maxLen=0):
    return True if value == LEEG else isAlphaNumeric(value, maxLen)


def isAlphaNumericOrNone(value, maxLen=0):
    return True if value is None else isAlphaNumeric(value, maxLen)


def isBookingCodeOrEmpty(value):
    return True if value == LEEG else all(booking_code.match(x) for x in value)


def isCsvText(value, maxLen=0):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    return all(csv_text.match(x) for x in value)


def isCsvTextOrNone(value, maxLen=0):
    return True if value is None else isCsvText(value, maxLen)


def isAmount(value: str, maxLen=20):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    return all(amount.match(x) for x in value)


def isDate(value: str):
    value = make_string(value)
    if len(value) not in (8, 10):
        return False
    if len(value) == 10:
        if len(value.replace('-', EMPTY).replace('/', EMPTY)) != 8:
            return False
    return all(date.match(x) for x in value)


def isFormattedDate(value: str):
    """ Must be of format yyyy-mm-dd """
    if not value or not isinstance(value, str) or len(value) < 8 or '-' not in value:
        return False

    # Add leading zeroes
    # - Example: 1960-1-1 => 1960-01-1
    value = f'{value[:5]}0{value[5:]}' if value[6] == '-' else value
    # - Example: 1960-01-1 => 1960-01-01
    value = f'{value[:8]}0{value[8:]}' if len(value) == 9 else value

    if len(value) < 10 or value[4] != '-' or value[7] != '-':
        return False
    if len(value.replace('-', EMPTY)) != 8:
        return False
    if not all(date.match(x) for x in value):
        return False
    return 1900 < int(value[:4]) < 2200 and 0 < int(value[5:7]) < 13 and 0 < int(value[8:]) < 32


def isAccount(value: str, maxLen=34):
    value = make_string(value)
    if 0 < maxLen < len(value) or isDate(value):
        return False
    return all(account.match(x) for x in value)


def likeAccount(value: str, maxLen=34):
    """ Spaarrekening  """
    value = make_string(value)
    if 0 < maxLen < len(value) or isDate(value):
        return False
    return all(like_account.match(x) for x in value)


def isCD(value):
    value = make_string(value)
    return value.lower() in ('c', 'd', 'credit', 'debet', 'af', 'bij')


def isAccountName(value):
    """ Must not be a code """
    value = make_string(value)
    if len(value) < 3 or isAccount(value) or isAmount(value) or isCD(value):
        return False
    return isCsvText(value)


def isCode(value, maxLen=2):
    """ Must be a code """
    value = make_string(value)
    if len(value) > maxLen or isInt(value):
        return False
    return True


def isNotCode(value, maxLenCode=2):
    """ Must be a code """
    if isCode(value, maxLenCode):
        return False
    return True


def isPathname(value, maxLen=0):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    return all(path_name.match(x) for x in value)


def isDirname(value, maxLen=0):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    return all(dir_name.match(x) for x in value)


def isFilename(value, maxLen=0):
    value = make_string(value)
    if not value or 0 < maxLen < len(value):
        return False
    return all(file_name.match(x) for x in value)


def isExt(value, maxLen=0):
    value = make_string(value)
    if 0 < maxLen < len(value):
        return False
    if not str(value).startswith('.'):
        return False
    if not isAlphaNumeric(value[1:]):
        return False
    return True


def enforce_valid_name(name):
    re.sub(r'[^\x00-\x7F]+', '_', name)
    if len(name) > 64:
        name = name[:64]
    return name


def make_string(value) -> str:
    if value is None:
        return EMPTY
    if isinstance(value, str):
        return value
    return str(value)
