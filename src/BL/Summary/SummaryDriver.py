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
from src.DL.Config import CF_COMBO_SUMMARY, CF_SUMMARY_YEAR
from src.DL.Enums.Enums import Summary
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.Enums import ActionCode
from src.GL.Result import Result


class SummaryDriver:

    def __init__(self):
        pass

    @staticmethod
    def create_summary(te_rows, summary_type=None, title=None) -> Result:
        """ summary_type and year is needed for unit test only
        @param summary_type: Summary type
        @param te_rows: Used in SearchResult.
        @param title: Needed in CLI mode.
        @return: Result OK|CN
        """
        CM = ConfigManager()
        summary_type = summary_type or CM.get_config_item(CF_COMBO_SUMMARY)

        # A. Search results
        if summary_type == Summary.SearchResult:
            return SearchResults().create_summary(te_rows, title=title)

        # B. Annual account
        elif summary_type == Summary.AnnualAccount:
            EM = ExportManager()
            year = CM.get_config_item(CF_SUMMARY_YEAR) or datetime.now().year
            return EM.export(year=year)
