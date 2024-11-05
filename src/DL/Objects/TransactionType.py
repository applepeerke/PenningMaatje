class TransactionType(object):

    @property
    def bank_name(self):
        return self._bank_name

    @property
    def transaction_code(self):
        return self._transaction_code

    @property
    def transaction_type(self):
        return self._transaction_type

    def __init__(self, bank_name, transaction_code,  transaction_type):
        self._bank_name = bank_name
        self._transaction_code = transaction_code
        self._transaction_type = transaction_type
