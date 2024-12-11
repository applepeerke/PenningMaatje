#!/usr/bin/env python3
from collections import OrderedDict

from src.DL.Config import CF_COMMA_REPRESENTATION_DB
from src.DL.DBDriver.AttType import AttType
from src.VL.Data.Constants.Const import BOOL_TEXT_TRUE, BOOL_TEXT_FALSE
from src.VL.Functions import get_col_widths
from src.VL.Models.BaseModel import BaseModel, model
from src.GL.Functions import FloatToStr
from src.GL.Validate import toBool


class BaseModelTable(BaseModel):
    @property
    def table_name(self):
        return self._table_name

    @property
    def max_col_width(self):
        return self._max_col_width

    @property
    def num_rows(self):
        return self._num_rows

    @property
    def col_def(self):
        return self._col_def

    @property
    def table_height(self):
        return len(self._rows)

    @property
    def rows(self):
        return self._rows

    @property
    def header(self):
        return self._header

    @property
    def visible_column_map(self):
        return self._visible_column_map

    @property
    def col_widths(self):
        return self._col_widths

    def __init__(self, table_name, key_num_rows=None):
        super().__init__()
        self._table_name = table_name
        self._num_rows = int(self._CM.get_config_item(key_num_rows)) if key_num_rows else 50
        self._max_col_width = 60
        self._col_widths_def = {}
        self._visible_column_map = []
        self._rows = []
        self._header = []
        self._col_widths = []
        # - Model col_def is without Id, but DB rows processed have an Id.
        self._col_def = model.get_model_definition(self._table_name)

    def _initialize_table(self):
        self._col_widths_def = OrderedDict({i: att.col_width for i, att in self._col_def.items()})
        self._col_widths_def[0] = 0  # Add Id
        # - Hide "Id" and optional other attributes.
        self._visible_column_map = [False]  # Do not display Id
        self._visible_column_map.extend([self._CM.is_attribute_visible(att) for att in self._col_def.values()])

    def set_data(self, data) -> int:
        """
        data: header with details
        col_widths: {No : col_width } or None. Default col_width=0. No. is 0-based.
        """
        if not data:  # No data
            return 0

        self._initialize_table()

        # Header
        self._header = data[0]

        if len(data) < 2:
            return 0

        self._rows = data[1:]  # Skip header

        # - Format the row cells.
        #   Rows also contain "Id" and "audit data". Format only model attributes.
        for r in self._rows:
            for i in range(1, len(self._col_def) + 1):  # Skip Id
                r[i] = self._format_cell(i, str(r[i]))

        # - After formatting (like justify!) the width is dynamically calculated.
        font_size = self._CM.get_font()[1]
        self._col_widths = list(
            get_col_widths(self._rows, self._col_widths_def, self._max_col_width, font_size).values())

        return len(self._rows)

    def _format_cell(self, col_no, att_value) -> str:
        att_def = self._col_def[col_no]  # Convert to string
        if att_def.type == AttType.Float:
            return FloatToStr(
                str(att_value), comma_source=self._CM.config_dict[CF_COMMA_REPRESENTATION_DB], justify='R')
        elif att_def.type == AttType.Bool:
            return BOOL_TEXT_TRUE if toBool(att_value) is True else BOOL_TEXT_FALSE
        return att_value

