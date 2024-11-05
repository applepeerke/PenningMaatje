#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import ntpath
import os
import platform
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from src.GL.GeneralException import GeneralException
from src.GL.Validate import format_os, normalize_dir, isInt, make_string
from src.GL.Const import BLANK, EMPTY, APP_NAME, COMMA_DB, COMMA_SOURCE

date_zeroes = '0000000000'


def replace_root_in_path(path, search_string=None, replace_by=''):
    if not search_string:
        slash = format_os('/')
        search_string = f'{slash}{APP_NAME}'
    current_path = os.path.dirname(os.path.realpath(__file__))
    index = current_path.find(search_string)
    if current_path.find(search_string) > 0:
        root = current_path[:index]
        if path and path.startswith(root):
            return path.replace(root, replace_by)
    return path


def file_as_bytes(file):
    with file:
        return file.read()


def skip_blanks(value: str, p) -> int:
    while -1 < p < len(value) and value[p] == BLANK:
        p += 1
    return p


def path_head(path, basename=None):
    path = normalize_dir(path)
    if not path:
        return None
    path = path[:-1]
    if path and not basename:
        path, tail = ntpath.split(path)
    else:
        tail = 'dummy'
        while tail and os.path.basename(path).lower() != basename.lower():
            path, tail = ntpath.split(path)
        if not tail:
            return None
    return normalize_dir(path)


def remove_color_code(text):
    if '\033' in text:
        text = text.replace('\033[0m', '')
        text = text.replace('\033[31m', '')
        text = text.replace('\033[32m', '')
        text = text.replace('\033[33m', '')
        text = text.replace('\033[34m', '')
        text = text.replace('\033[35m', '')
    return text


def remove_crlf(line):
    if line.endswith('\n') or line.endswith('\r'):
        line = line[:-1]
    if line.endswith('\n') or line.endswith('\r'):
        line = line[:-1]
    return line


def sanitize_text(text: str, special_chars: tuple = ("'", "\n"), replace_by: str = "_") -> str:
    try:
        if not text:
            return EMPTY
        for c in special_chars:
            if c in text:
                text = str.replace(text, c, replace_by)
    except TypeError:  # Not a string: pass
        pass
    finally:
        return text


def try_amount_input(amount):
    """ Reflect input to view even when wrong. """
    try:
        return FloatToStr(amount, zero_is_empty=True)
    except GeneralException:
        return amount


def toFloat(value, comma_source=COMMA_SOURCE, default=0.0, round_decimals=True, strict=True) -> float:
    """ E.g. transform input to database representation """
    if isinstance(value, float):
        return float(f'{round(value, 2):.2f}') if round_decimals is True else value

    # Default
    if not isinstance(default, float):
        default = 0.0
    default = float(f'{round(default, 2):.2f}') if round_decimals is True else default

    # Validation
    value = make_string(value)
    if not value:
        return default
    if not maybeFloat(value) or len(value) > 20:
        if strict:
            raise GeneralException(f'Waarde "{value}" kan niet naar een bedrag geconverteerd worden.')
        return default
    
    # Minus sign
    if value.endswith('-'):
        value = f'-{value[:-1]}'
        if len(value) == 1:
            return default
    if '-' in value[1:]:
        raise GeneralException(f'Min-teken op ongeldige plaats in bedrag "{value}".')
    # Whitelist
    if any(char not in '0123456789-.,' for char in value):
        raise GeneralException(f'Ongeldig bedrag "{value}".')
    if comma_source not in (',', '.'):
        raise GeneralException(f'Ongeldige komma representatie "{comma_source}".')

    # Only comma is relevant, not decimal points
    dec_point = ',' if comma_source == '.' else '.'
    if dec_point in value:
        c = value.find(comma_source)
        p = value.find(dec_point)
        # If comma found, it should be 3rd from right position.
        if c > -1 and (c < p or value[-3] != comma_source):
            raise GeneralException(f'Komma staat verkeerd in "{value}".')
        if (c == -1 and value[-4] != dec_point
                or (len(value) > 6 and value[-7] != dec_point)
                or (len(value) > 10 and value[-11] != dec_point)):
            raise GeneralException(f'Decimale punt staat verkeerd in "{value}".')
    value = value.replace(dec_point, EMPTY).replace(',', '.')

    try:
        return float(f'{round(float(value), 2):.2f}') if round_decimals is True else float(value)
    except ValueError:
        return default


