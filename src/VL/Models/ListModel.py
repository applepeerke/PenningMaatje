from src.VL.Models.BaseModel import DD
from src.VL.Models.BaseModelTable import BaseModelTable


class ListModel(BaseModelTable):
    @property
    def title(self):
        return self._title

    @property
    def pk(self):
        return self._pk

    def __init__(self, table_name, title, pk=None, key_num_rows=None):
        super().__init__(table_name, key_num_rows)
        self._pk = pk
        self._title = title
        self.set_data(DD.fetch_set(table_name, pk))
