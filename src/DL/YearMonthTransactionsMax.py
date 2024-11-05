class YearMonthTransactionsMax(object):

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def count(self):
        return self._count

    def __init__(self, year: int = 0, month: int = 0, count: int = 0):
        self._year = year
        self._month = month
        self._count = count

    def to_dict(self) -> dict:
        return {'year': self._year, 'month': self._month, 'count': self._count}
