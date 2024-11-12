from src.DL.Config import CF_COMMA_REPRESENTATION_DB, CF_COMMA_REPRESENTATION_DISPLAY, CF_REMARKS
from src.DL.Model import FD
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as AccountCache
from src.VL.Models.BaseModel import model, CM, DD
from src.VL.Models.BaseModelTable import BaseModelTable
from src.GL.Const import EMPTY, BLANK
from src.GL.Functions import FloatToStr

TE_dict = model.get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)  # Skip Id
BCM = BookingCache()
ACM = AccountCache()
TABLE = Table.TransactionEnriched


class TransactionModel(BaseModelTable):

    @property
    def account_number(self):
        return self._account_number

    @property
    def date(self):
        return self._date

    @property
    def booking_description(self):
        return self._booking_description

    @property
    def booking_descriptions(self):
        return self._booking_descriptions

    @property
    def counter_account(self):
        return self._counter_account

    @property
    def name(self):
        return self._name

    @property
    def mutation_type(self):
        return self._mutation_type

    @property
    def transaction_code(self):
        return self._transaction_code

    @property
    def amount(self):
        return self._amount

    @property
    def amount_signed(self):
        return self._amount_signed

    @property
    def transaction_date(self):
        return self._transaction_date

    @property
    def transaction_time(self):
        return self._transaction_time

    @property
    def comments(self):
        return self._comments

    @property
    def remarks(self):
        return self._remarks

    def __init__(self):
        super().__init__(Table.TransactionEnriched)
        self._account_number = EMPTY
        self._date = EMPTY
        self._name = EMPTY
        self._amount = EMPTY
        self._amount_signed = 0.00
        self._booking_description = EMPTY
        self._booking_descriptions = []
        self._comments = EMPTY
        self._counter_account = EMPTY
        self._mutation_type = EMPTY
        self._transaction_code = EMPTY
        self._transaction_date = EMPTY
        self._transaction_time = EMPTY
        self._remarks = EMPTY
        self._comma_db = CM.config_dict.get(CF_COMMA_REPRESENTATION_DB, '.')
        self._display = CM.config_dict.get(CF_COMMA_REPRESENTATION_DISPLAY, ',')

    def set_data(self, row):
        if not row:
            return

        self._account_number = row[TE_dict[FD.Account_bban]]
        self._date = row[TE_dict[FD.Date]]
        self._name = row[TE_dict[FD.Name]]
        self._amount_signed = row[TE_dict[FD.Amount]]

        # Set sign and refill combo
        if row[TE_dict[FD.Add_Sub]] == 'Af':
            self._amount_signed *= -1
        self._booking_descriptions = DD.set_get_combo_items(FD.Booking_code)

        self._amount = FloatToStr(
            str(self._amount_signed), comma_source=self._comma_db, comma_target=self._display, justify='R')
        self._booking_description = BCM.get_value_from_id(row[TE_dict[FD.Booking_id]], FD.Booking_description)

        self._comments = self.format_mededelingen(row[TE_dict[FD.Comments]])
        self._counter_account = ACM.get_iban_from_id(row[TE_dict[FD.Counter_account_id]])
        self._mutation_type = row[TE_dict[FD.Transaction_type]]
        self._transaction_code = row[TE_dict[FD.Transaction_code]]
        self._transaction_date = row[TE_dict[FD.Transaction_date]]
        self._transaction_time = row[TE_dict[FD.Transaction_time]]
        self._remarks = row[TE_dict[FD.Remarks]]

    def update_from_config(self):
        self._remarks = CM.get_config_item(CF_REMARKS)

    @staticmethod
    def format_mededelingen(mededelingen) -> str:
        """ E.g. "Naam: Pietje Puk Datum: 2022-01-01" """
        result, key, key_prv, new_line = EMPTY, EMPTY, EMPTY, EMPTY
        s, s_key, s_value_prv = 0, 0, 0
        while True:
            # Next item
            p = mededelingen.find(': ', s)
            if p == -1:
                if key_prv:  # Last time
                    result = f'{result}{new_line}{key}: {mededelingen[s_value_prv:]}'
                break
            s = p + 1
            # Store key and add previous "key: value"
            s_key = mededelingen.rfind(BLANK, 0, p)
            if s_key == -1:
                key = mededelingen[:p]  # E.g. "Naam"
            else:
                key_prv = key  # E.g. "Naam"
                key = mededelingen[s_key+1:p]  # E.g. "Datum"
                result = f'{result}{new_line}{key_prv}: {mededelingen[s_value_prv:s_key]}'  # E.g. "Naam: Pietje Puk"
                new_line = '\n'
            s_value_prv = p + 2  # Skip  ": "
        # Check:
        if result.replace('\n', BLANK) != mededelingen:
            return mededelingen
        return result
