# ---------------------------------------------------------------------------------------------------------------------
# TransactieFile.py
#
# Author      : Peter Heijligers
# Description : Transactie file
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-10 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import ntpath

from src.GL.Functions import is_valid_file
from src.GL.Validate import normalize_dir


class TransactionFile(object):

    @property
    def path(self):
        return self._path

    @property
    def delimiter(self):
        return self._delimiter

    @property
    def colno_mapping(self):
        return self._colno_mapping

    @property
    def error_message(self):
        return self._error_message

    @property
    def dir_name(self):
        return self._dir_name

    @property
    def file_name(self):
        return self._file_name

    @property
    def key(self):
        return self._key

    @error_message.setter
    def error_message(self, value):
        self._error_message = value

    def __init__(self, path: str, colno_mapping: dict, delimiter=','):
        self._colno_mapping = colno_mapping
        self._delimiter = delimiter
        self._dir_name = None
        self._file_name = None
        self._path = path
        self._error_message = None
        self._key = None
        self._set_attrs()

    def _set_attrs(self):
        if not is_valid_file(self._path):
            self._error_message = f'{__name__}: Path "{self._path}" is invalid.'
        else:
            # Split Dir and File
            d, self._file_name = ntpath.split(self._path)
            self._dir_name = normalize_dir(d)

            if self._file_name:
                p = self._file_name.find('_')  # Start of date_from
                if p > -1:
                    self._key = self._file_name[p:].strip()
