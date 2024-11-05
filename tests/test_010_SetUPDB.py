import unittest

from src.DL.DBDriver import DBDriver
from src.DL.DBInitialize import DBInitialize
from src.DL.Model import *
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Enums import LogLevel

session = Session()
session.start(unit_test=True)
model = Model()
config_manager = ConfigManager(unit_test=True)
csvm = CsvManager()
db: DBDriver


class SetupDBTestCase(unittest.TestCase):

    def test_TC00_start_log(self):
        log = Log()
        log.start_log(Session().log_dir, level=LogLevel.Verbose)
        self.assertTrue(log.log_level == LogLevel.Verbose)

    def test_TC01_Setup_db(self):
        result = DBInitialize().start(build=True)
        self.assertTrue(result.OK, msg=result.text)


if __name__ == '__main__':
    unittest.main()
