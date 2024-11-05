#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# -----------------------------------------------------------------------------------------------------------

import os
import platform

from src.GL.Enums import LogLevel, LogType, Color, ColorWin, MessageSeverity as Sev
from ..Functions import is_valid_file
from ..GeneralException import GeneralException

EMPTY = ''
BLANK = ' '


class Singleton:
    """ Singleton """

    class LogManager:
        """Implementation of Singleton interface """

        log_level_sev = {
            LogLevel.Info: Sev.Info,
            LogLevel.Warning: Sev.Warning,
            LogLevel.Error: Sev.Error,
            LogLevel.Verbose: 0,
        }

        @property
        def log_level(self):
            return self._log_level

        @property
        def log_type(self):
            return self._log_type

        @property
        def log_file_name(self):
            return self._log_file_name

        @property
        def log_path(self):
            return self._log_path

        @property
        def is_progress_started(self):
            return self._is_progress_started

        """
        Setters
        """

        @log_level.setter
        def log_level(self, value):
            self._log_level = value

        def __init__(self):
            """
            Constructor
            """
            self._log_file_name = EMPTY
            self._log_level = LogLevel.Verbose
            self._log_type = EMPTY
            self._is_progress_started = False

            self.previous_line = EMPTY
            self.previous_lineNC = EMPTY
            self._log_path = EMPTY

            if platform.system().lower() == 'linux' \
                    or platform.system().lower() == 'osx' \
                    or platform.system().lower() == 'darwin':
                self.WindowsPlatform = False
            else:
                self.WindowsPlatform = True
            self._noColor = self._get_noColorToken()

        def get_color(self, color_name):
            if color_name == 'RED':
                if self.WindowsPlatform:
                    return ColorWin.RED
                else:
                    return Color.RED
            if color_name == 'BLUE':
                if self.WindowsPlatform:
                    return ColorWin.BLUE
                else:
                    return Color.BLUE
            if color_name == 'GREEN':
                if self.WindowsPlatform:
                    return ColorWin.GREEN
                else:
                    return Color.GREEN
            if color_name == 'ORANGE':
                if self.WindowsPlatform:
                    return ColorWin.ORANGE
                else:
                    return Color.ORANGE
            else:
                return EMPTY

        def start_log(self, log_dir, log_type=LogType.Both, level=LogLevel.Verbose, suffix=EMPTY, initialize=True):
            """
            For a simple and verbose start of the log
            """
            self._log_level = level
            self._log_type = log_type
            if not log_dir or not os.path.exists(log_dir):
                raise GeneralException(f'{__name__}: A directory is required.')
            self._log_file_name = f'Log{suffix}.txt'
            self._log_path = log_dir + self.log_file_name
            if initialize and is_valid_file(self._log_path):
                os.remove(self._log_path)

        def add_line(self, line, sev=Sev.Completion):
            """
            Log a line
            A. Forced verbose
            B. severity value <= log level value
            C. No severity and Verbose
            """
            if (sev and sev <= self.log_level_sev[self._log_level]) \
                    or (not sev and self.log_level_sev[self._log_level] >= Sev.Info):
                return

            self.stop_progressbar()  # Stop progress bar (just in case)

            # Stdout
            if self.log_type == LogType.Both or self.log_type == LogType.Stdout or self._log_type == EMPTY:
                print(line)
            # File: no colors.
            if self.log_type == LogType.Both or self.log_type == LogType.File:
                self._append_file(str(line))

        def add_coloured_line(self, line, color=None, new_line=True, sev=Sev.Completion):
            """
            Log a coloured line
            """
            if (sev and sev <= self.log_level_sev[self._log_level]) \
                    or (not sev and self.log_level_sev[self._log_level] >= Sev.Info):
                return

            lineNC = line

            if color:
                color = self.get_color(color)
                color = self._validate_color_platform(color)
                line = f'{color}{line}{self._noColor}'

            # Hold output
            if not new_line:
                self.previous_lineNC = lineNC + BLANK
                if color:
                    self.previous_line = f'{color}{line}{self._noColor}{BLANK}'
                else:
                    self.previous_line = f'{line}{BLANK}'

            # Write output
            else:
                self.stop_progressbar()  # Stop progress bar (just in case)
                # Stdout: with color (on non-windows platform).
                if self.log_type == LogType.Both or self.log_type == LogType.Stdout:
                    print(self.previous_line + line)
                # File
                if self.log_type == LogType.Both or self.log_type == LogType.File:
                    self._append_file(f'{str(self.previous_lineNC)}{str(lineNC)}')

                # Initialize previous fields
                self.previous_line = EMPTY
                self.previous_lineNC = EMPTY

        def _append_file(self, line):
            # File: no colors.
            with open(self._log_path, 'a') as txtFile:
                txtFile.write(self._colorless(line) + '\n')

        @staticmethod
        def _colorless(line):
            s = 0
            while s > -1:
                s = line.find('\033[')
                if s == -1:
                    break
                e = line.find('m', s)
                if e == -1:
                    break
                line = line.replace(line[s:e + 1], '')
            return line

        def progress(self, line=EMPTY, new_line=False, color=EMPTY):
            """
            Progress bar. Not in Verbose!
            Typically 1st time "line" contains a string, next times a progress character like "."
            """
            if line == EMPTY:
                return

            color = self._validate_color_platform(color)
            if color != EMPTY:
                line = color + line + self._get_noColorToken()

            if self.is_progress_started \
                    and not self.log_level == LogLevel.Verbose \
                    and (self.log_type == LogType.Both or
                         self.log_type == LogType.Stdout):
                if not new_line:
                    print(line, end='', flush=True)
                else:
                    print(line)

        def _validate_color_platform(self, color):
            if self.WindowsPlatform == 'Windows':
                # Jaar: Get windows coloring right. For now, no color for Windows.
                color = None
            return color

        def _get_noColorToken(self):
            if self.WindowsPlatform == 'Windows':
                return ColorWin.NC
            else:
                return Color.NC

        def start_progressbar(self, line=EMPTY, color=EMPTY):
            self._is_progress_started = True
            self.progress(line, new_line=False, color=color)

        def stop_progressbar(self):
            if self.is_progress_started:
                print(EMPTY)
            self._is_progress_started = False

        @staticmethod
        def new_line(strict=False):
            if strict:
                print('\n')
            else:
                print(EMPTY)

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.LogManager()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