def FloatToStr(
        amount,
        comma_source=COMMA_DB,
        comma_target=COMMA_SOURCE,
        add_decimals=True,
        justify=EMPTY,
        width=15,
        round_decimals=True,
        add_minus=True,
        valuta=EMPTY,
        zero_is_empty=False,
        error_is_empty=False
) -> str:
    """ From db representation to user (view) representation"""
    amount = make_string(amount)
    # Validation
    if not maybeFloat(amount) \
            or comma_source not in (',', '.') \
            or justify not in ('R', 'L', EMPTY) \
            or width <= len(str(amount)) \
            or width < 4:
        return amount

    # Preparation
    # - Round decimals (optionally)
    if round_decimals:
        p_comma = amount.find(comma_source)
        if p_comma > -1:
            decimal_part = amount[p_comma:]
            if len(decimal_part) > 3:
                amount = str(round(float(amount), 2))

    decimal_point_source = '.' if comma_source == ',' else ','
    decimal_point_target = '.' if comma_target == ',' else ','

    # Strip the amount and convert comma.
    # - Remove "-", '."  and blanks.
    f_amount = amount.replace(decimal_point_source, EMPTY).replace('-', EMPTY).strip()
    # - Remove leading zeroes.
    f_amount = f_amount.lstrip('0')
    # - Replace komma (Opt)
    if comma_source != comma_target:
        f_amount = f_amount.replace(comma_source, comma_target)
    if not f_amount:
        f_amount = f'0{comma_target}00'

    # Decimal part
    p_comma = f_amount.find(comma_target)
    decimal_part = comma_target if p_comma == -1 else f_amount[p_comma:]
    decimal_part = decimal_part.ljust(3, '0')  # Pad trailing zeroes

    # Numeric part
    numeric_part = f_amount[:p_comma] if p_comma > -1 else f_amount

    # Add decimals
    if add_decimals:
        result = []
        count = 0
        for i in range(len(numeric_part) - 1, -1, -1):
            count += 1
            result.append(numeric_part[i])
            if count % 3 == 0 and i > 0:
                result.append(decimal_point_target)
        result.reverse()
        numeric_part = EMPTY.join(result)

    # Combine the parts
    unsigned = f'{numeric_part or "0"}{decimal_part}'
    # "0.00" may be returned as ""
    if zero_is_empty and all(i == '0' for i in unsigned if i not in (',', '.')):
        return EMPTY
    minus = '-' if add_minus and '-' in amount else EMPTY
    valuta = f'{valuta} ' if valuta else EMPTY
    result = f'{valuta}{minus}{unsigned}'
    if len(result) > width:
        if error_is_empty:
            return EMPTY
        raise GeneralException(f'{__name__}: Bedrag "{f_amount}" is te groot voor de opgegeven grootte "{width}".')

    # Justify
    if justify:
        result = result.ljust(width) if justify.startswith('L') else result.rjust(width)
    return result


def maybeFloat(value: str) -> bool:
    """ Is this value possibly a string representation of a float """
    value = make_string(value)
    if (value not in (EMPTY, '.', ',', '-')
            and all(i in '0123456789.,-' for i in value)):
        # Check on date
        if '-' in value and value[0] != '-' and value[-1] != '-':
            return False
        return True


