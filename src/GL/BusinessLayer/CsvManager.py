# ---------------------------------------------------------------------------------------------------------------------
# DataManager.py
#
# Author      : Peter Heijligers
# Description : Manage csv table data
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2017-09-04 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

import csv

from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import DELIMITER, DELIMITER_ALT, BLANK, TEXT_SEPARATOR
from src.GL.Functions import is_valid_file
from src.GL.GeneralException import GeneralException

EMPTY = ''
PGM = 'CsvManager'
apostrophes = ["'", '"']


class CsvManager(object):
    """
    Manage business data in .csv files
    """

    def __init__(self):
        self._file_name = EMPTY
        self._data_path = EMPTY
        self._error_message = None
        self._delimiter = None

    @property
    def error_message(self):
        return self._error_message

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        self._file_name = value

    @property
    def delimiter(self):
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value):
        self._delimiter = value

    def get_first_row(self, data_path=None, delimiter=None) -> list:
        """
        Return first matched table row
        """

        if not is_valid_file(data_path):
            return []

        if not self._delimiter or delimiter:
            self._set_delimiter(data_path, delimiter)

        row = self._try_first_row(data_path, first=True)
        if len(row) == 1:
            self._set_delimiter(data_path)
            row = self._try_first_row(data_path)
        return row

    def _try_first_row(self, data_path, first=False) -> list:
        try:
            result = []
            with open(data_path, encoding='utf-8-sig', errors='replace') as csvFile:
                data_reader = csv.reader(
                    csvFile, delimiter=self._delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in data_reader:
                    result = row
                    break
            return result
        except (IOError, IndexError, csv.Error) as e:
            if first:
                return [BLANK]   # Simulate row length=1
            raise GeneralException(f'{PGM}.try_header: Error in "{data_path}": {e}')

    def get_rows(self, include_header_row=False,
                 where=None,
                 data_path=None,
                 include_empty_row=False,
                 delimiter=None,
                 max=None,
                 check_delimiter=False):
        """
        Read rows from disk
        :return: list
        """
        method = 'get_rows'
        rows = []

        if not is_valid_file(data_path):
            return []

        if not self._delimiter or delimiter or check_delimiter:
            self._set_delimiter(data_path, delimiter)

        try:
            trial = 0
            while trial < 2:
                trial += 1
                with open(data_path, encoding='utf-8-sig',  errors='replace') as csvFile:
                    csv_reader = csv.reader(
                        csvFile, delimiter=self._delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL,
                        skipinitialspace=True)
                    rows, index = self.process_file(
                        csv_reader, include_header_row, include_empty_row, max, trial)
                    if rows:  # OK
                        break

                    if index == -1:  # Retry
                        self._set_delimiter(data_path)
                        continue

                    if rows and index > 0:
                        raise GeneralException(
                            f'{PGM}.{method}: csv error in row {str(index + 1)} of "{data_path}".')

        except (IOError, csv.Error) as e:
            raise GeneralException(f'{PGM}.{method}: {e}')

        # Where
        if where:
            rows = self._filtered_rows(rows, where)
        return rows

    @staticmethod
    def _filtered_rows(rows, where: dict):
        out_rows = []
        for row in rows:
            for key, value in where.items():
                if not value or row[key].lower() == value.lower():
                    out_rows.append(row)
        return out_rows

    def process_file(self, csv_reader, include_header_row, include_empty_row, max, trial) -> (list, int):
        rows = []
        index = 0
        sanitize = False
        try:
            for row in csv_reader:
                if index == 0 and len(row) == 1 and self._delimiter in row[0]:
                    sanitize = True
                if sanitize:
                    row = self._sanitize_csv_row(row[0], self._delimiter)
                # Optionally toggle delimiter
                if index == 0 and len(row) == 1 and trial == 1:
                    self._delimiter = DELIMITER_ALT if self._delimiter == DELIMITER else DELIMITER
                    return [], -1

                if include_header_row or index > 0:
                    valid = True
                    # Optionally skip empty rows
                    if include_empty_row:
                        if not row:
                            row = [EMPTY]
                    else:
                        valid = False
                        for cell in row:
                            if cell is not EMPTY:
                                valid = True
                                break
                    if valid:
                        rows.append(row)
                if max and len(rows) == max:
                    break
                index += 1
            return rows, index
        except IndexError:
            return [], index

    def get_unique_column(self, data_path, column_name) -> set:
        rows = self.get_rows(data_path=data_path, include_header_row=True, check_delimiter=True)
        header = rows[0]
        index = -1
        for i in range(len(header)):
            if header[i].lower() == column_name.lower():
                index = i
                break
        return {row[index] for row in rows[1:]} if index > -1 else set()

    def write_rows(self, rows, col_names=None, open_mode='a', data_path=None, delimiter=';', include_id=True) -> bool:
        if not rows:
            return False
        if data_path is None:
            data_path = Session().resource_dir + self._file_name

        try:
            # rows = self._sanitize_delimiter(rows)
            first = True
            with open(data_path, open_mode) as csvFile:
                csv_writer = csv.writer(
                    csvFile, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                for row in rows:
                    if col_names is not None and first:
                        first = False
                        header = ['Id'] if include_id else []
                        header.extend(col_names)
                        csv_writer.writerow(header)
                    if row:  # row might be None
                        csv_writer.writerow(row)
            return True
        except csv.Error as e:
            raise GeneralException(f'{PGM}.write_rows: {e}')

    @staticmethod
    def _sanitize_delimiter(rows):
        # Check
        if len(rows) == 0 or len(rows[0]) > 1:
            return rows
        # Toggle delimiter
        delimiter = DELIMITER if DELIMITER in rows[0] else DELIMITER_ALT
        out_rows = [row.split(delimiter) for row in rows]
        for row in out_rows:
            if len(row) != len(out_rows[0]):
                return rows
        return out_rows

    def _set_delimiter(self, data_path, delimiter=None):
        """ For this file, figure out and set the delimiter to "," or ";"  """
        if delimiter:
            self._delimiter = delimiter
            return

        delimiter = DELIMITER
        delimiter_alt = DELIMITER_ALT
        if self._try_delimiter(data_path, delimiter):
            self._delimiter = delimiter
        elif self._try_delimiter(data_path, delimiter_alt):
            self._delimiter = delimiter_alt

        if not self._delimiter:
            raise GeneralException(f'{PGM}.set_delimiter: Delimiter could not be set')

    @staticmethod
    def _try_delimiter(data_path, delimiter) -> bool:
        """ If first row contains 1 field containing the alternate delimiter, toggle the delimiter. """
        try:
            with open(data_path, encoding='utf-8-sig', errors='replace') as csvFile:
                csv_reader = csv.reader(csvFile, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in csv_reader:
                    return False if len(row) == 1 and (
                            (DELIMITER in row[0] and DELIMITER != delimiter) or
                            (DELIMITER_ALT in row[0] and DELIMITER_ALT != delimiter)) \
                        else True
        except (IOError, IndexError, csv.Error):
            return False

    @staticmethod
    def _sanitize_csv_row(inp_row, delimiter=DELIMITER, text_separator=TEXT_SEPARATOR, ) -> list:
        """ Escape delimiters in text and then remove apostrophes """
        replace_by = \
            DELIMITER_ALT if delimiter == DELIMITER else DELIMITER if delimiter == DELIMITER_ALT else delimiter

        # Step 1: Replace delimiters (',') occurring within text by the alt (';')
        inside = False
        out_row = ''
        i = 0
        while i < len(inp_row):
            if inp_row[i] == text_separator:
                inside = False if inside else True
            if inside and inp_row[i] == delimiter:
                out_row += replace_by
            else:
                out_row += inp_row[i]
            i += 1

        # Step 2: Split the 1-cell row into a list of cells
        row = out_row.split(delimiter)

        # Step 3: Remove apostrophes from the cells, and replace the alt (';') by the delimiter (',')
        # Example: ['2023-05-01', "-88;71", ...] will become ['2023-05-01', '-88,71', ...]
        i = 0
        for value in row:
            for j in apostrophes:
                row[i] = value.replace(j, EMPTY).replace(replace_by, delimiter)
            i += 1
        return row
