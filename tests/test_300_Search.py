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
from src.DL.Config import *
from src.DL.DBDriver.Att import Att
from src.DL.Model import FD
from src.DL.Table import Table
from src.VL.Data.DataDriver import Singleton as DataDriver
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Const import EMPTY

CM = ConfigManager(unit_test=True)
DD = DataDriver()


def ini_config():
    CM.config_dict[CF_SEARCH_YEAR] = EMPTY
    CM.config_dict[CF_SEARCH_MONTH] = EMPTY
    CM.config_dict[CF_SEARCH_BOOKING_CODE] = EMPTY
    CM.config_dict[CF_SEARCH_COUNTER_ACCOUNT] = EMPTY
    CM.config_dict[CF_SEARCH_AMOUNT] = EMPTY
    CM.config_dict[CF_SEARCH_AMOUNT_TO] = EMPTY
    CM.config_dict[CF_SEARCH_TRANSACTION_CODE] = EMPTY
    CM.config_dict[CF_SEARCH_TEXT] = EMPTY


class SearchTestCase(unittest.TestCase):

    def test_TC01_StartUp(self):
        result = start_up(input_dir=get_input_sub_dir('Bankafschriften'), build=True)
        self.assertTrue(result.OK)

    def test_TC02_Search(self):
        global DD
        DD = DataDriver()
        DD.start()
        ini_config()
        self.assertTrue(self._search([Att(FD.Year, 2022)]) == 0)  # Only header row
        self.assertTrue(self._search([Att(FD.Year, 2018)]) == 2)
        self.assertTrue(self._search([Att(FD.Month, 12)]) == 2)
        self.assertTrue(self._search([Att(FD.Name, 'HOOGVLIET 701 1 DEN  HAAG NLD')]) == 1)
        self.assertTrue(self._search([Att(FD.Name, '%HOOGVLIET%')]) == 1)
        self.assertTrue(self._search([Att(FD.Name, 'HOOGVLIET%')]) == 1)
        self.assertTrue(self._search([Att(FD.Comments, '%020%')]) == 1)
        self.assertTrue(self._search([Att(FD.Amount, 3.49)]) == 1)

    @staticmethod
    def _search(where=None, table_name=Table.TransactionEnriched) -> int:
        rows = DD.fetch_set(table_name, where=where)
        return len(rows) - 1  # Without header row


if __name__ == '__main__':
    unittest.main()
