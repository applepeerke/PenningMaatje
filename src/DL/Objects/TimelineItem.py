from src.GL.Functions import toFloat


class TimelineItem(object):

    @property
    def x_label(self):
        return self._x_label

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def amount(self):
        return self._amount
    """
    Setters
    """
    @amount.setter
    def amount(self, value: dict):
        self._amount = value

    def __init__(self, year, month=0, amount=0):
        self._year = year
        self._month = month
        self._amount = toFloat(amount)
        self._x_label = self._month if month > 0 else self._year
