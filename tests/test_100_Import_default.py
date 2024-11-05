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


class ImportDefaultTestCase(unittest.TestCase):

    def test_TC01_Build(self):
        result = start_up(get_input_sub_dir('Bankafschriften - meerdere rekeningen'), build=True, auto_continue=True)
        self.assertTrue(result.OK)


if __name__ == '__main__':
    unittest.main()
