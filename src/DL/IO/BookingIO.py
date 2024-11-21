from src.DL.DBDriver.Att import Att
from src.DL.IO.BaseIO import BaseIO
from src.DL.Model import FD, Model
from src.DL.Objects.Booking import Booking
from src.DL.Table import Table
from src.VL.Data.Constants.Const import PROTECTED_BOOKINGS
from src.VL.Data.Constants.Enums import BoxCommand
from src.DL.Lexicon import TRANSACTIONS, BOOKING_CODE
from src.VL.Models.BookingCodeModel import BookingCodeModel
from src.GL.Const import EMPTY, MUTATION_PGM_BC
from src.GL.Enums import ActionCode, Mutation, ResultCode
from src.GL.Result import Result
from src.GL.Validate import toBool
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache

TABLE = Table.BookingCode
d = Model().get_colno_per_att_name(TABLE, zero_based=False)
PGM = MUTATION_PGM_BC

BCM = BookingCodeCache()


class BookingIO(BaseIO):

    def __init__(self):
        super().__init__(TABLE)
        self._result = Result()
        self._object = None
        self._object_old = None
        self._transaction_count = 0

    @staticmethod
    def row_to_obj(row) -> Booking:
        return Booking(
            booking_type=row[d[FD.Booking_type]],
            booking_maingroup=row[d[FD.Booking_maingroup]],
            booking_subgroup=row[d[FD.Booking_subgroup]],
            booking_code=row[d[FD.Booking_code]],
            seqno=row[d[FD.SeqNo]],
            protected=toBool(row[d[FD.Protected]]),
        ) if row else Booking()

    def insert(self, obj: Booking) -> Result:
        """ Avoid duplicates and set the protected ones """
        obj = self._set_protected(obj)
        self._updert(obj, where=obj.get_pk(), pgm=PGM)
        return self._result

    def update_by_id(self, obj: Booking, Id) -> bool:
        """ Avoid duplicates and set the protected ones """
        obj = self._set_protected(obj)
        return self.update(obj, where=[Att(FD.ID, Id)])

    def chkins(self, obj: Booking) -> Result:
        """ Avoid duplicates and set the protected ones """
        obj = self._set_protected(obj)
        self._chkins(obj, where=obj.get_pk(), pgm=PGM)
        return Result()

    def fetch_booking_codes(self, allow_empty=True) -> list:
        """ booking codes"""
        rows = self._db.select(table_name=TABLE, name=FD.Booking_code)
        unique_codes = {c for c in rows if c}
        if allow_empty:
            unique_codes.add(EMPTY)
        return list(unique_codes)

    @staticmethod
    def _set_protected(obj):
        if obj.booking_maingroup in PROTECTED_BOOKINGS:
            obj.protected = True
        return obj

    def get_last_seqno_for_type(self, type):
        """ To get the seqno for a protected 'other' booking. Should be the last one. """
        rows = self._db.select(table_name=TABLE, name=FD.SeqNo, where=[Att(FD.Booking_type, type)])
        return max(seqno for seqno in rows)

    def edit(self, model: BookingCodeModel) -> Result:
        self._result = Result()
        self._transaction_count = model.transaction_count
        self._object = model.object
        self._object_old = model.object_old

        # Go!
        pk_current = self._object_old.get_pk()
        pk_new = self._object.get_pk()

        result = self._validate(model.command)
        if not result.OK:
            return result

        if model.command == BoxCommand.Add:
            self._db.insert(TABLE, self._obj_to_row(Mutation.Create, self._object), pgm=PGM)
            self._set_changed_flag(Mutation.Create)

        elif model.command == BoxCommand.Update:
            # Warning
            if not self._confirm('gewijzigd'):
                return Result(action_code=ActionCode.Close)

            values = pk_new.copy()
            values.extend([
                Att(FD.Booking_code, self._object.booking_code),
                Att(FD.SeqNo, self._object.seqno)])
            self._db.update(TABLE, where=pk_current, values=values, pgm=PGM)
            self._set_changed_flag(Mutation.Update)

            # Update booking code in imported files
            if self._object.booking_code != self._object_old.booking_code:
                result = self._update_imported_files(pk_new)
                if not result.OK:
                    return result

        elif model.command == BoxCommand.Delete:
            # Warning
            if not self._confirm('verwijderd'):
                return Result(action_code=ActionCode.Close)

            # Clear booking Id in TransactionEnriched and CounterAccount
            Id = self._db.fetch_id(TABLE, where=pk_current)
            self._db.update(
                Table.TransactionEnriched,
                where=[Att(FD.Booking_id, Id)], values=[Att(FD.Booking_id, 0)], pgm=PGM)

            # Clear booking in imported files
            result = self._update_imported_files(pk_new=None)
            if not result.OK:
                return result

            self.delete(pk_current)
            self._set_changed_flag(Mutation.Delete)

        elif model.command == BoxCommand.Rename:
            if self._db.fetch_id(TABLE, where=pk_new):
                return Result(ResultCode.Error, f'Nieuwe boeking bestaat al.')
            self._db.update(TABLE, where=pk_current, values=pk_new, pgm=PGM)
            self._set_changed_flag(Mutation.Create)
        return self._result

    def _validate(self, command) -> Result:
        """ Protected bookings (other revenues/costs/overbookings) existence cannot be changed."""
        result = Result()
        if command in (BoxCommand.Delete, BoxCommand.Rename):
            if self._object_old.protected:
                result = Result(
                    ResultCode.Error, f'Type "{self._object_old.booking_type}" '
                                      f'hoofdgroep "{self._object_old.booking_maingroup}" is beschermd. '
                                      f'{command} is niet mogelijk.')
        if command in (BoxCommand.Update, BoxCommand.Add):
            if (self._object_old.booking_code != self._object.booking_code and
                    self._object.booking_code in BCM.booking_codes):
                result = Result(
                    ResultCode.Error, f'Nieuwe {BOOKING_CODE} bestaat al. {command} is niet mogelijk.')
        return result

    def _update_imported_files(self, pk_new=None) -> Result():
        """
        Update booking codes in imported files. Also, to EMPTY if it is a Delete.
            CounterAccount,
            SearchTerms
        """
        code_old = self._object_old.booking_code
        code_new = self._object.booking_code if pk_new else EMPTY

        # Update
        if code_old != code_new:
            where = [Att(FD.Booking_code, code_old)]
            values = [Att(FD.Booking_code, code_new)]

            self._db.update(Table.CounterAccount, where=where, values=values, pgm=PGM)
            self._db.update(Table.SearchTerm, where=where, values=values, pgm=PGM)
        return Result()

    def _confirm(self, action) -> bool:
        if self._transaction_count == 0:
            return True

        from src.VL.Views.PopUps.Dialog_with_transactions import DialogWithTransactions
        message = f'Er zijn {self._transaction_count} {TRANSACTIONS} aan {BOOKING_CODE} ' \
                  f'{self._object_old.booking_code} gekoppeld.\n' \
                  f'Deze koppelingen worden {action}.\n\n'
        Id = self._db.fetch_id(TABLE, where=self._object.get_pk())
        dialog = DialogWithTransactions(where=[Att(FD.Booking_id, Id)])
        return dialog.confirm(PGM, f'{message}\nDoorgaan?')
