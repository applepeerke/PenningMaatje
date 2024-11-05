from src.DL.Model import FD
from src.VL.Models.BaseModel import BaseModel, DD
from src.GL.BusinessLayer.SessionManager import Singleton as Session


class SearchModel(BaseModel):

    @property
    def years(self):
        return self._years

    @property
    def months(self):
        return self._months

    @property
    def counter_account_numbers(self):
        return self._counter_account_numbers

    @property
    def booking_description_searchables(self):
        return self._booking_description_searchables

    @property
    def transaction_codes(self):
        return self._transaction_codes

    @property
    def image_magnifying_glass(self):
        return f'{self._get_image_path("magnifying_glass.png")}'

    @property
    def image_refresh(self):
        return f'{self._get_image_path("refresh.png")}'

    @property
    def image_export(self):
        return f'{self._get_image_path("export.png")}'

    def __init__(self):
        super().__init__()
        # Combo boxes
        self._years = self._get_combo_data(FD.Year)
        self._months = self._get_combo_data(FD.Month)
        self._transaction_codes = self._get_combo_data(FD.Transaction_code)
        self._booking_description_searchables = self._get_combo_data(FD.Booking_description_searchable)
        self._counter_account_numbers = self._get_combo_data(FD.Counter_account_number)
        self._rows = []
        self._total = 0

    @staticmethod
    def _get_combo_data(name) -> list:
        return DD.get_combo_items(name)

    @staticmethod
    def _get_image_path(image_name):
        return f'{Session().images_dir}{image_name}'
