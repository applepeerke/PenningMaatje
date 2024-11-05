from src.DL.Config import CF_ROWS_YEAR
from src.DL.Table import Table
from src.VL.Models.BaseModelTable import BaseModelTable, CM


class Years(BaseModelTable):

    def __init__(self):
        super().__init__(Table.Year)
        self._num_rows = int(CM.get_config_item(CF_ROWS_YEAR, 2))
