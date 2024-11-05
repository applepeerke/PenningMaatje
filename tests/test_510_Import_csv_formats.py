#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from src.DL.Report import Report
from src.GL.Const import EMPTY
from src.GL.GeneralException import GeneralException

base_list = ['Datum', 'Bedrag', 'Naam', 'Af Bij', 'Rekening', 'Tegenrekening', 'Mededelingen']


class ImportFormatsTestCase(unittest.TestCase):

    def test_TC01_Expected_csv_columns(self):
        """ Aantal verwachte te importeren kolommen. Max. 8 """
        # Header
        # - Mutatiesoort zit niet  in bestand Transaction, TransactieCode wel (maar niet verplicht).
        self._run_test(7, base_list)
        self._run_test(7, base_list, extend_with=['Mutatiesoort'])
        self._run_test(8, base_list, extend_with=['TransactieCode'])
        # - Credit, D/C zijn synoniemen.
        self._run_test(7, base_list, extend_with=['Credit'])
        self._run_test(7, base_list, extend_with=['D/C'])
        # - ING Spaarrekening bevat "Rekening naam" ipv "Rekening"
        self._run_test(7, ['Datum', 'Bedrag', 'Rekening naam', 'Rekening', 'Tegenrekening', 'Mededelingen', 'Af Bij'])
        # - Datum ontbreekt
        self._run_test(0, ['Bedrag', 'Rekening naam', 'Rekening', 'Tegenrekening', 'Mededelingen', 'Af Bij'])
        # - "Date" is spelfout
        self._run_test(0, ['Datm', 'Bedrag', 'Rekening naam', 'Rekening', 'Tegenrekening', 'Mededelingen', 'Af Bij'])
        # - Andere volgorde
        self._run_test(7, ['Af Bij', 'Mededelingen', 'Tegenrekening', 'Rekening', 'Naam', 'Bedrag', 'Datum'])

        # Geen header
        self._run_test(8, ['2023-01-27', '1,00', 'Mijn naam', 'NLABCD0001234567', '1234567', 'Af', 'BA', 'opm'])
        self._run_test(8, ['2023-01-27', '1,00', 'Mijn naam', 'C 123-45678', '1234567', 'Af', 'BA', 'opm'])

    def _run_test(self, expected: int, first_row, extend_with=None):
        extra_msg = EMPTY
        base = first_row.copy()
        mapping = {}
        if extend_with:
            base.extend(extend_with)
        # Get colno mapping
        try:
            mapping: dict = Report().get_transaction_file_colno_mapping(base)
        except GeneralException as e:
            extra_msg = f' {e}'
        self.assertTrue(len(mapping) == expected, msg=f'Expected {expected}, found {len(mapping)}. {extra_msg}')

    def _check_record_count(self, session, table_name, expected_count):
        real_count = session.db.count(table_name)
        self.assertTrue(
            real_count == expected_count,
            msg=f'Real {table_name} record count ({real_count}) is not as expected ({expected_count})')


if __name__ == '__main__':
    unittest.main()
