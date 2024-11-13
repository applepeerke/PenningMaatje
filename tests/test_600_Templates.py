#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from src.BL.Functions import get_annual_account_filename
from src.BL.Managers.TemplateManager import TOTAL_GENERAL
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Functions import maybeFloat, toFloat
from src.GL.GeneralException import GeneralException
from src.pmc import PMC
from tests.Functions import start_up, get_input_sub_dir

csvm = CsvManager()


class TemplateTestCase(unittest.TestCase):

    def test_TC01_Templates(self):

        self._run_test('Jaarrekening', exp_tg=-103.49, exp_cols=6, exp_rows=19)
        self._run_test('Jaarrekening - without totals', exp_tg=-103.49, exp_cols=6, exp_rows=9)
        self._run_test('Jaarrekening - 3 empty extra columns', exp_tg=-103.49, exp_cols=9, exp_rows=19)
        self._run_test('Jaarrekening - 1 realisation 1 budget', exp_tg=-103.49, exp_cols=5, exp_rows=19)
        self._run_test('Jaarrekening - 1 realisation 0 budget', exp_tg=-103.49, exp_cols=4, exp_rows=19)
        self._run_test('Jaarrekening - 0 amounts', exp_tg=0.0, exp_cols=3, exp_rows=11)
        self._run_test('Jaarrekening - wrong format', exp_result=False)
        self._run_test('Jaarrekening - invalid tokens', exp_result=False)

    def _run_test(
            self,
            template_name,
            exp_tg=0.0,  # Total General
            exp_cols=0,
            exp_rows=0,
            exp_result=True
    ):
        # Start config, session and db, import transactions
        input_sub_dir = get_input_sub_dir('Bankafschriften')
        result = start_up(input_dir=input_sub_dir, build=True)
        self.assertTrue(result.OK)

        try:
            # Start PenningMaatje (without build db).
            year = 2018
            export_dir = Session().export_dir
            filename = get_annual_account_filename(year, 12, title=template_name)
            path = f'{export_dir}{filename}'
            pmc = PMC(export_dir, year, build=False)
            pmc.produce_csv_files(template_name, year)
        except GeneralException:
            self.assertTrue(exp_result is False)
            return

        # Check no. of rows
        rows = csvm.get_rows(data_path=path, include_header_row=True, include_empty_row=True)
        self.assertTrue(
            len(rows) == exp_rows,
            msg=f'Real rows count ({len(rows)}) is not as expected ({exp_rows}).\nPath is "{path}"')

        # Check no. of columns
        cols_count = len(rows[0]) if rows else 0
        self.assertTrue(
            cols_count == exp_cols,
            msg=f'Real columns count ({cols_count}) is not as expected ({exp_cols}).\nPath is "{path}"')

        # Check General Total
        for row in rows:
            if any(TOTAL_GENERAL.upper() in cell.upper() for cell in row):
                # 1st cell should contain realisation total general amount.
                amounts = [cell for cell in row if maybeFloat(cell)]
                realisation_general_total = toFloat(amounts[0]) if amounts else 0.0
                self.assertTrue(
                    realisation_general_total == exp_tg,
                    msg=f'Total general ({realisation_general_total}) is not as expected '
                        f'({exp_tg}).\nPath is "{path}"')
                break


if __name__ == '__main__':
    unittest.main()
