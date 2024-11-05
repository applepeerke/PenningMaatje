#!/usr/bin/env python3

from src.DL.Model import Model
from src.VL.Data.DataDriver import Singleton as DataDriver
from src.GL.BusinessLayer.ConfigManager import ConfigManager

CM = ConfigManager()
DD = DataDriver()
model = Model()


class BaseModel:
    @property
    def DD(self):
        return DD