def get_age(birthday: int) -> int:
    born = datetime.strptime(str(birthday), '%Y%m%d')
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def get_date_from_age(birthday: int, age_years: int, age_months: int) -> int:
    """
    Add years and months to birthday.
    @return: Ymd
    """
    born = datetime.strptime(str(birthday), '%Y%m%d')
    # Add the years and months
    to_year = born.year + age_years
    to_month = born.month + age_months
    if to_month > 12:
        to_month = to_month - 12
        to_year += 1
    # Determine the day
    to_day = born.day
    count = 0
    while not _is_valid_date(to_year, to_month, to_day) and count < 5:
        count += 1
        to_day += 1
        if to_day > 31:
            to_day = 0
    # Date should be valid now.
    if not _is_valid_date(to_year, to_month, to_day):
        raise GeneralException(
            f'Datum kon niet bepaald worden uit geboortedatum "{birthday}" en leeftijd {age_years} en {age_months}.')
    return int(f'{to_year}{_pad_zeroes(str(to_month))}{_pad_zeroes(str(to_day))}')


def toDateDb(input_date, dft=0) -> int:
    """
    Convert date to db representation, i.e. yyyymmdd integer.
    N.B. Config dates may be corrupt, formatted, string or int.
    """
    input_date = format_date(input_date, get_date_format(input_date, allow_MDY=False), output_format='YMD')
    if input_date:
        input_date = input_date.replace('-', EMPTY)
    return int(input_date) if isInt(input_date) else dft


def get_date_format(input_date: str, allow_MDY=False, expected_input_format=None) -> str or None:
    """
    Requirements: year is in yyyy format.
    Return: 'YMD' or 'DMY' or 'YDM'. If not sure, EMPTY.
    """
    input_date = make_string(input_date)

    if not input_date or len(input_date) not in (8, 10):
        return None

    date_format, yyyy, mm, dd = EMPTY, EMPTY, EMPTY, EMPTY

    # First try if matches expectation
    if expected_input_format:
        if _is_valid_date(*_get_Y_m_d(input_date, expected_input_format)):
            return expected_input_format

    # A. Length 8 (no separators)
    if len(input_date) == 8 and isInt(input_date):
        # Year at the start and not at the end
        if 1900 < int(input_date[:4]) < 3000 and not 1900 < int(input_date[4:]) < 3000:
            date_format = 'YMD'
        # Year at the end and not at the start
        elif 1900 < int(input_date[4:]) < 3000 and not 1900 < int(input_date[:4]) < 3000:
            # Day at the start
            if 13 <= int(input_date[:2]) <= 31 or not allow_MDY:
                date_format = 'DMY'
            # Day in the middle
            elif 13 <= int(input_date[2:4]) <= 31:
                date_format = 'MDY'

    # B. Length 10 (with 2 separators)
    elif len(input_date) == 10:
        # Get the 2 positions of date separators (like '/' or '-')
        sep_index = [i for i in range(len(input_date)) if input_date[i] != BLANK and not isInt(input_date[i])]
        if not len(sep_index) == 2:
            return None  # unknown

        if sep_index == [4, 7]:  # yyyy-mm-dd
            date_format = 'YMD'
        elif sep_index == [2, 5]:  # dd-mm-yyyy / mm-dd-yyyy
            e1 = input_date[:2]
            e2 = input_date[3:5]
            if int(e2) > 12 and allow_MDY:
                date_format = 'MDY'
            elif int(e1) > 12 or not allow_MDY:
                date_format = 'DMY'

    return date_format if _is_valid_date(*_get_Y_m_d(input_date, date_format)) \
        else None


def _get_Y_m_d(input_date: str, input_format) -> (str, str, str):
    """
    @return: yyyy, mm, dd
    """
    # Format is known, convert to 8
    if len(input_date) == 10:
        input_date = input_date.replace('-', EMPTY)

    if input_format == 'YMD':
        return input_date[:4], input_date[4:6], input_date[6:]
    elif input_format == 'DMY':
        return input_date[4:], input_date[2:4], input_date[:2]
    elif input_format == 'MDY':
        return input_date[4:], input_date[:2], input_date[2:4]
    else:
        return EMPTY, EMPTY, EMPTY


def _is_valid_date(yyyy, mm, dd) -> bool:
    try:
        return isInt(yyyy) and isInt(mm) and isInt(dd) and datetime(int(yyyy), int(mm), int(dd))
    except ValueError:
        return False


