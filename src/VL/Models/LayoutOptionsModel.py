from src.BL.Functions import get_fonts
from src.VL.Models.BaseModel import BaseModel


class LayoutOptionsModel(BaseModel):

    @property
    def fonts(self):
        return self._fonts

    @property
    def image_magnifying_glass(self):
        return f'{self._session.images_dir}magnifying_glass.png'

    def __init__(self):
        super().__init__()
        self._fonts = get_fonts()
