from src.VL.Data.Constants.Enums import BoxCommand
from src.VL.Models.BaseModel import BaseModel


class ListItemModel(BaseModel):

    @property
    def object(self):
        return self._object

    @property
    def object_old(self):
        return self._object_old

    @property
    def command(self):
        return self._command

    @object.setter
    def object(self, value):
        self._object = value

    def __init__(self, table_name, command: BoxCommand, obj=None):
        super().__init__()
        self._table_name = table_name
        self._command = command
        self._object = obj
        self._object_old = obj
