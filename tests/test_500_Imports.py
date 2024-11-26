#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from tests.Functions import start_up, get_input_sub_dir
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.DL.Table import Table


class ImportTestCase(unittest.TestCase):

    def test_TC01_Choices(self):

        # No transactions
        self._run_test(get_input_sub_dir(
            'Bankafschriften - geen'),
            expected_accounts=0,
            expected_import_result_OK=False)

        # Invalid transactions header
        self._run_test(get_input_sub_dir(
            'Bankafschriften - ongeldige header'),
            expected_transaction_count=0,
            expected_accounts=0,
            expected_import_result_OK=False)

        # Invalid transactions format
        self._run_test(get_input_sub_dir(
            'Bankafschriften - ongeldig formaat'),
            expected_transaction_count=0,
            expected_accounts=0,
            expected_import_result_OK=False)

        # Double transactions - cancel
        self._run_test(get_input_sub_dir(
            'Bankafschriften - dubbel'),
            expected_transaction_count=0,
            expected_accounts=4,
            expected_import_result_OK=False
        )

        # Double transactions - continue
        self._run_test(get_input_sub_dir(
            'Bankafschriften - dubbel'),
            expected_import_result_OK=False,
            expected_accounts=2,
            auto_continue=True)

        # Multiple accounts
        self._run_test(get_input_sub_dir(
            'Bankafschriften - meerdere rekeningen'),
            expected_transaction_count=3,
            expected_accounts=4)

    def _run_test(self,
                  input_dir,
                  expected_import_result_OK=True,
                  expected_transaction_count=0,
                  expected_accounts=0,
                  auto_continue=False):
        # Start config, session and db, import transactions
        result = start_up(input_dir=input_dir, build=True, auto_continue=auto_continue)
        # Import as expected?
        self.assertTrue(result.OK == expected_import_result_OK)
        # Transactions count
        self._check_record_count(Session(), Table.TransactionEnriched, expected_transaction_count)
        # Accounts count
        self._check_record_count(Session(), Table.Account, expected_accounts)

    def _check_record_count(self, session, table_name, expected_count):
        real_count = session.db.count(table_name)
        self.assertTrue(
            real_count == expected_count,
            msg=f'Real {table_name} record count ({real_count}) is not as expected ({expected_count})')


if __name__ == '__main__':
    unittest.main()
