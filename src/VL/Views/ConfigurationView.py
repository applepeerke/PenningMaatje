from src.VL.Data.Constants.Enums import Pane
from src.VL.Views.BaseView import BaseView


class ConfigurationView(BaseView):

    def get_view(self) -> list:
        pass

    def __init__(self):
        super().__init__(pane_name=Pane.CF)
