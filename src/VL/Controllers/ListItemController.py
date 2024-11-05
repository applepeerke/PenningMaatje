#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2022-06-06 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from typing import Callable

from src.DL.Model import EMPTY
from src.VL.Controllers.BaseController import BaseController
from src.VL.Data.Constants.Const import CMD_OK
from src.VL.Data.Constants.Enums import BoxCommand
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Enums import ActionCode, ResultCode
from src.GL.Result import Result


class ListItemController(BaseController):

    def __init__(self, obj_name, model, table_name, io: Callable, required: list, pk: list):
        super().__init__()
        self._obj_name = obj_name
        self._table_name = table_name
        self._model = model
        self._io = io()
        self._rqd_atts = required
        self._pk = pk

        self._CM = ConfigManager()

    def handle_event(self, event):
        super().handle_event(event)
        # After Cancel: Close item window redisplay list.
        if self._result.CN:
            self._result = Result(action_code=ActionCode.Close)
            return
        if not self._result.OK:
            return

        # - OK
        if self._event_key == CMD_OK:
            self._set_object_from_config()
            self.edit()
            if self._result.OK:
                self._result = Result(action_code=ActionCode.Close)

    def _set_object_from_config(self):
        pass

    def edit(self):
        self._result = Result()
        self._validate(self._model.command)
        if self._result.OK:
            self._result = self._io.edit(self._model)

    def _validate(self, command):
        self._result = Result()
        # Required attributes specified?
        if (command in (BoxCommand.Add, BoxCommand.Update)
                and not all(self._isSpecifiedInAtt(
                    self._model.object.attributes.get(att.name, att)) for att in self._rqd_atts)):
            return
        # Check existence in database
        if command in (BoxCommand.Add, BoxCommand.Rename):
            self._should_exist(pk_should_exist=False)
        elif command == BoxCommand.Update:
            self._should_exist(pk_should_exist=True, lk_should_exist=True)
        elif command == BoxCommand.Delete:
            self._should_exist(pk_should_exist=True)

    def _should_exist(self, pk_should_exist, lk_should_exist=False):
        new_pk = [self._model.object.attributes.get(att.name, att.value) for att in self._pk]
        Id = self._session.db.fetch_id(self._table_name, where=new_pk)
        self._text = EMPTY
        pk_text = ','.join([f'"{att.name}={att.value}"' for att in new_pk])
        if pk_should_exist is True and Id == 0:  # Update/Delete
            self._result = Result(ResultCode.Error, f'{self._obj_name} met {pk_text} bestaat niet.')
        elif pk_should_exist is False and Id > 0:  # Add/Rename
            self._result = Result(ResultCode.Error, f'{self._obj_name} met {pk_text} bestaat al.')

        # Should full logical key exist? (Update)
        if self._result.OK and lk_should_exist:
            self._lk_exists()

    def _lk_exists(self):
        """ All attributes that exist in db """
        Id = self._session.db.fetch_id(
            self._table_name, where=[att for att in self._model.object.attributes.values() if att.in_db is True])
        if Id > 0:
            self._result = Result(ResultCode.Warning, 'Er is niets gewijzigd. De gegevens bestaan al.')
