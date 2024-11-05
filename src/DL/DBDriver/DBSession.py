class Singleton:
    """ Singleton """

    class DB:
        """Implementation of Singleton interface """

        @property
        def driver(self):
            return self._driver

        @driver.setter
        def driver(self, value):
            self._driver = value

        def __init__(self):
            self._driver = None

    # ---------------------------------------------------------------------------------------------------------------------
    # Singleton logic
    # ---------------------------------------------------------------------------------------------------------------------

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.DB()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
