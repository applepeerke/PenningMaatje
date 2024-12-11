#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-12-13 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.Base import Base
from src.GL.Enums import ResultCode
from src.GL.Result import Result


class BaseManager(Base):

    @property
    def result(self):
        return self._result

    def __init__(self):
        super().__init__()
        self._db = self._session.db
        self._result = Result()

    def _set_error(self, text):
        self._result = Result(ResultCode.Error, text)
