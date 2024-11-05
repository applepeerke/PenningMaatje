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
from src.GL.Functions import FloatToStr
from src.GL.GeneralException import GeneralException


class FormatHelpersTestCase(unittest.TestCase):

    def test_TC01_Format_amount(self):
        # Default is justify right, width=15, comma_source=".", comma_target=",".
        self.assertTrue(FloatToStr('0', justify='R') == '           0,00')
        self.assertTrue(FloatToStr(',0', justify='R') == '           0,00')
        self.assertTrue(FloatToStr(',', justify='R') == ',')
        self.assertTrue(FloatToStr('1', justify='R') == '           1,00')
        self.assertTrue(FloatToStr('1.0', justify='R') == '           1,00')
        self.assertTrue(FloatToStr('1,0', justify='R', comma_source=',') == '           1,00')
        self.assertTrue(FloatToStr('1,00', justify='R', comma_source=',') == '           1,00')
        self.assertTrue(FloatToStr('1.1', justify='R') == '           1,10')
        self.assertTrue(FloatToStr('1.12', justify='R') == '           1,12')
        self.assertTrue(FloatToStr('01.12', justify='R') == '           1,12')
        # Minus
        self.assertTrue(FloatToStr('-1', justify='R') == '          -1,00')
        # No pad
        self.assertTrue(FloatToStr('-1', justify=EMPTY) == '-1,00')
        # Decimals
        self.assertTrue(FloatToStr('1,000', justify=EMPTY) == '1.000,00')
        self.assertTrue(FloatToStr('-12345678.90', justify='R') == ' -12.345.678,90')
        # Comma representation
        self.assertTrue(FloatToStr('0', justify=EMPTY, comma_target='.') == '0.00')
        self.assertTrue(FloatToStr('100', justify=EMPTY, comma_source=',', comma_target=',') == '100,00')
        self.assertTrue(FloatToStr('1.000', justify=EMPTY, comma_source=',', comma_target=',') == '1.000,00')
        self.assertTrue(FloatToStr('1.000,00', justify=EMPTY, comma_source=',', comma_target='.') == '1,000.00')
        self.assertTrue(FloatToStr('1,000.00', justify=EMPTY, comma_source='.', comma_target='.') == '1,000.00')
        self.assertTrue(FloatToStr('1,000.00', justify=EMPTY, comma_source='.', comma_target=',') == '1.000,00')
        # Exceptions
        self.assertTrue(FloatToStr(EMPTY) == EMPTY)
        # invalid (too many decimals), returns appx. input.
        self.assertTrue(FloatToStr('.123', justify=EMPTY, round_decimals=False) == '0,123')
        self.assertTrue(FloatToStr('1234567890', width=10, justify='R') == '1234567890')  # too big, returns input.
        args = ['123456789', '.', ',', True, 'R', 10]
        kwargs = {}
        self.assertRaises(GeneralException, FloatToStr, *args, **kwargs)


if __name__ == '__main__':
    unittest.main()
