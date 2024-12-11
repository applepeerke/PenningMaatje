from src.DL.Config import CF_ROWS_MONTH
from src.DL.Table import Table
from src.VL.Models.BaseModelTable import BaseModelTable


class Months(BaseModelTable):

    def __init__(self):
        super().__init__(Table.Month)
        self._num_rows = int(self._CM.get_config_item(CF_ROWS_MONTH, 2))
