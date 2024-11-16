from src.DL.Table import Table
from src.VL.Models.BaseModelTable import BaseModelTable


class Accounts(BaseModelTable):

    def __init__(self):
        super().__init__(Table.Account)
        self._max_col_width = 132
