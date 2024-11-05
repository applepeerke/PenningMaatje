import os
import platform

from .Const import EMPTY
from .DBException import DBException


def format_os(path_part):
    if not path_part:
        return None
    # On Windows, use backslash.
    if platform.system() == 'Windows':
        path_part = str(path_part).replace('/', '\\')
    return path_part


def get_home_dir():
    return '~'


def format_dir(dir_name, create=False, required=False, check_exist=False) -> str:
    # Append a directory separator if not empty and not already present.
    if not dir_name:
        return EMPTY
    if dir_name.startswith('.'):
        dir_name = f'{os.path.dirname(os.path.realpath(__file__))}{dir_name[1:]}'
    if not (dir_name.endswith('/') and not dir_name.endswith('\\')):
        dir_name += '/'
    formatted_dir = format_os(dir_name)
    return formatted_dir if not required and not check_exist and not create \
        else _validated_dir(formatted_dir, create, required, check_exist)


def _validated_dir(dir_path, create=False, required=False, check_exist=False) -> str:
    if dir_path:
        if not os.path.exists(dir_path) and create:
            os.makedirs(dir_path)
    if not dir_path or not os.path.exists(dir_path):
        if required:
            raise DBException(f'{__name__}: Invalid directory "{dir_path}"')
        else:
            return EMPTY if check_exist else dir_path
    return dir_path


def validate_path(path, required=False) -> str:
    if not path or not os.path.isfile(path):
        if required:
            raise DBException(f'{__name__}: Invalid path "{path}"')
        else:
            return EMPTY
    return path


def find_path_by_app_name(app_name, suffix=EMPTY):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    index = str.rfind(current_dir, app_name) if app_name else -1
    if index == -1:
        raise DBException(f'{__name__}: "{app_name}" was not found in current path.')
    return format_dir(f'{format_dir(current_dir[:index + len(app_name) + 1])}{suffix}')


def quote(value):
    # escape and then surround by single quotes
    return "'" + str(value).replace("'", "''") + "'"


def quote_none(value):
    # escape and then surround by single quotes
    return "'" + "'" if value is None else value


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
