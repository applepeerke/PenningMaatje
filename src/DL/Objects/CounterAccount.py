from src.GL.Const import EMPTY


class CounterAccount(object):

    @property
    def counter_account_number(self):
        return self._counter_account_number

    @property
    def name(self):
        return self._account_name

    @property
    def first_comment(self):
        return self._first_comment

    def __init__(self, counter_account_number, account_name, first_comment=EMPTY):
        self._counter_account_number = counter_account_number
        self._account_name = account_name
        self._first_comment = first_comment
