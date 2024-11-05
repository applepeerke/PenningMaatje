#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
#
from collections import OrderedDict

from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.AttType import AttType
from src.DL.Table import Table
from src.GL.GeneralException import GeneralException

NAME = 'Name'
DESC = 'Description'
TYPE = 'Type'
VALUE = 'Value'
ID = 'Id'
PK = 'PK'

PGM = 'Model'
EMPTY = ''
table = Table()


# Index definitions
class IndexDef(object):
    AC_IX_on_Iban = 'AC_IX_on_Iban'
    CA_IX_on_CounterAccount_name = 'CA_IX_on_CounterAccount_name'
    TX_IX_on_Transaction_name = 'TX_IX_on_Transaction_name'
    TT_IX_on_Transaction_type = 'TT_IX_on_Transaction_type'
    BK_IX_on_Booking_type = 'BK_IX_on_Booking_type'
    BK_IX_on_Booking_code = 'BK_IX_on_Booking_code'
    BK_IX_on_Booking_protected = 'BK_IX_on_Booking_protected'
    ST_IX_on_Booking_code = 'ST_IX_on_Booking_code'
    ST_IX_on_Search_term = 'ST_IX_on_Search_term'

    TE_IX_on_Date = 'TE_IX_on_Date'
    TE_IX_on_Year = 'TE_IX_on_Year'
    TE_IX_on_Transaction_code = 'TE_IX_on_Transaction_code'
    TE_IX_on_Transaction_type = 'TE_IX_on_Transaction_type'
    TE_IX_on_Amount = 'TE_IX_on_Amount'
    TE_IX_on_Booking = 'TE_IX_on_Booking'
    TE_IX_on_Comment = 'TE_IX_on_Comment'
    TE_IX_on_Name = 'TE_IX_on_Name'
    TE_IX_on_Counter_account = 'TE_IX_on_Counter_account'
    TE_IX_on_Remarks = 'TE_IX_on_Remarks'

    FF_IX_on_Label = 'FF_IX_on_Label'


# Field definition
class FD(object):
    ID = 'Id'
    No = 'No'
    Active = 'Actief'

    # FFD
    FF_TableName = 'TableName'
    FF_AttName = 'AttributeName'
    FF_AttType = 'AttributeType'
    FF_AttLength = 'AttributeLength'
    FF_Derived = 'Derived'

    # Booking
    Booking_id = 'BoekingID'
    Booking_type = 'BoekingsType'
    Booking_maingroup = 'Hoofdgroep'
    Booking_subgroup = 'Subgroep'
    Booking_code = 'BoekingsCode'
    Booking_description = 'BoekingOmschrijving'
    SeqNo = 'Volgnr'
    Protected = 'Beschermd'
    Booking_description_searchable = 'ZoekBoekingOmschrijving'

    # AnnualAccount
    Amount_realisation = 'RealisatieBedrag'
    Amount_budget_this_year = 'BegrotingsBedrag'
    Amount_budget_previous_year = 'BegrotingsBedragVorigJaar'

    # Account
    Bban = 'Bban'
    Iban = 'Iban'

    # CounterAccount
    Counter_account_id = 'TegenrekeningID'
    FirstComment = 'EersteMededelingen'

    # FlatFile
    Key = 'Key'
    Value = 'Value'

    # Log
    Log = 'Log'
    Log_entry = 'Logregels'

    # Month
    Costs = 'Uitgaven'
    Overbooking = 'Overboeking'
    Revenues = 'Inkomsten'
    Balance = 'Saldo'
    Balance_corrected = 'SaldoGecorrigeerd'

    # Searchterm
    SearchTerm = 'Zoekterm'
    Counter_account_number = 'Tegenrekening'
    Counter_account_bban = 'TegenrekeningBban'
    Name = 'Naam'

    # Summary
    Trend_years = 'TrendJaren'

    # Transaction
    Account_number = 'Rekening'
    Account_name = 'RekeningNaam'
    Amount = 'Bedrag'
    Amount_monthly = 'BedragPerMaandNetto'
    Amount_yearly = 'BedragPerJaarNetto'
    Currency = 'Valuta'
    Amount_signed = 'BedragMetTeken'
    Add_Sub = 'Af_Bij'
    Transaction_type = 'MutatieSoort'
    Transaction_code = 'TransactieCode'
    Comments = 'Mededelingen'
    SaldoAfterMutation = 'Saldo na mutatie'
    Tag = 'Tag'
    Date_format = 'DatumFormaat'

    # TransactieEnriched
    Account_bban = 'RekeningBban'
    Date = 'Datum'
    Year = 'Jaar'
    Month = 'Maand'
    Counter_bban = 'CounterBban'
    Transaction_date = 'TransactieDatum'
    Transaction_time = 'TransactieTijd'
    Remarks = 'Bijzonderheden'

    # TransactionType
    Bank_name = 'BankNaam'


