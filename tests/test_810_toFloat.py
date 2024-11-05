#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import unittest

from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException


class ToFloatTestCase(unittest.TestCase):

    def test_TC01_ToFloat(self):
        self.assertTrue(toFloat('') == 0)
        self.assertTrue(toFloat('0') == 0)
        self.assertTrue(toFloat(',0') == 0)
        self.assertTrue(toFloat(',', strict=False) == 0)
        self.assertTrue(toFloat('1') == 1)
        self.assertTrue(toFloat('1,0') == 1)
        self.assertTrue(toFloat('1,00') == 1.00)
        self.assertTrue(toFloat('1,1') == 1.1)
        self.assertTrue(toFloat('1,12') == 1.12)
        self.assertTrue(toFloat('01,12') == 1.12)
        # Minus
        self.assertTrue(toFloat('-1') == -1)
        # Decimals
        self.assertTrue(toFloat('1.000,00') == 1000.00)
        self.assertTrue(toFloat('-12.345.678,90') == -12345678.90)

        # Comma = '.'
        self.assertTrue(toFloat('.0', comma_source='.') == 0)
        self.assertTrue(toFloat('.', comma_source='.', strict=False) == 0)
        self.assertTrue(toFloat('1', comma_source='.') == 1)
        self.assertTrue(toFloat('1.0', comma_source='.') == 1)
        self.assertTrue(toFloat('1.00', comma_source='.') == 1.00)
        self.assertTrue(toFloat('1.1', comma_source='.') == 1.1)
        self.assertTrue(toFloat('1.12', comma_source='.') == 1.12)
        self.assertTrue(toFloat('01.12', comma_source='.') == 1.12)
        # Minus
        self.assertTrue(toFloat('-1.00', comma_source='.') == -1)
        # Decimals
        self.assertTrue(toFloat('1,000.00', comma_source='.') == 1000.00)
        self.assertTrue(toFloat('-12,345,678.90', comma_source='.') == -12345678.90)

        # Exceptions
        self.assertRaises(GeneralException, toFloat, '1234567.89', ',')
        self.assertRaises(GeneralException, toFloat, '1234567,89', '.')
        self.assertRaises(GeneralException, toFloat, '1234.567,0', ',')
        self.assertRaises(GeneralException, toFloat, '1234.567,89', ',')
        self.assertRaises(GeneralException, toFloat, '12.34.567,89', ',')


if __name__ == '__main__':
    unittest.main()
