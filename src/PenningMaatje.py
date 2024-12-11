#!/usr/bin/env python3
from tkinter import TclError

from src.VL.Windows.General.MessageBox import MessageBox
from src.VL.Windows.MainWindow import MainWindow
from src.GL.Const import APP_NAME
from src.GL.Enums import MessageSeverity, Color
from src.GL.GeneralException import GeneralException


def start(diagnostic_mode=False):
    diagnostic_mode = diagnostic_mode
    while True:  # Restart loop
        W = MainWindow(diagnostic_mode=diagnostic_mode)
        try:
            W.display()
            if not W.result.RT:  # Normal end
                break
        # Exception handling
        except (GeneralException, Exception) as e:
            if W and W.result and W.result.OK and e and type(e) is TclError and 'toplevel' in str(e):
                break   # Hoofdscherm is gesloten voor detail scherm.
            if diagnostic_mode is True:
                print(f'{Color.RED}Fout opgetreden in diagnostische mode:{Color.NC} {e}\n'
                      f'App wordt beëindigd.')
                break
            try:
                answer = error_message_box(
                    f'\n\nEr is iets fout gegaan, de app zal worden beëindigd.\n\n'
                    f'De Melding is: "{e}".\n\n'
                    f'{APP_NAME} resetten en herstarten in diagnostische mode?\n')
                if not answer:
                    break
                diagnostic_mode = True
            except Exception as e:
                print(f'{Color.RED}Diagnostische mode kon niet gestart worden.{Color.NC}\n'
                      f'Oorzaak: {e}\n'
                      f'App wordt beëindigd.')
                break


def error_message_box(text, cont_text=False) -> bool:
    return MessageBox().message_box(text, title='Fout opgetreden', cont_text=cont_text, severity=MessageSeverity.Error)
