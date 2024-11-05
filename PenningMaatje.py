#!/usr/bin/env python3
import ctypes
import os
import platform

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))


def format_os(path_part):
    # On Windows, use backslash.
    if platform.system() == 'Windows':
        path_part = str(path_part).replace('/', '\\')
    else:
        path_part = str(path_part).replace('\\', '/')
    return path_part


def slash():
    return format_os('/')


def get_app_root_dir() -> str:
    """ Should be the same level as src folder (so not in "src") """
    return f'{ROOT_DIR}{slash()}'


def get_root_dir() -> str:
    """ Should be the same level as App folder """
    return ROOT_DIR.rstrip(os.path.basename(ROOT_DIR))


def make_dpi_aware():
    if not platform.system() == 'Windows' or not platform.release():
        return
    release_out = ''
    for c in platform.release():
        if not c.isdigit():
            break
        release_out = f'{release_out}{c}'

    if int(release_out) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)


if __name__ == '__main__':
    from src.PenningMaatje import start
    make_dpi_aware()
    start()
