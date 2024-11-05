import PySimpleGUI as sg

from src.DL.Objects.Window import Window
from src.VL.Functions import get_name_from_key, get_name_from_text
from src.VL.Views.BaseView import BaseView


class SelectBox(BaseView):

    def get_view(self) -> list:
        pass

    def __init__(self, relative_location=None):
        super().__init__()
        if relative_location:
            self._relative_location = relative_location
        self._trial_count = 0

    def get_input(self, key, items, dft=None, title='Selecteer') -> str:
        return self._process_box(key, items, dft, title)

    def _process_box(self, key, items, dft, title) -> str:
        layout = self._get_window(key, items, dft)
        window = Window(title, layout, relative_location=self._relative_location).instance()

        while True:
            event, values = window.read()
            event_key = get_name_from_key(event)
            input_value = None

            if event == sg.WIN_CLOSED:
                break

            # - Select
            elif event_key == get_name_from_text(key):
                input_value = values.get(event)
                self.set_setting(event_key, input_value)
                if input_value:
                    break

        window.close()
        # Reset location
        self._relative_location = None
        return input_value

    def _get_window(self, key, items, dft=None) -> list:
        x = len(self._get_label(key))
        lists = [self.frame('input', [self.combo(key, items=items, dft=dft, x=x, evt=True)])]
        return [self.frame('SelectionBox', lists, p=0)]
