from src.GL.Const import EMPTY


class TemplateField:
    @property
    def template_var_name(self):
        return self._template_var_name

    @property
    def model_var_name(self):
        return self._model_var_name

    @property
    def column_no(self):
        return self._column_no

    @property
    def value(self):
        return self._value

    @property
    def value_prv(self):
        return self._value_prv

    @property
    def same_value_count(self):
        return self._same_value_count

    """
    Setters
    """
    @value.setter
    def value(self, value):
        self._value = value

    @model_var_name.setter
    def model_var_name(self, value):
        self._model_var_name = value

    @value_prv.setter
    def value_prv(self, value):
        self._value_prv = value

    @same_value_count.setter
    def same_value_count(self, value):
        self._same_value_count = value

    def __init__(self, name, value=None, column: int = 0):
        self._template_var_name = name
        self._model_var_name = EMPTY
        self._value = value
        self._column_no = column
        # context
        self._value_prv = EMPTY
        self._same_value_count = 0
