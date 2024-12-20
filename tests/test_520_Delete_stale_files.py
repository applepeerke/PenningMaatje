#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import os
import unittest
from datetime import datetime
from os import listdir

from tests.Functions import start_up, get_session
from src.DL.Table import Table
from src.VL.Data.DataDriver import Singleton as DataDriver


def count_dirs(session, including_today=True) -> int:
    return sum(
        1 for i in listdir(session.backup_dir)
        if os.path.isdir(f'{session.backup_dir}{i}')
        and (including_today or i != datetime.now().strftime("%Y%m%d")))


class DeleteStaleFilesTestCase(unittest.TestCase):

    def test_TC01_Create_and_delete_stale_files(self):
        result = self._run_test()
        self.assertTrue(result.OK)
        result = self._run_test(build=True)
        self.assertTrue(result.OK)

    def _run_test(self, build=False):
        result = start_up(build=build)
        self.assertTrue(result.OK)

        DD = DataDriver()
        session = get_session()
        # Dir of today is overwritten
        count = count_dirs(session, including_today=False)  # count backup dirs except of today

        session.set_user_table_changed(Table.BookingCode)
        session.set_user_table_changed(Table.SearchTerm)

        DD.export_user_tables()
        dir_count = count_dirs(session, including_today=True)
        self.assertTrue(dir_count == count + 1,
                        msg=f'Expected {count + 1} but found {dir_count}')  # 1 dir created

        DD.delete_stale_files(retention_days=0)
        csv_files = []
        dir_names = [d for d in listdir(session.backup_dir)]
        for d in dir_names:
            dir_name = f'{session.backup_dir}{d}'
            if os.path.isdir(dir_name):
                for f in listdir(dir_name):
                    if f.lower().endswith('.csv'):
                        csv_files.append(f)

        # Most recent files are kept, 1 csv file per type should remain in n backup dirs.
        self.assertTrue(len(csv_files) == 4,
                        msg=f'Expected 4 but found {len(csv_files)}')
        return DD.result


if __name__ == '__main__':
    unittest.main()