FFD = {}


def where_for_id(Id):
    return [Att(FD.ID, Id)]


def get_colno(colno: int, zero_based: bool) -> int:
    return colno - 1 if zero_based else colno


class Model(object):
    @property
    def FFD(self):
        return self._FFD

    @property
    def DB_tables(self):
        return self._DB_tables

    @property
    def DB_base_tables(self):
        return self._DB_base_tables

    @property
    def user_maintainable_tables(self):
        return self._user_maintainable_tables

    def __init__(self):
        self._table = Table
        self._index = 0

        self._DB_tables = [
            Table.Account,
            Table.AnnualAccount,
            Table.Booking,
            Table.CounterAccount,
            Table.FlatFiles,  # Retrieved kv-pairs from TransactionEnriched
            Table.Log,
            Table.Month,
            Table.SearchTerm,
            Table.Transaction,
            Table.TransactionEnriched,
            Table.Year,
        ]

        self._DB_base_tables = [
            Table.Booking,
            Table.CounterAccount,
            Table.SearchTerm,
            Table.AnnualAccount
        ]
        self._user_maintainable_tables = [
            Table.Booking,
            Table.CounterAccount,
            Table.SearchTerm
        ]

        self._FFD_FFD = OrderedDict({
            1: Att(FD.FF_TableName),
            2: Att(FD.FF_AttName),
            3: Att(FD.FF_AttType),
            4: Att(FD.FF_AttLength, type=AttType.Int),
            5: Att(FD.FF_Derived, type=AttType.Bool)
        })

        """
        Table definitions 
        """
        self._Account = OrderedDict({
            1: Att(FD.Bban),
            2: Att(FD.Iban),
        })

        self._FlatFiles = OrderedDict({
            1: Att(FD.Key),
            2: Att(FD.Value)
        })

        self._TransactieCode = OrderedDict({
            1: Att(FD.Transaction_code),
        })
        self._TransactionEnriched = OrderedDict({
            1: Att(FD.Account_bban, visible=False, colhdg_report='Rekening'),
            2: Att(FD.Date, type=AttType.Int),
            3: Att(FD.Year, type=AttType.Int, visible=False),
            4: Att(FD.Month, type=AttType.Int, visible=False),
            5: Att(FD.Name, col_width=40),
            6: Att(FD.Transaction_code, visible=False),
            7: Att(FD.Add_Sub, visible=False, colhdg_report='Af Bij'),
            8: Att(FD.Amount, type=AttType.Float, visible=False),
            9: Att(FD.Amount_signed, col_width=18, type=AttType.Float),
            10: Att(FD.Comments),
            11: Att(FD.Counter_account_number, visible=False),
            12: Att(FD.Counter_account_bban, visible=False),
            13: Att(FD.Transaction_type, visible=False),
            14: Att(FD.Remarks, col_width=30),
            15: Att(FD.Transaction_date, visible=False, colhdg_report='TDatum', description='Transactie datum'),
            16: Att(FD.Transaction_time, visible=False, colhdg_report='TTijd', description='Transactie tijd'),
            17: Att(FD.Booking_code),  # Is derived from Booking_id
            18: Att(FD.Counter_account_id, visible=False, type=AttType.Int),  # FK
            19: Att(FD.Booking_id, visible=False, type=AttType.Int),  # FK
        })
        self._Transaction = OrderedDict({
            1: Att(FD.Date),
            2: Att(FD.Name),
            3: Att(FD.Account_number),
            4: Att(FD.Counter_account_number),
            5: Att(FD.Transaction_code, optional=True),  # May during import be derived from MutatieSoort
            6: Att(FD.Add_Sub, colhdg_report='Af Bij', optional=True),
            7: Att(FD.Amount, type=AttType.Float),
            8: Att(FD.Comments),
            9: Att(FD.Date_format, optional=True)
        })
        self._TransactionSoort = OrderedDict({
            1: Att(FD.Transaction_type),
        })
        self._TransactionType = OrderedDict({
            1: Att(FD.Bank_name),
            2: Att(FD.Transaction_code),
            3: Att(FD.Transaction_type),
        })
        self._Year = OrderedDict({
            1: Att(FD.Year, type=AttType.Int),
            2: Att(FD.Overbooking, description='Overboeking', type=AttType.Float),
            3: Att(FD.Costs, type=AttType.Float),
            4: Att(FD.Revenues, type=AttType.Float),
            5: Att(FD.Balance, type=AttType.Float),
            6: Att(FD.Balance_corrected, colhdg_report='Saldo - Overb.', description='Saldo - Overboeking',
                   type=AttType.Float),
        })

        # Month = Year last part
        self._Month = OrderedDict({1: Att(FD.Year, type=AttType.Int), 2: Att(FD.Month, type=AttType.Int)})
        for No, att in self._Year.items():
            if No > 1:
                self._Month[No + 1] = att
        """ 
        User import 
        """
        self._Booking = OrderedDict({
            1: Att(FD.Booking_type),
            2: Att(FD.Booking_maingroup),
            3: Att(FD.Booking_subgroup),
            4: Att(FD.Booking_code),
            5: Att(FD.SeqNo, type=AttType.Int),
            # Not required in csv
            6: Att(FD.Protected, type=AttType.Bool, derived=True, col_width=15)
        })
        self._CounterAccount = OrderedDict({
            1: Att(FD.Counter_account_number),
            2: Att(FD.Name),
            3: Att(FD.FirstComment),
            4: Att(FD.Booking_code)
        })
        self._SearchTerms = OrderedDict({
            1: Att(FD.SearchTerm, col_width=20),
            2: Att(FD.Booking_code, visible=False),
            3: Att(FD.Booking_description, in_db=False, col_width=60)
        })
        self._AnnualAccount = OrderedDict({
            1: Att(FD.Year, type=AttType.Int),
            2: Att(FD.Booking_type),
            3: Att(FD.Booking_maingroup),
            4: Att(FD.Booking_subgroup),
            5: Att(FD.Booking_code),
            6: Att(FD.Amount_realisation, type=AttType.Float),
            7: Att(FD.Amount_budget_this_year, type=AttType.Float),
            8: Att(FD.Amount_budget_previous_year, type=AttType.Float),
        })
        self._Log = OrderedDict({
            1: Att(FD.Log_entry),
        })

        """
        Database
        """
        self._FFD = {
            Table.Account: self._Account,
            Table.AnnualAccount: self._AnnualAccount,
            Table.Booking: self._Booking,
            Table.CounterAccount: self._CounterAccount,

            Table.FlatFiles: self._FlatFiles,
            Table.Log: self._Log,
            Table.Month: self._Month,
            Table.SearchTerm: self._SearchTerms,
            Table.Transaction: self._Transaction,
            Table.TransactionEnriched: self._TransactionEnriched,
            Table.Year: self._Year,
        }

        self._Indexes = {

            Table.Account: {
                PK: [FD.Bban],
                IndexDef.AC_IX_on_Iban:
                    [FD.Iban,
                     FD.ID],
            },
            Table.AnnualAccount: {
                PK: [FD.Booking_type,
                     FD.Booking_maingroup,
                     FD.Booking_subgroup]
            },
            Table.Booking: {
                PK: [FD.Booking_type,
                     FD.Booking_maingroup,
                     FD.Booking_subgroup],
                IndexDef.BK_IX_on_Booking_type:
                    [FD.Booking_type,
                     FD.ID],
                IndexDef.BK_IX_on_Booking_code:
                    [FD.Booking_code,
                     FD.ID],
                IndexDef.BK_IX_on_Booking_protected:
                    [FD.Booking_maingroup,
                     FD.Protected],
            },
            Table.CounterAccount: {
                PK: [FD.Name],
                IndexDef.CA_IX_on_CounterAccount_name:
                    [FD.Name,
                     FD.ID],
            },
            Table.FlatFiles: {
                PK: [FD.Key],
                IndexDef.FF_IX_on_Label:
                    [FD.Key,
                     FD.ID],
            },
            Table.Month: {PK: [FD.Year, FD.Month]},

            Table.SearchTerm: {
                PK: [FD.SearchTerm],
                IndexDef.ST_IX_on_Search_term:
                    [FD.SearchTerm,
                     FD.ID],
                IndexDef.ST_IX_on_Booking_code:
                    [FD.Booking_code,
                     FD.ID],
            },

            # 1 account_bban
            Table.Transaction: {
                PK: [FD.Account_number, FD.Date, FD.Counter_account_number, FD.Name, FD.Amount, FD.Comments, FD.ID],
                IndexDef.TX_IX_on_Transaction_name:
                    [FD.Name,
                     FD.ID],
            },
            Table.TransactionEnriched: {
                PK: [FD.Account_bban, FD.Date, FD.Counter_account_number, FD.Name, FD.Amount, FD.Comments, FD.ID],
                IndexDef.TE_IX_on_Date:
                    [FD.Account_bban,
                     FD.Date,
                     FD.Counter_account_id,
                     FD.ID],
                IndexDef.TE_IX_on_Year:
                    [FD.Account_bban,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Counter_account:
                    [FD.Account_bban,
                     FD.Counter_account_id,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Transaction_code:
                    [FD.Account_bban,
                     FD.Transaction_code,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Amount:
                    [FD.Account_bban,
                     FD.Amount_signed,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Transaction_type:
                    [FD.Account_bban,
                     FD.Transaction_type,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Booking:
                    [FD.Account_bban,
                     FD.Booking_id,
                     FD.Year,
                     FD.ID],
                IndexDef.TE_IX_on_Remarks:
                    [FD.Account_bban,
                     FD.Remarks,
                     FD.Year,
                     FD.ID],
            },
            Table.Year: {PK: [FD.Year]},
        }

    def get_FFD(self):
        """
        :return: File Field Definition.
        """
        return self._FFD_FFD

    def get_indexes(self, table_name):
        """
        :return: Table indexes.
        """
        return self._Indexes.get(table_name, {})

    def _get_pk_names(self, table_name, include_id=False) -> list:
        """
        :return: PK index.
        """
        pk_names = self._Indexes[table_name][PK] \
            if table_name in self._Indexes and PK in self._Indexes[table_name] \
            else []
        if not include_id and ID in pk_names:
            pk_names.remove(ID)
        return pk_names

    def get_pk_text(self, table_name, row, include_id=False) -> str:
        """
        @return: PK text like "id=1, order='myOrder'"
        """
        pk_names = self._get_pk_names(table_name, include_id)
        pk_text = EMPTY
        for n in pk_names:
            if pk_text:
                pk_text = f'{pk_text}, {n}={row[self.get_colno_per_att_name(table_name)[n]]}'
            else:
                pk_text = f'{n}={row[self.get_colno_per_att_name(table_name)[n]]}'
        return pk_text

    def get_db_definition(self, table_name):
        """
        :return: Db definition (Only if attribute exists in db).
        """
        self._index = 0
        dfn = self.get_model_definition(table_name).values()
        return {self._get_index(): att for att in dfn if att.in_db}

    def _get_index(self) -> int:
        self._index += 1
        return self._index

    def get_model_definition(self, table_name):
        """
        :return: Model definition.
        """
        return self._FFD_FFD if table_name == 'FFD' else self._FFD.get(table_name, {})

    def get_att(self, table_name, att_name, value=None, relation=None) -> Att or None:
        """
        :return: Model attribute. Optionally populated with a value and/or relation.
        """
        for att in self.get_model_definition(table_name).values():
            if att.name == att_name:
                if value is not None:
                    att.value = value
                    att.set_relation(relation)
                return att
        return None

    def get_atts(self, table_name, zero_based=False) -> dict:
        """
        :return: db attributes
        """
        return {get_colno(colno, zero_based): att for colno, att in self.get_db_definition(table_name).items()}

    def get_colno_per_att_name(
            self, table_name, zero_based=True, include_derived=True, include_not_in_db=False) -> dict:
        """
        :return: Attribute names by db column numbers. Example: {name : col_no }.
        """
        if include_not_in_db:
            return {
                att.name: get_colno(colno, zero_based) for colno, att in self.get_model_definition(table_name).items()
                if (not att.derived or include_derived)}
        else:
            return {att.name: get_colno(colno, zero_based) for colno, att in self.get_db_definition(table_name).items()
                if (not att.derived or include_derived)}

    def get_att_names(self, table_name):
        """
        :return: db attribute names in designed sequence
        """
        return [att.name for att in self.get_db_definition(table_name).values()]

    def get_att_name_per_colno(self, table_name, zero_based=True):
        """
        :return: db attribute names
        """
        return {get_colno(colno, zero_based): att.name for colno, att in self.get_db_definition(table_name).items()}

    def get_att_per_name(self, table_name) -> dict:
        """
        :return: db attributes by name
        """
        return {att.name: att for key, att in self.get_db_definition(table_name).items()}

    def get_column_number(self, table_name, col_name, zero_based=False) -> int:
        """
        :return: db attribute sequence number
        """
        colno = [col_number for col_number, att in self.get_db_definition(table_name).items() if att.name == col_name]
        return get_colno(colno[0], zero_based) if colno else -1

    def get_value(self, table_name, att_name, row):
        """ Get value from db row """
        if not table_name or not att_name or not row:
            raise GeneralException(f'{PGM}.get_value: Invalid input')
        colno = self.get_column_number(table_name, att_name)
        if -1 < colno < len(row):
            return row[colno]
        raise GeneralException(f'{PGM}.get_value: Invalid column number "{colno}".')

    def get_colno_per_report_colhdg(self, table_name) -> dict:
        """
        :return: Report column headings by db column number, i.e. {colhdg : col_no }
        """
        return {att.colhdg_report: colno for colno, att in self.get_db_definition(table_name).items()}

    def get_report_colhdg_names(self, table_name, include_not_in_db=False) -> list:
        """
        :return: Report column headings
        """
        if include_not_in_db:
            return [att.colhdg_report for att in list(self.get_model_definition(table_name).values())]
        else:
            return [att.colhdg_report for att in list(self.get_db_definition(table_name).values())]

    def get_pk_atts_from_row(self, table_name, row) -> [Att]:
        """
        :return: The PK where-attributes from a selected db row
        """
        pk_def = self._Indexes[table_name][PK]
        return [self.get_att(table_name, att_name, value=row[self.get_column_number(table_name, att_name)])
                for att_name in pk_def if att_name != ID] \
            if row and PK in self._Indexes[table_name] else []

    def get_logical_ID_from_row(self, table_name, row) -> str:
        """
        :return: The pk row values separated by "|", e.g. '123456|20220413|618'
        """
        return '|'.join(
            [str(row[self.get_column_number(table_name, att_name)])
             for att_name in self._Indexes[table_name][PK]
             if att_name != ID]
        ) if row else EMPTY

    def to_db_row(self, table_name: Table, attributes: dict, check_pk=True) -> list:
        """
        attributes: {name : Att }
        :return: List of table attribute values, used for table insert.
        """
        # Check if received attribute types correspond to table definition.
        [self._validate_type(table_name, att_name, att.value) for att_name, att in attributes.items()]
        # Check if pk is specified.
        if check_pk:
            self._is_pk_present(table_name, attributes)
        return [self._get_att_value(attributes, att_name) for att_name in self.get_att_names(table_name)]

    @staticmethod
    def _get_att_value(attributes, name):
        return attributes.get(name).value if name in attributes else EMPTY

    def _validate_type(self, table_name: Table, att_name: str, value):
        """
        Check if all inputed attributes are of the expected model type.
        """
        dfn = self.get_att(table_name, att_name)
        dfn_types = AttType.python_allowed_types.get(dfn.type)
        if type(value).__name__ not in dfn_types:
            raise GeneralException(
                f'{PGM}.to_row: parameter "{att_name}" value "{value}" has type "{type(value).__name__}". '
                f'However only allowed are  "{dfn_types}"')

    def _is_pk_present(self, table_name: Table, attributes):
        """
        Check if complete PK is present in attributes .
        """
        pk_names = self._get_pk_names(table_name, include_id=False)
        if pk_names and not all(att_name in attributes for att_name in pk_names):
            raise GeneralException(
                f'{PGM}.to_row: not all PK attribute names ("{pk_names}") are received in the input. ')
