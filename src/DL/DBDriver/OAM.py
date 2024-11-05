from .Att import Att
from .Const import EMPTY
from .DBException import DBException
from .Enums import IOStatus
from ..Model import Model, FD
from .DBSession import Singleton as DBSession

model = Model()
PGM = 'OAM'


class OAM(object):
    @property
    def status(self):
        return self._io_status

    @property
    def error_message(self):
        return self._error_message

    """
    Transforms **kwargs to rows and handles CRUD with rows.
    """

    def __init__(self, table_name, **kwargs):
        if not table_name:
            raise DBException(f'{__name__}.__init__: Missing required input.')
        self._table_name = table_name

        # DB driver must have been started.
        if not DBSession().driver:
            raise DBException(f'{__name__}.__init__: DB driver does not exist yet.')
        self._db = DBSession().driver

        # PK must be retrieved
        self._pk = self._get_pk(**kwargs)
        if not self._pk:
            raise DBException(f'{__name__}.__init__: PK could not be retrieved.')

        self._ID = 0
        self._made_changes = False
        self._io_status = IOStatus.OK
        self._error_message = EMPTY
        self._row = model.row_from_kwargs(table_name, **kwargs)

    """
    Mappings
    """

    def insert(self):
        """
        Insert row in database (default: pk)
        """
        self._io_status = IOStatus.OK
        # Check for existing PK.
        if self._db.fetch(self._table_name, where=self._pk):
            self._set_error(IOStatus.VE, f'Record to be inserted already exists with PK="{self._pk}".')
            return
        # Insert
        self._ID = self._db.insert(self._row)
        self._made_changes = True

    def update(self, **kwargs):
        """
        Update row in database (first check on changes)
        return: ID
        """
        self._io_status = IOStatus.OK
        # Get existing record
        existing_kwargs = model.row_to_kwargs(self._table_name, self._row) if self._fetch_init() else {}
        if not existing_kwargs:
            self._set_error(IOStatus.VE, 'Record to be updated does not exist.')
            return

        # Check if any value has been changed
        if any(value != existing_kwargs[name] for name, value in kwargs.items()):
            values = [Att(k, v) for k, v in kwargs.items()]
            self._db.update(self._table_name, where=self._pk, values=values)

    def fetch(self) -> dict:
        """ return: row as att_names """
        return model.row_to_att_names(self._table_name, self._row) if self._fetch_init() else {}

    def _fetch_init(self) -> dict:
        """ Fetch row in database. Reset made_changes flag. """
        self._io_status = IOStatus.OK
        row = self._db.fetch_one(self._table_name, where=self._pk)
        if not row:
            return {}
        self._ID = row[0]
        self._row = row[1:]
        self._made_changes = False  # Reset

    def delete(self):
        """
        Delete row in database (default: pk)
        """
        self._io_status = IOStatus.OK
        self._db.delete(self._table_name, where=self._pk)
        self._made_changes = True

    """
    Private methods
    """

    def _get_pk(self, **kwargs) -> list:
        if FD.ID in kwargs:
            return [Att(FD.ID, value=kwargs[FD.ID])]
        return model.pk_from_kwargs(self._table_name, **kwargs)

    def _set_error(self, status, message):
        self._io_status = status
        if not self._error_message:
            self._error_message = f'{__name__}: {message}'
