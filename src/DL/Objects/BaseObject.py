# ---------------------------------------------------------------------------------------------------------------------
# Base.py
#
# Author      : Peter Heijligers
# Description : Base model
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-02 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Model import Model
from src.DL.Table import Table

PGM = 'BaseObject'


class BaseObject(object):

    @property
    def attributes(self):
        return self._attributes

    def __init__(self, table_name: Table):
        self._model = Model()
        self._table_name = table_name
        self._attributes = {}
        self._set_attributes()

    def to_db_row(self):
        return self._model.to_db_row(self._table_name, self._attributes)

    def _set_attributes(self):
        """ Convert object values to Attributes """
        raise NotImplementedError(
            f'{PGM}: Method "set_attributes" has not been implemented for table {self._table_name}.')

    def _set_attribute_value(self, name, value):
        """ When setting the Att value, also conversion is done to user representation, e.g. float to amount """
        self._attributes[name].value = value
