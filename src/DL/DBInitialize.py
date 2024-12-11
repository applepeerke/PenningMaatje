from src.Base import Base
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.DBDriver import DBDriver
from src.DL.Lexicon import TRANSACTIONS
from src.DL.Model import Model, FD
from src.GL.Const import APP_NAME, FFD, EMPTY
from src.GL.Enums import ResultCode, MessageSeverity as Sev, Color, ActionCode
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'DBInitialize'
model = Model()

class DBInitialize(Base):

    def __init__(self):
        super().__init__()
        self._db = None
        self._result = Result()

    def start(self, build=False) -> Result:
        self._result = Result()

        # Connect
        self._connect(self._session.database_dir)
        if not self._result.OK:
            return self._result

        if build:
            self._build()

        # Store in session
        self._session.db = self._db

        # Check consistency
        if not self.is_consistent():
            if not build:
                self._result.text = (
                    f'De database moet (opnieuw) opgebouwd worden.\n\n'
                    f'Alle gegevens in de database gaan hierbij verloren,\n'
                    f'maar worden hersteld bij het importeren van je {TRANSACTIONS}.\n\n'
                    f'Database opbouwen?\n')
                self._result.code = ResultCode.Error
                self._result.action_code = ActionCode.Retry
        return self._result

    def is_consistent(self) -> bool:
        error_tables = set()

        # Check if all tables exist
        for table_name in model.DB_tables:
            if not self._db.get_table_description(table_name, check_only=True):
                error_tables.add(table_name)
                self._result.add_message(
                    f'Tabel {table_name} bestaat niet in de database.', Sev.Error)

        # Check if FFD in db corresponds with model definition
        for table_name in model.DB_tables:
            ffd_atts = self._db.select(FFD, name=FD.FF_AttName, where=[
                Att(FD.FF_TableName, value=table_name)])
            # Check if all model attributes are present in the FFD
            db_att_names = model.get_att_names(table_name)
            for att_name in db_att_names:
                if att_name not in ffd_atts:
                    error_tables.add(table_name)
                    self._result.add_message(
                        f'Table {table_name} attribute {att_name} does not exist in the table FFD.', Sev.Error)

            # Check if all FFD attributes are present in the model (deleted attribute)
            for ffd_att_name in ffd_atts:
                if ffd_att_name not in db_att_names:
                    error_tables.add(table_name)
                    self._result.add_message(
                        f'FFD attribute "{ffd_att_name}" does not exist in table {table_name}.', Sev.Error)

            # Check if all FFD attributes are present in physical file
            schema = self._db.get_table_description(table_name, check_only=True)
            if not schema:
                error_tables.add(table_name)
                self._result.add_message(
                    f'Table "{table_name}" does not exist in the database.', Sev.Error)
            else:
                if len(schema) - 7 != len(ffd_atts):  # Minus "Id" and "audit data"
                    error_tables.add(table_name)
                    self._result.add_message(
                        f'Physical table length minus Id and Audit ({len(schema) - 7}) '
                        f'is not equal to FFD definition ({len(ffd_atts)}).', Sev.Error)

                schema_atts = [n[0] for n in schema]
                # Check if all FFD attributes are present in physical file
                for ffd_att_name in ffd_atts:
                    if ffd_att_name not in schema_atts:
                        error_tables.add(table_name)
                        self._result.add_message(
                            f'FFD attribute "{ffd_att_name}" does not exist in the physical table {table_name}.',
                            Sev.Error)

                # Check if all physical file attributes are present in FFD
                for schema_name in schema_atts[1:-6]:
                    if schema_name not in ffd_atts:
                        error_tables.add(table_name)
                        self._result.add_message(
                            f'Schema attribute "{schema_name}" does not exist in FFD table {table_name}.', Sev.Error)
        # Completion
        if error_tables:
            plur = 's' if len(error_tables) > 1 else EMPTY
            verb = 'are' if len(error_tables) > 1 else 'is'
            self._result.add_message(f'Table{plur} {verb} inconsistent with the model: '
                                     f'\n{", ".join(error_tables)}')
            return False

        self._result.text = 'Database is consistent.'
        return True

    def _connect(self, db_dir=None, db_name=APP_NAME):

        # Validate
        if not self._session:
            self._result.add_message(f'{PGM}: Er is nog geen sessie.', Sev.Error)
            return

        if not db_dir:
            self._result.add_message(f'{PGM}: Er is nog geen database folder gespecificeerd.', Sev.Error)
            return

        # Get the driver
        try:
            self._db = DBDriver(f'{db_dir}{db_name}.db')
            if not self._db:
                self._result.add_message(f'{PGM}: Database driver kon niet gestart worden.', Sev.Error)
                return
        except GeneralException as e:
            self._result.add_message(f'{PGM}: Database error: "{e.message}".', Sev.Error)
            return

        # Set driver in session
        self._session.db_name = f'{db_name}.db'
        return

    def _build(self):
        self._result.add_message(f'Build is gestart for tabellen "{", ".join(model.DB_tables)}".')
        # Build
        for table_name in model.DB_tables:
            try:
                self._db.drop_table(table_name)
                self._db_create_table_from_model(self._db, table_name)
            except GeneralException:
                self._result.add_message(
                    f'{PGM}: Tabel "{table_name}" kon {Color.RED}NIET{Color.NC} worden gemaakt.', Sev.Error)
        # OK: Clear messages.
        if self._result.OK:
            self._result.add_message(
                f'Build is {Color.GREEN}OK{Color.NC}. De tabellen zijn verwijderd en opnieuw gemaakt.')
            self._result = Result()

    @staticmethod
    def _db_create_table_from_model(db, table_name):
        """ Skip the non_db attributes """
        row_def = {colno: att for colno, att in model.get_db_definition(table_name).items()}
        db.create_table(table_name, row_def, index_def=model.get_indexes(table_name))
