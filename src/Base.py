from src.DL.Config import CF_OUTPUT_DIR
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.SessionManager import Singleton as Session

PGM = 'Base'

CM = ConfigManager()
session = Session()

"""
Purpose: Provide Session and Configuration
"""

class Base:
    @property
    def session(self):
        return self._session

    @property
    def CM(self):
        return self._CM

    def __init__(self):
        self._CM = CM
        self._CM.start_config()
        self._session = session
        self._session.start(self._CM.get_config_item(CF_OUTPUT_DIR), unit_test=self._CM.unit_test)