def try_format_date_input(input_date, input_format=None, output_format=None) -> str:
    """ Returns invalid output too, to allow dynamically formatting when typing. MDY not allowed. """
    if not input_date:
        return EMPTY

    # When needed overrule specified (default) input format.
    tried_input_format = get_date_format(input_date, allow_MDY=False, expected_input_format=input_format)
    if tried_input_format and tried_input_format != input_format:
        input_format = tried_input_format

    result = format_date(
        input_date, input_format=input_format, allow_MDY=False, output_format=output_format)
    return input_date if not result else result


def format_date(
        input_date: str, input_format=None, output_separator='-', allow_MDY=True, output_format=None) -> str:
    """
    Requirements: Input is formatted string, where year is in yyyy format. Blank can not be a separator (EMPTY can).
    @return: yyyy-mm-dd (default), or format specified.
    """
    # Validate before
    if not input_date:
        return EMPTY

    input_date = make_string(input_date)

    # If "date time", remove the "time" part
    if len(input_date) > 10:
        if ':' in input_date:
            p = input_date.find(BLANK)
            if p:
                input_date = input_date[:p]
        if len(input_date) > 10:
            return EMPTY

    # Preserve hard input date format
    if not output_format and input_format:
        output_format = input_format

    # Try to calculate input date format if not specified (separators required)
    if input_format not in ('YMD', 'DMY', 'MDY'):
        if len(input_date) == 10:
            input_format = get_date_format(input_date, allow_MDY=allow_MDY)
            if not input_format:
                return EMPTY  # Error
        else:
            input_format = 'YMD'  # Assume db notation YMD

    # Get the 2 positions of date separators (like '/' or '-')
    sep_index = [i for i in range(len(input_date) - 1) if input_date[i] != BLANK and not isInt(input_date[i])]
    # If no separators, add them
    if not len(sep_index) == 2:
        if sep_index or len(input_date) != 8:
            return EMPTY  # Error
        if input_format == 'YMD':
            input_date = f'{input_date[:4]}{output_separator}{input_date[4:6]}{output_separator}{input_date[6:]}'
        elif input_format == 'DMY':
            input_date = f'{input_date[:2]}{output_separator}{input_date[2:4]}{output_separator}{input_date[4:8]}'
        else:  # MDY
            input_date = f'{input_date[2:4]}{output_separator}{input_date[:2]}{output_separator}{input_date[4:8]}'
        sep_index = [i for i in range(len(input_date) - 1) if input_date[i] != BLANK and not isInt(input_date[i])]

    # Get uniform date elements
    E1 = input_date[:sep_index[0]].lstrip()
    E2 = input_date[sep_index[0] + 1:sep_index[1]]
    E3 = input_date[sep_index[1] + 1:].rstrip()

    if input_format == 'YMD':
        YY = E1
        MM = _pad_zeroes(E2)
        DD = _pad_zeroes(E3)
    elif input_format == 'DMY':
        YY = E3
        MM = _pad_zeroes(E2)
        DD = _pad_zeroes(E1)
    else:  # MDY
        YY = E3
        MM = _pad_zeroes(E1)
        DD = _pad_zeroes(E2)

    # Validation after
    if not len(YY) == 4:
        return EMPTY

    # Output
    formatted_ymd = f'{YY}{output_separator}{MM}{output_separator}{DD}'

    # a. Invalid
    if not is_formatted_ymd(formatted_ymd):
        return EMPTY

    # b. Depending on detected input date format (Default: YMD)
    if output_format == 'YMD':
        return f'{YY}{output_separator}{MM}{output_separator}{DD}'
    elif output_format == 'DMY':
        return f'{DD}{output_separator}{MM}{output_separator}{YY}'
    elif output_format == 'MDY':
        return f'{MM}{output_separator}{DD}{output_separator}{YY}'
    else:
        return formatted_ymd


def is_formatted_ymd(input_date) -> bool:
    """ Is it a yyyy-mm-dd? """
    input_date = make_string(input_date)
    return True \
        if input_date and len(input_date) == 10 \
        and 1900 <= int(input_date[:4]) <= 3000 \
        and 1 <= int(input_date[5:7]) <= 12 \
        and 1 <= int(input_date[8:]) <= 31 \
        and input_date[4] == '-' and input_date[7] == '-' \
        else False


