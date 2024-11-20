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


class AccountIO(BaseIO):

    @property
    def objects(self):
        return self._objects

    def __init__(self):
        super().__init__(TABLE)
        self._accounts_dict = {}
        self._started = False

    def _initialize(self, force=False):
        if self._started and not force:
            return
        self._started = True
        if not self._accounts_dict:
            for o in self._get_objects():
                self._accounts_dict[o.bban] = o

    def insert(self, obj: Account):
        """ Avoid duplicates """
        where = [Att(FD.Bban, obj.bban)]
        self._insert(obj, where, pgm=PGM)

    def add_account_to_cache(self, value):
        if not value:
            return
        bban, iban = self.get_bban_iban_from_account_number(value)
        if bban and iban:
            self._accounts_dict[bban] = Account(bban, iban)

    def persist_accounts(self):
        [self.insert(Account(bban, o.iban, o.description)) for bban, o in self._accounts_dict.items()]

    def get_current_iban(self, current_iban) -> str:
        """ Used in import_transactions """
        self._initialize()
        iban = current_iban
        # If iban does not exist (in the new iban cache list), return the first one from cache (or empty)
        if not any(o.iban == current_iban for o in self._accounts_dict.values()):
            iban = list(self._accounts_dict.values())[0].iban if self._accounts_dict else EMPTY
        return iban

    def get_description(self, iban) -> str:
        """ Used in summaries. Iban must be known at this point."""
        self._initialize()
        descriptions = [o.description for o in self._accounts_dict.values() if o.iban == iban]
        return descriptions[0] if descriptions and len(descriptions) == 1 else EMPTY

    def _get_objects(self) -> list:
        rows = self._session.db.select(TABLE, mode=FetchMode.WholeTable)
        self._objects = [self.row_to_obj(row) for row in rows]
        return self._objects

    def get_ibans(self) -> list:
        self._initialize()
        return [o.iban for o in self._accounts_dict.values()]

    def get_bbans(self) -> list:
        self._initialize()
        return [o.bban for o in self._accounts_dict.values()]

    def get_bban_iban_from_account_number(self, value) -> (str, str):
        account_number = sophisticate_account_number(value)
        if not account_number:
            return EMPTY
        # Convert account number to bban
        bban = account_number if account_number[0].isdigit() else get_BBAN_from_IBAN(account_number)
        # Check: bban can not have different ibans
        account = self._accounts_dict.get(bban)
        iban_cached = account.iban if account else None
        iban = account_number if not account_number[0].isdigit() else iban_cached
        if iban_cached and iban != iban_cached:
            raise GeneralException(
                f'{PGM}: IBAN {iban} van rekening {value} verschilt van eerder gevonden '
                f'waarde {iban_cached}')
        return bban, iban

    @staticmethod
    def row_to_obj(row) -> Account:
        return Account(
            bban=row[d[FD.Bban]],
            iban=row[d[FD.Iban]],
            description=row[d[FD.Description]]
        )
