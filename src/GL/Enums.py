#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Lexicon import RED, GREEN, ORANGE, BLUE, PURPLE, BROWN, PINK, GREY, OLIVE, CYAN
from src.GL.Const import EMPTY, BLANK


class Color(object):
    RED = '\033[31m'
    GREEN = '\033[32m'
    ORANGE = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    NC = '\033[0m'


# W10 does not seem to support ANSI cmd colors
class ColorWin(object):
    RED = ''
    GREEN = ''
    ORANGE = ''
    BLUE = ''
    PURPLE = ''
    NC = ''


# Matplotlib tableau colors
class ColorTableau(object):
    Red = 'tab:red'
    Green = 'tab:green'
    Orange = 'tab:orange'
    Blue = 'tab:blue'
    Purple = 'tab:purple'
    Brown = 'tab:brown'
    Pink = 'tab:pink'
    Grey = 'tab:grey'
    Olive = 'tab:olive'
    Cyan = 'tab:cyan'

    names = [Red, Orange, Purple, Pink, Blue, Cyan, Olive, Green, Brown, Grey]
    mapping = {EMPTY: None, RED: Red, GREEN: Green, ORANGE: Orange, BLUE: Blue, PURPLE: Purple, BROWN: Brown,
               PINK: Pink, GREY: Grey, OLIVE: Olive, CYAN: Cyan}


class LogType(object):
    File = 'File'
    Stdout = 'Stdout'
    Both = 'Both'


class LogLevel(object):
    Error = 'Fout'
    Warning = 'Waarschuwing'
    Info = 'Informatief'
    Verbose = 'Uitvoerig'
    All = 'All'

    values = [Error, Warning, Info, Verbose]


class ResultCode(object):
    Ok = 'OK'
    Error = 'ER'
    Warning = 'WA'
    NotFound = 'NR'
    Equal = 'EQ'
    Canceled = 'CN'
    Exit = 'EX'


class ActionCode(object):
    Cancel = 'CN'
    Retry = 'RT'
    Go = 'GO'
    Close = 'CL'


class Appearance(object):
    Label = 'Label'
    OptionBox = 'OptionBox'
    CheckBox = 'CheckBox'
    RadioButton = 'RadioButton'
    Entry = 'Entry'
    TextArea = 'TextArea'


class Mutation:
    Create = 'C'
    Read = 'R'
    Update = 'U'
    Delete = 'D'


class MessageSeverity:
    Info = 10
    Warning = 20
    Error = 30
    Completion = 40

    @staticmethod
    def get_title(severity=0, text=EMPTY):
        if text:
            return text
        if severity == 10:
            return 'Info'
        elif severity == 20:
            return 'Waarschuwing'
        elif severity == 30:
            return 'Fout opgetreden'
        elif severity == 40:
            return 'Compleet melding'
        return BLANK
