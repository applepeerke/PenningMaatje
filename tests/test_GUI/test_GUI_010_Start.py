import os
import unittest

from src.DL.DBDriver.DBDriver import DBDriver
from src.DL.Model import Model
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import APP_NAME
from src.GL.Functions import move_file
from src.GL.GeneralException import GeneralException

model = Model()
config_manager = ConfigManager(unit_test=True)
csvm = CsvManager()
db: DBDriver


class StartTestCase(unittest.TestCase):

    def _save_restore_file(self, mode, path, overwrite=True, from_must_exist=True):
        if mode == 'S':
            if from_must_exist:
                self.assertTrue(os.path.isfile(path))
            move_file(path, f'{path}#')
        elif mode == 'R':
            if not overwrite and os.path.isfile(path):
                return
            move_file(f'{path}#', path)

    def test_TC00_start_from_scratch(self):
        # Preparation:
        Session().start(unit_test=True)
        # First move old #-ones to normal files (just to be sure)
        self._save_restore_file('R', config_manager.get_path())
        self._save_restore_file('R', f'{Session().database_dir}{APP_NAME}.db')
        # - "Delete" by renaming to "#"-file
        self._save_restore_file('S', config_manager.get_path())
        self._save_restore_file('S', f'{Session().database_dir}{APP_NAME}.db', from_must_exist=False)

        # Start app
        try:
            from src.PenningMaatje import start
            start()
        except GeneralException:
            pass
        finally:
            # Finally move old #-ones to normal files
            self._save_restore_file('R', config_manager.get_path())


if __name__ == '__main__':
    unittest.main()
