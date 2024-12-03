import PySimpleGUI as sg

from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session

CM = ConfigManager()


def info_box(text, title='Info'):
    sg.PopupOK(f'\n{text}\n', title=title, grab_anywhere=True, keep_on_top=True, icon=Session().get_icon(),
               font=CM.get_font())


def confirm_factory_reset(text, title='Onbekende fout') -> bool:
    answer = sg.PopupOKCancel(f'\n{text}\n', title=title, keep_on_top=True, font=CM.get_font())
    return True if answer == 'OK' else False