def add_months(input_date: int, months: int) -> int:
    """ Add a number of months to a date in db representation (yyyymmdd) """
    start_date = datetime.strptime(str(input_date), '%Y%m%d')
    return int(datetime.strftime(start_date + relativedelta(months=months), '%Y%m%d'))


def timestamp_from_string(date_Y_m_d, time_H_M_S=None):
    if time_H_M_S:
        time_stamp = time.mktime(
            datetime.strptime(f'{date_Y_m_d} {time_H_M_S}', '%Y-%m-%d %H:%M:%S').timetuple())
    else:
        time_stamp = time.mktime(
            datetime.strptime(f'{date_Y_m_d}', '%Y-%m-%d').timetuple())
    return time_stamp


def _pad_zeroes(element, length=2) -> str:
    if len(element) >= length:
        return element
    no_of_zeroes = length - len(element)
    return f'{date_zeroes[:no_of_zeroes]}{element}'


def creation_date(path_to_file, fmt='%Y%m%d') -> str:
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if not is_valid_file(path_to_file):
        return EMPTY
    if platform.system() == 'Windows':
        ts = os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            ts = stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            ts = stat.st_mtime
    crt_date = datetime.fromtimestamp(ts).strftime(fmt)
    return crt_date


def file_modification_date(path_to_file, fmt='%Y%m%d') -> str:
    if not is_valid_file(path_to_file):
        return EMPTY
    if platform.system() == 'Windows':
        ts = os.path.getmtime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        ts = stat.st_mtime
    return datetime.fromtimestamp(ts).strftime(fmt)


def file_mutation_date(path, fmt='%Y%m%d') -> str:
    c_date = creation_date(path, fmt)
    if not c_date:
        return EMPTY
    m_date = file_modification_date(path, fmt)
    return m_date if m_date and c_date and m_date > c_date else c_date


def file_staleness_in_days(path) -> int:
    if not file_mutation_date(path):
        return 0
    d1 = datetime.strptime(file_mutation_date(path, '%Y-%m-%d'), '%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    d2 = datetime.strptime(today, '%Y-%m-%d')
    return abs((d2 - d1).days)


def move_file(from_path, to_path) -> bool:
    if not is_valid_file(from_path):
        return False
    if os.path.isfile(to_path):
        os.remove(to_path)
    try:
        os.rename(from_path, to_path)
    except OSError as e:
        print(f'{__name__}: {e.args[0]}')
        return False
    return True


def remove_file(path) -> bool:
    if path and os.path.isfile(path):
        os.remove(path)
        return True
    return False


def tuple_to_value(value):
    if isinstance(value, str) and value and len(value) > 2 and value[0] == '(' and value[-1] == ')':
        return value[1:-1].split(',')[0]
    elif isinstance(value, tuple):
        return value[0]
    return value


def canonize(item, canonic=True):
    return item.lower().replace(BLANK, EMPTY) if canonic else item


def is_valid_file(path) -> bool:
    return True if path and os.path.isfile(path) and os.stat(path).st_size > 0 else False


def find_files(basedir):
    """
    Return all file paths in the specified base directory (recursively).
    """
    for path, dirs, files in os.walk(os.path.abspath(basedir)):
        yield path


def try_to_get_date_format(rows, index, path) -> str:
    date_format = _try_to_get_date_format(rows, index, allow_MDY=False)
    if not date_format:
        date_format = _try_to_get_date_format(rows, index, allow_MDY=True)
    if not date_format:
        raise GeneralException(f'Datum formaat kon niet vastgesteld worden in bestand\n"{path}".')
    return date_format


def _try_to_get_date_format(rows, col_no, allow_MDY, max_tries=1000) -> str or None:
    for i in range(0, min(len(rows), max_tries)):
        if date_format := get_date_format(rows[i][col_no], allow_MDY=allow_MDY):
            return date_format
    return None
