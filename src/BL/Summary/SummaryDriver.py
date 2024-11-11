#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime

from src.BL.Managers.ExportManager import ExportManager
from src.BL.Summary.SearchResults import SearchResults
from src.DL.Config import CF_COMBO_SUMMARY
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.SQLOperator import SQLOperator
from src.DL.Enums.Enums import Summary
from src.DL.Lexicon import ANNUAL_ACCOUNT, SEARCH_RESULT
from src.DL.Model import FD
from src.DL.Table import Table
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

session = Session()


class SummaryDriver:

    def __init__(self):
        self._CM = ConfigManager()
        self._EM = ExportManager()
        self._search_results = SearchResults()
        self._result = Result()

    def create_summary(self, te_rows, summary_type=None, year=None) -> Result:
        summary_type = summary_type or self._CM.get_config_item(CF_COMBO_SUMMARY)

        # A. Search results
        if summary_type == Summary.SearchResult:
            return self._search_results.create_summary(te_rows, title=SEARCH_RESULT)

        # B. Annual account
        elif summary_type == Summary.AnnualAccount:
            self.produce_csv_files(ANNUAL_ACCOUNT, year, monthly=False, quarterly=False)

        # B. Annual account Plus
        elif summary_type == Summary.AnnualAccountPlus:
            self.produce_csv_files(ANNUAL_ACCOUNT, year)
        return self._result

    def produce_csv_files(self, template_name=None, year=None, monthly=True, quarterly=True):
        # Jaarrekening t/m maand x
        if template_name:
            self._result = self._EM.export(template_name=template_name, year=year)
            if not self._result.OK:
                raise GeneralException(self._result.get_messages_as_message())

        # Kwartalen, maanden
        [self._export_transactions(year, q=i) for i in range(1, 5) if monthly]
        [self._export_transactions(year, month_from=i, month_to=i) for i in range(1, 13) if quarterly]

    def _export_transactions(self, year, month_from=None, month_to=None, q=None):
        if q:
            month_from = ((q - 1) * 3) + 1
            month_to = month_from + 2

        where = [Att(FD.Year, year)]
        if month_from == month_to:
            title = f'{year} maand {month_from} transacties'
            where.extend([Att(FD.Month, month_from)])
        else:
            title = f'{year} Q{q} transacties'
            where.extend([
                Att(FD.Month, month_from, relation=SQLOperator().GE),
                Att(FD.Month, month_to, relation=SQLOperator().LE)]
            )
        te_rows = session.db.select(Table.TransactionEnriched, where=where)
        if te_rows:
            self._result = self._search_results.create_summary(te_rows, title=title)
            if not self._result.OK:
                raise GeneralException(self._result.get_messages_as_message())
