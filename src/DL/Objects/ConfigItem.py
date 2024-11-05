class ConfigItem(object):

    @property
    def label(self):
        return self._label

    @property
    def value(self):
        return self._value

    @property
    def tooltip(self):
        return self._tooltip

    @property
    def validation_method(self):
        return self._validation_method

    """
    Setters
    """
    @value.setter
    def value(self, value):
        self._value = value

    def __init__(self, label=None, value=None, tooltip=None, validation_method=None):
        self._label = label
        self._value = value
        self._validation_method = validation_method
        self._tooltip = tooltip
