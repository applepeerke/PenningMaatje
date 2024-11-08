from src.BL.Functions import get_BBAN_from_IBAN, sophisticate_account_number
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.Enums import FetchMode
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD, Model
from src.DL.Objects.Account import Account
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.GL.GeneralException import GeneralException

PGM = 'AccountIO'
TABLE = Table.Account
d = Model().get_colno_per_att_name(TABLE, zero_based=False)


class AccountsIO(BaseIO):

    @property
    def objects(self):
        return self._objects

    def __init__(self):
        super().__init__(TABLE)
        self._accounts_dict = {}

    def insert(self, obj: Account):
        """ Avoid duplicates """
        where = [Att(FD.Bban, obj.bban)]
        self._insert(obj, where, pgm=PGM)

    def add_account_to_cache(self, value):
        if not value:
            return
        bban, iban = self.get_bban_iban_from_account_number(value)
        if bban and iban:
            self._accounts_dict[bban] = iban

    def persist_accounts(self):
        [self.insert(Account(bban, iban)) for bban, iban in self._accounts_dict.items()]

    def get_current_iban(self, current_iban) -> str:
        iban = current_iban
        self._accounts_dict = {o.bban: o.iban for o in self._get_objects()}

        # If iban in config does not exist in the new iban list, return the first one (or empty)
        if not any(iban == current_iban for iban in self._accounts_dict.values()):
            iban = list(self._accounts_dict.values())[0] if self._accounts_dict else EMPTY
        return iban

    def _get_objects(self) -> list:
        rows = self._session.db.select(TABLE, mode=FetchMode.WholeTable)
        self._objects = [self._row_to_obj(row) for row in rows]
        return self._objects

    def get_ibans(self) -> list:
        return self._session.db.select(TABLE, name=FD.Iban)

    def get_bban_iban_from_account_number(self, value) -> (str, str):
        account_number = sophisticate_account_number(value)
        if not account_number:
            return EMPTY
        # Convert account number to bban
        bban = account_number if account_number[0].isdigit() else get_BBAN_from_IBAN(account_number)
        # Check: bban can not have different ibans
        iban_cached = self._accounts_dict.get(bban, EMPTY)
        iban = account_number if not account_number[0].isdigit() else self._accounts_dict.get(bban, EMPTY)
        if iban_cached and iban != iban_cached:
            raise GeneralException(
                f'{PGM}: IBAN {iban} van rekening {value} verschilt van eerder gevonden '
                f'waarde {iban_cached}')
        return bban, iban

    @staticmethod
    def _row_to_obj(row) -> Account:
        return Account(
                bban=row[d[FD.Bban]],
                iban=row[d[FD.Iban]]
            )
