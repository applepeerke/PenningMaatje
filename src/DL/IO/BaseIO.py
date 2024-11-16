from src.DL.DBDriver.Att import Att
from src.DL.Model import Model, FD
from src.VL.Data.Constants.Enums import BoxCommand
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY, UNKNOWN
from src.GL.Enums import Mutation, MessageSeverity, ActionCode
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result

PGM = 'BaseIO'


class BaseIO:
    @property
    def result(self):
        return self._result

    def __init__(self, table_name):
        self._result = Result()
        self._table_name = table_name
        self._object = None
        self._object_old = None
        self._model = Model()
        self._session = Session()
        if not self._session.CLI_mode:
            from src.VL.Views.PopUps.PopUp import PopUp
            self._dialog = PopUp()
        self._db = self._session.db
        self._mode = EMPTY
        self._row = []

    def edit(self, model) -> Result:
        self._result = Result()
        self._object = model.object
        self._object_old = model.object_old
        # Go!
        pk_current = self._get_pk(self._object_old)

        if model.command == BoxCommand.Add:
            self._db.insert(self._table_name, self._obj_to_row(Mutation.Create, self._object), pgm=PGM)
            self._set_changed_flag(Mutation.Create)

        elif model.command == BoxCommand.Update:
            self._db.update(self._table_name, where=pk_current, values=self._get_all_values(), pgm=PGM)
            self._set_changed_flag(Mutation.Update)

        elif model.command == BoxCommand.Delete:
            self.delete(pk_current)
            self._set_changed_flag(Mutation.Delete)

        elif model.command == BoxCommand.Rename:
            Id_old = self._db.fetch_id(self._table_name, where=pk_current)
            Id_new = self._db.fetch_id(self._table_name, where=self._get_pk(self._object))
            # Replace?
            if 0 < Id_old != Id_new and Id_new > 0:
                if self._dialog and not self._dialog.confirm(
                        popup_key=f'{PGM}.rename', text='Bestand bestaat al. Vervangen?'):
                    return Result(action_code=ActionCode.Cancel)
                # Delete existing one
                self.delete(pk_current)
            # Update including pk
            self._db.update(
                self._table_name,
                where=pk_current,
                values=self._get_all_values(),
                pgm=PGM)
            self._set_changed_flag(Mutation.Create)
        return self._result

    def _get_all_values(self):
        raise NotImplementedError(f'{PGM}: Method "_get_all_values" is not implemented.')

    """ ? """

    def has_changed(self, obj, where) -> int:
        """
        Has an object attribute changed with respect to the record in the database?
        @return: Id=record changed, 0=not changed, -1=not found
        """
        # - Record exists?
        if not obj or not where:
            return -1
        row = self._db.fetch_one(self._table_name, where=where)
        if not row or isinstance(row[0], list):
            return -1
        # Has something changed?
        obj_prv = self.row_to_obj(row)
        if any(str(att.value) != str(obj_prv.attributes[att.name].value) for att in obj.attributes.values()):
            return row[0]
        return 0

    """ C """

    def insert(self, obj):
        where = None
        self._insert(obj, where, pgm=PGM)

    def _insert(self, obj, where=None, pgm=PGM) -> bool:
        """ Avoid duplicates """
        ID = self._db.fetch_id(self._table_name, where=where or self._obj_to_row(Mutation.Read, obj))
        if ID > 0:
            return False
        ID = self._db.insert(self._table_name, self._obj_to_row(Mutation.Create, obj), pgm=pgm)
        if ID > 0:
            self._set_changed_flag(Mutation.Create)
        return ID > 0

    def _chkins(self, obj, where, pgm=PGM) -> bool:
        ID = self._db.fetch_id(self._table_name, where=where)
        if ID <= 0:
            ID = self._db.insert(self._table_name, self._obj_to_row(Mutation.Create, obj), pgm=pgm)
            self._set_changed_flag(Mutation.Create)
        return ID > 0

    """ R """

    def fetch(self, where):
        row = self._db.fetch_one(self._table_name, where=where)
        return self.row_to_obj(row)

    def count(self, where=None) -> int:
        return self._db.count(self._table_name, where=where)

    def select(self, where=None):
        rows = self._db.select(self._table_name, where=where)
        return [self.row_to_obj(row) for row in rows]

    def id_to_obj(self, Id=0):
        return self.row_to_obj(self._id_to_row(Id))

    def _id_to_row(self, Id=0) -> list:
        return self._db.fetch_one(table_name=self._table_name, where=[Att(FD.ID, value=Id)])

    """ U """

    def update(self, obj, where, pgm=PGM) -> bool:
        self._result = Result()
        # Validate
        Id = self.has_changed(obj, where)
        if Id == -1:  # No valid record found
            return False
        if Id == 0:  # Nothing changed
            self._result.add_message(
                'Er is niets gewijzigd. De gegevens bestaan al.', severity=MessageSeverity.Warning)
            return False
        # Try to update
        if not self._db.update(
                self._table_name, self._obj_to_row(Mutation.Update, obj), where=[Att(FD.ID, Id)], pgm=pgm):
            return False
        # - Success
        self._set_changed_flag(Mutation.Update)
        return True

    def _updert(self, obj, where, pgm=PGM) -> bool:
        # Update
        if self.update(obj, where, pgm):
            return True
        elif not self._result.OK:  # Nothing changed
            return False
        # Create
        ID = self._db.insert(self._table_name, self._obj_to_row(Mutation.Create, obj), pgm=pgm)
        if ID > 0:
            self._set_changed_flag(Mutation.Create)
        return ID > 0

    """ D """

    def delete(self, where: [Att]) -> int:
        if not where:
            return 0
        result = self._db.delete(self._table_name, where=where)
        if result:
            self._set_changed_flag(Mutation.Delete)
        return result

    """
    General
    """
    def _set_changed_flag(self, mode):
        self._session.set_user_table_changed(self._table_name)
        text = UNKNOWN
        if mode == Mutation.Create:
            text = 'toegevoegd'
        elif mode == Mutation.Delete:
            text = 'verwijderd'
        elif mode == Mutation.Update:
            text = 'gewijzigd'
        self._result.add_message(
            f'Gegevens zijn {text}.', severity=MessageSeverity.Completion, log_message=False)

    @staticmethod
    def row_to_obj(row):
        raise NotImplementedError(f'{PGM}: Method "_row_to_obj" is not implemented.')

    def _obj_to_row(self, mode: Mutation, obj) -> list:
        """
        Insert: Values
        Update: Attributes
        """
        self._mode = mode
        self._row = []
        self._att_names = []
        ob_dict = self._model.get_colno_per_att_name(self._table_name)
        for name in ob_dict:
            if name == FD.Active:
                self._append_to_row(name, obj.active)
            elif name == FD.Amount:
                self._append_to_row(name, obj.amount)
            elif name == FD.Amount_budget_this_year:
                self._append_to_row(name, obj.amount_budget_this_year)
            elif name == FD.Amount_budget_previous_year:
                self._append_to_row(name, obj.amount_budget_previous_year)
            elif name == FD.Amount_monthly:
                self._append_to_row(name, obj.amount_monthly)
            elif name == FD.Amount_realisation:
                self._append_to_row(name, obj.amount_realisation)
            elif name == FD.Amount_signed:
                self._append_to_row(name, obj.amount_signed)
            elif name == FD.Amount_yearly:
                self._append_to_row(name, obj.amount_yearly)
            elif name == FD.Bban:
                self._append_to_row(name, obj.bban)
            elif name == FD.Booking_code:
                self._append_to_row(name, obj.booking_code)
            elif name == FD.Booking_id:
                self._append_to_row(name, obj.booking_id)
            elif name == FD.Booking_maingroup:
                self._append_to_row(name, obj.booking_maingroup)
            elif name == FD.Booking_subgroup:
                self._append_to_row(name, obj.booking_subgroup)
            elif name == FD.Booking_type:
                self._append_to_row(name, obj.booking_type)
            elif name == FD.Counter_account_number:
                self._append_to_row(name, obj.counter_account_number)
            elif name == FD.Description:
                self._append_to_row(name, obj.description)
            elif name == FD.FirstComment:
                self._append_to_row(name, obj.first_comment)
            elif name == FD.Iban:
                self._append_to_row(name, obj.iban)
            elif name == FD.Name:
                self._append_to_row(name, obj.name)
            elif name == FD.Opening_balance:
                self._append_to_row(name, obj.opening_balance)
            elif name == FD.Protected:
                self._append_to_row(name, obj.protected)
            elif name == FD.SearchTerm:
                self._append_to_row(name, obj.search_term)
            elif name == FD.SeqNo:
                self._append_to_row(name, obj.seqno)
            elif name == FD.Year:
                self._append_to_row(name, obj.year)

        self._check_definition(ob_dict)
        return self._row

    def _append_to_row(self, name, value):
        self._att_names.append(name)
        value = Att(name, value) if self._mode != Mutation.Create else value
        self._row.append(value)

    def _check_definition(self, ob_dict):
        if len(self._row) != len(ob_dict):
            missing_names = ', '.join([k for k in ob_dict if k not in self._att_names])
            raise GeneralException(
                f'{PGM}: Ongeldige definitie voor "{self._table_name}". '
                f'Waarschijnlijk is een veld nog niet aan de "_to_row" lijst toegevoegd.\n'
                f'Ontbrekende attributen zijn: "{missing_names}"')

    @staticmethod
    def _get_pk(obj) -> list:
        pass

    def are_all_equal(self, objects_a: list, objects_b: list) -> bool:
        if not objects_a and not objects_b:
            return True
        if len(objects_a) != len(objects_b):
            return False
        for obj_a in objects_a:
            if not any(self._is_equal(obj_a, obj_b) for obj_b in objects_b):
                return False
        return True

    @staticmethod
    def _is_equal(obj_a, obj_b):
        return all(att.value == obj_b.attributes[att.name].value for att in obj_a.attributes.values()
                   if att.in_db is True)
