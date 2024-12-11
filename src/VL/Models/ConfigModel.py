from src.VL.Models.BaseModel import BaseModel
from src.VL.Models.BaseModelTable import BaseModelTable


class ConfigModel(BaseModel):

    @property
    def account_model(self):
        return self._account_model

    @property
    def do_import(self):
        return self._do_import

    @property
    def do_factory_reset(self):
        return self._do_factory_reset

    """
    Setters
    """

    @do_import.setter
    def do_import(self, value):
        self._do_import = value

    @do_factory_reset.setter
    def do_factory_reset(self, value):
        self._do_factory_reset = value

    def __init__(self, account_model: BaseModelTable):
        super().__init__()
        self._do_import = False
        self._do_factory_reset = False
        self._account_model = account_model
