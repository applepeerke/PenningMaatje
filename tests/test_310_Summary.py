#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from src.BL.Summary.SummaryDriver import SummaryDriver
from src.DL.Config import *
from src.DL.Enums.Enums import Summary
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from tests.Functions import start_up, get_input_sub_dir

CM = ConfigManager(unit_test=True)
model = Model()


class SearchTestCase(unittest.TestCase):

    def test_TC01_StartUp(self):
        result = start_up(input_dir=get_input_sub_dir('Bankafschriften'), build=True)
        self.assertTrue(result.OK)

    def test_TC02_Summary(self):
        result = start_up(input_dir=get_input_sub_dir('Bankafschriften'), build=True)
        self.assertTrue(result.OK)
        te_rows = Session().db.select(Table.TransactionEnriched)
        year = model.get_value(Table.TransactionEnriched, FD.Year, te_rows[0])
        CM.set_config_item(CF_SUMMARY_YEAR, year)
        CM.set_config_item(CF_SUMMARY_MONTH_FROM, 1)
        CM.set_config_item(CF_SUMMARY_MONTH_TO, 12)
        for summary_type in Summary.values():
            result = SummaryDriver().create_summary(summary_type, te_rows)
            self.assertTrue(
                result.OK or result.WA,
                msg=f'Error at summary "{summary_type}" for year "{year}": {result.get_messages_as_message()}')


if __name__ == '__main__':
    unittest.main()
