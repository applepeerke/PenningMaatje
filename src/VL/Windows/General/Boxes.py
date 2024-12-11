import PySimpleGUI as sg

from src.Base import Base

class Boxes(Base):
    def __init__(self):
        super().__init__()


    def info_box(self, text, title='Info'):
        sg.PopupOK(f'\n{text}\n', title=title, grab_anywhere=True, keep_on_top=True, icon=self._session.get_icon(),
                   font=self._CM.get_font())


    def confirm_factory_reset(self, text, title='Onbekende fout') -> bool:
        answer = sg.PopupOKCancel(f'\n{text}\n', title=title, keep_on_top=True, font=self._CM.get_font())
        return True if answer == 'OK' else False
