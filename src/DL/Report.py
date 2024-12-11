#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini colhdg_report
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# -------------------------------------------------------------------------------------------------------------------

from src.DL.DBDriver.Att import Att
from src.DL.Model import Model, FD
from src.DL.Table import Table
from src.GL.Const import EMPTY
from src.GL.Functions import canonize
from src.GL.GeneralException import GeneralException
from src.GL.Validate import isDate, isAmount, isCD, isAccountName, isCode, isNotCode, likeAccount

PGM = 'Report'

model = Model()
TE_dict_by_colno = model.get_colno_per_report_colhdg(Table.TransactionEnriched)
TX_dict = model.get_colno_per_att_name(Table.Transaction)


class Report:
    # Reports
    CsvExport = 'CsvExport'

    Names = [CsvExport]

    # Maps Report to TransactionEnriched.
    Mapping = {
        CsvExport: {
            1: Att(FD.Date),
            2: Att(FD.Name),
            3: Att(FD.Account_number),
            4: Att(FD.Counter_account_number),
            5: Att(FD.Transaction_code),
            6: Att(FD.Amount_signed),
            7: Att(FD.Transaction_type),
            8: Att(FD.Comments),
            9: Att(FD.Booking_code),
            10: Att(FD.Booking_type),
            11: Att(FD.Booking_id, in_db=True)  # Exclude from csv
        }
    }
    # Input csv synonyms canonized (lowercase and removed spaces).
    Synonyms = {
        FD.Date: {'date'},
        FD.Name: {'rekeningnaam', 'naam tegenpartij', 'name'},
        FD.Add_Sub: {'afbij'},
        FD.Counter_account_number: {'tegenrekening', 'tegenrekeningnummer', 'tegenrekening iban', 'counterparty'},
        FD.Account_number: {'rekening', 'iban/bban', 'iban', 'account'},
        FD.Transaction_code: {'transactiecode', 'mutatiecode'},
        FD.Amount: {'bedrag(eur)', 'amount'},
        FD.Transaction_type: {'transactiesoort'},
        FD.Comments: {'omschrijving', 'description'}
    }

    @property
    def report_name(self):
        return self._report_name

    @property
    def header_names(self):
        return self._header_names

    @property
    def attributes(self):
        return self._attributes

    def __init__(self, report_name=None):
        self._report_name = report_name
        if report_name and (report_name not in self.Names or report_name not in self.Mapping):
            raise GeneralException(f'{__name__}: Report name {report_name} is not supported.')

        # Defaults to CsvImport definition from model Transaction
        self._csv_def = self.Mapping.get(report_name, model.get_atts(Table.Transaction))
        self._header_names = [att.colhdg_report for colno, att in self._csv_def.items()]
        self._attributes = [att for att in self._csv_def.values()] if report_name else []
        self._missing_column_names = []

    def map_report_to_model(self, derived_names=None) -> dict:
        """
        Maps table def to a report definition, so you can e.g. use TE_dict[att.name]. Used in export.
        Input: mapping uses att.colhdg_report from both csv and model definition.
        Output: {report att_name: model colno}.
        """
        derived_names = derived_names or []
        missing_names = [att.colhdg_report for att in self._csv_def.values()
                         if att.colhdg_report not in TE_dict_by_colno]
        if missing_names and not all(name in derived_names for name in missing_names):
            raise GeneralException(f'CsvExport names not found in Model definition: "{missing_names}"')
        return {att.name: TE_dict_by_colno.get(att.name, EMPTY) for col_no, att in self._csv_def.items()}

    def get_transaction_file_colno_mapping(self, first_row=None) -> dict:
        """
        Maps csv header row to CsvImport definition.
        return: {model att_name: csv colno}
        First_row may not have column headings but direct details; also it may be from different banks.
        """
        first_row = first_row or self._header_names

        # Validation
        if not all(type(i) is str for i in first_row):
            raise GeneralException(f'Ongeldige regel met kopteksten gevonden:\n"{str(first_row)}"')

        # Some csv downloads have a header (ING), others have not (Triodos)
        colno_mapping = self._map_columns_from_detail_row(first_row) \
            if any(isDate(value) for value in first_row) \
            else self._map_columns_from_header_row(first_row)
        return self._map_evaluate(colno_mapping)

    def _map_columns_from_header_row(self, header_row) -> dict:
        """
        return: { model colno: csv colno } (zero_based)
        ALL model columns must  be populated.
        Csv header names  are looked up  in the model first. If not found, in Report.Synonyms.
        If not found and optional, they will be -1, else error.

        Example:
            header_row:         ['Datum', 'Bedrag (EUR)', 'Rekening', 'Rekening naam', ...]
            Model Transaction:  {'Datum': 1, 'Bedrag': 2, 'Naam': 3, 'TegenrekeningNummer': 4, ...}
            return:             {1: 0, 2: 1, 3: 4, 4: 3, ...}
        """
        self._missing_column_names = []
        # CsvImport def is the target
        # Convert to LC, remove spaces
        header_lc = [canonize(name) for name in header_row]
        import_def = model.get_atts(Table.Transaction, zero_based=True)

        # a. populate exact header matches.
        colno_mapping = {}
        for colno, att in import_def.items():
            # Per header column try all synonyms
            for h in range(len(header_lc)):
                for name in self._get_synonyms(att.name):
                    if header_lc[h] == name:
                        colno_mapping[colno] = h

        # b. populate near header matches, e.g. "Bedrag (EUR)" -> "Bedrag"
        for colno, att in import_def.items():
            if colno not in colno_mapping:
                # Per header column try all synonyms
                for h in range(len(header_lc)):
                    for name in self._get_synonyms(att.name):
                        if header_lc[h] in name or name in header_lc[h]:
                            if h not in colno_mapping.values():
                                colno_mapping[colno] = h

        # c. Now every required header-column must be present in the target definition.
        if len(colno_mapping) < len(import_def):
            required = [colno for colno, att in import_def.items() if not att.optional]
            self._missing_column_names = [
                import_def[colno].colhdg_report for colno in required if colno not in colno_mapping.keys()]
        return colno_mapping

    @staticmethod
    def _get_synonyms(att_name) -> set:
        synonyms = {canonize(att_name)}
        for s in Report.Synonyms.get(att_name, {}):
            if s:
                synonyms.add(canonize(s))
        return synonyms

    def _map_columns_from_detail_row(self, from_detail_row) -> dict:
        """
        When there is no header.
        from_detail_row: row without column names.
        return: mapping { model colno: csv colno } (zero_based)

        Example from_detail_row:
        Datum | Rekening | Bedrag | C/D | Naam | Tegenrekening | Transactiecode | Mededelingen |
        "06-03-2009,"NL84TRIO0123345678","500,00","Credit","HEIJLIGERS/HEIJLIGERS-FE","1232123","PO",
        "TRANSACTIEDATUM* 05-03-2009","500,00"
        """
        self._pos = 0
        self._colnos = set()
        self._colno_mapping = {}
        # Datum (eerst)
        self._add_item(FD.Date, from_detail_row, isDate)
        # Bedrag (daarna)
        self._add_item(FD.Amount, from_detail_row, isAmount, self._pos + 1)
        # Rekening (eerst)
        self._add_item(FD.Account_number, from_detail_row, likeAccount)
        # Tegenrekening (daarna)
        self._add_item(FD.Counter_account_number, from_detail_row, likeAccount, self._pos + 1)
        # Naam (eerst)
        self._add_item(FD.Name, from_detail_row, isAccountName)
        # Af Bij
        self._add_item(FD.Add_Sub, from_detail_row, isCD)
        # Transactiecode
        self._add_item(FD.Transaction_code, from_detail_row, isCode)
        # Mededelingen (daarna)
        self._add_item(FD.Comments, from_detail_row, isNotCode, self._pos + 1)
        return self._colno_mapping

    def _add_item(self, att_name, from_detail_row, validator: callable, start_pos=0, alt_validator: callable = None):
        colno = self._get_item_colno(att_name, from_detail_row, validator, start_pos)
        # Not found, optionally try alternative validator
        if colno == -1:
            if alt_validator:
                colno = self._get_item_colno(att_name, from_detail_row, alt_validator, start_pos)
                if colno == -1:
                    return
            return
        self._colno_mapping[TX_dict[att_name]] = colno

    def _get_item_colno(self, att_name, from_detail_row, validator: callable, start_pos=0) -> int:
        """ Mededelingen is laatste, kan van alles bevatten, mag nog niet voorkomen."""
        for i in range(start_pos, len(from_detail_row)):
            if i not in self._colnos and validator(from_detail_row[i]):
                self._colnos.add(i)
                self._pos = i
                return i
        raise GeneralException(f'Veld "{att_name}" niet gevonden in "{from_detail_row}"')

    def _map_evaluate(self, to_dict) -> dict:
        # Success
        if not self._missing_column_names:
            # Sort
            result = {key: val for key, val in sorted(to_dict.items(), key=lambda x: x[1])}
            return result

        # Fail
        en = 'en' if len(self._missing_column_names) > 1 else EMPTY
        zijn = 'zijn' if len(self._missing_column_names) > 1 else 'is'
        raise GeneralException(
            f'Veld{en} "{", ".join(self._missing_column_names)}" in de kopregel {zijn} niet gevonden.')
