from src.BL.Functions import get_fonts
from src.VL.Models.BaseModel import BaseModel


class LayoutOptionsModel(BaseModel):

    @property
    def fonts(self):
        return self._fonts

    def __init__(self):
        self._fonts = get_fonts()
