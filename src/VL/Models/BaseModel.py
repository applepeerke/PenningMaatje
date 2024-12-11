#!/usr/bin/env python3
from src.Base import Base
from src.DL.Model import Model
from src.VL.Data.DataDriver import Singleton as DataDriver

DD = DataDriver()
model = Model()


class BaseModel(Base):
    @property
    def DD(self):
        return DD
