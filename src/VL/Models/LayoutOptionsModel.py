from src.BL.Functions import get_fonts
from src.VL.Models.BaseModel import BaseModel
from src.GL.BusinessLayer.SessionManager import Singleton as Session


class LayoutOptionsModel(BaseModel):

    @property
    def fonts(self):
        return self._fonts

    @property
    def image_magnifying_glass(self):
        return f'{self._session.images_dir}magnifying_glass.png'

    def __init__(self):
        self._fonts = get_fonts()
        self._session = Session()
