#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from src.GL.Const import EMPTY
from src.GL.Functions import get_date_format


class FormatHelpersTestCase(unittest.TestCase):

    def test_TC01_Get_date_format(self):
        # A. Invalid
        # - Must be specified
        self.assertIsNone(get_date_format(EMPTY))
        # - Must be 8 or 10 long
        self.assertIsNone(get_date_format('121222'))
        self.assertIsNone(get_date_format('012-12-2022'))
        # - Must have 2 separators if 10 long at dedicated places
        self.assertIsNone(get_date_format('2022012022'))
        self.assertIsNone(get_date_format('2022-10222'))
        self.assertIsNone(get_date_format('2022--0222'))
        self.assertIsNone(get_date_format('2022-0--22'))
        self.assertIsNone(get_date_format('20220222--'))
        #   - Must have 0 separators if 8 long
        self.assertIsNone(get_date_format('2-2-2022'))
        self.assertIsNone(get_date_format('2-02-2022'))
        self.assertIsNone(get_date_format('02022022', allow_MDY=True))
        # - Edges
        self.assertIsNone(get_date_format('2022-22-01'))  # YDM not supported
        self.assertIsNone(get_date_format('02-22-2022'))  # MDY not supported
        self.assertIsNone(get_date_format('02-02-2022',  allow_MDY=True))   # Can be DMY or MDY
        self.assertIsNone(get_date_format('20223001'))  # YDM not supported
        self.assertIsNone(get_date_format('20022022'))  # Where is the year?
        # B. Valid
        #  -10 long
        self.assertTrue(get_date_format('22-02-2022') == 'DMY')
        self.assertTrue(get_date_format('2022-02-22') == 'YMD')
        self.assertTrue(get_date_format('02-02-2022') == 'DMY')
        self.assertTrue(get_date_format('02-22-2022', allow_MDY=True) == 'MDY')  # MDY supported
        #   -- Edges
        self.assertTrue(get_date_format('2012-12-12') == 'YMD')
        self.assertTrue(get_date_format('12-12-2012') == 'DMY')
        #  - 8 long
        # ToDo: commented out should work too
        # self.assertTrue(get_date_format('30022022') == 'DMY')
        self.assertTrue(get_date_format('20220222') == 'YMD')
        # self.assertTrue(get_date_format('02302022', allow_MDY=True) == 'MDY')
        self.assertTrue(get_date_format('02022022') == 'DMY')
        #   -- Edges
        self.assertTrue(get_date_format('20121212') == 'YMD')
        self.assertTrue(get_date_format('12122012') == 'DMY')
        self.assertTrue(get_date_format('20181219') == 'YMD')
        self.assertTrue(get_date_format('20220101') == 'YMD')  # YDM not supported


if __name__ == '__main__':
    unittest.main()
