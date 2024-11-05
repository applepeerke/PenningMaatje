#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from tests.Functions import start_up, start_db, get_input_sub_dir
from src.BL.Managers.ConsistencyManager import ConsistencyManager
from src.BL.Managers.ImportManager import ImportManager
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager
from src.DL.Model import Model
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session

CM = ConfigManager(unit_test=True)
model = Model()


class PenningMaatjeTestCase(unittest.TestCase):

    def test_TC00_Start(self):
        result = start_up(get_input_sub_dir('Bankafschriften - meerdere rekeningen'))
        self.assertTrue(result.OK)
        session = Session()
        result = start_db(build=True)
        self.assertTrue(result.OK)

        [session.db.clear(table) for table in model.DB_tables]

        IM = ImportManager()
        UM = UserCsvFileManager()
        UM.import_booking_related_user_defined_csv_files()
        IM.import_bank_transactions(session.db)
        IM.create_enriched_mutations(session.db)

    @staticmethod
    def test_TC01_Consistency():
        ConsM = ConsistencyManager()
        ConsM.run()


if __name__ == '__main__':
    unittest.main()
