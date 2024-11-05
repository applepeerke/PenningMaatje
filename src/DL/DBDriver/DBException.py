class DBException(Exception):

    def __init__(self, message):
        super().__init__(message)
