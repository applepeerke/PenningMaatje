# Author      : Peter Heijligers
# Description : Audit
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2020-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import getpass

from .Const import NC, MANY, PGM
from .Att import *
from .Enums import TransactionMode
from .Functions import quote

Datetime_creation = 'Datetime_creation'
Program_creation = 'Program_creation'
User_creation = 'User_creation'
Datetime_mutation = 'Datetime_mutation'
Program_mutation = 'Program_mutation'
User_mutation = 'User_mutation'

AUDIT_NAMES = [Datetime_creation, Program_creation, User_creation,
               Datetime_mutation, Program_mutation, User_mutation]

AUDIT_NONE = 'AUDIT_NONE'
AUDIT_ALL = 'AUDIT_ALL'
AUDIT_CREATION = 'AUDIT_CREATION'
AUDIT_PRIVATE = 'AUDIT_PRIVATE'
AUDIT_CREATION_PRIVATE = 'AUDIT_CREATION_PRIVATE'
AUDIT_DEF = {
    AUDIT_NONE: [],
    AUDIT_ALL: [
        Datetime_creation, Program_creation, User_creation, Datetime_mutation, Program_mutation, User_mutation],
    AUDIT_CREATION: [Datetime_creation, Program_creation, User_creation],
    AUDIT_PRIVATE: [Datetime_creation, Program_creation, Datetime_mutation, Program_mutation],
    AUDIT_CREATION_PRIVATE: [Datetime_creation, Program_creation],
}


def get_audit_names_from_schema_names(schema_att_names):
    return [a for a in schema_att_names if a in AUDIT_DEF[AUDIT_ALL]]


def get_audit_type_from_schema(schema_att_names):
    schema_audit_names = get_audit_names_from_schema_names(schema_att_names)
    if schema_audit_names:
        for audit_type, audit_names in AUDIT_DEF.items():
            if len(schema_audit_names) == len(audit_names) and all(s in audit_names for s in schema_audit_names):
                return audit_type
    return AUDIT_NONE


def get_audit_values_from_row(row, audit) -> list:
    """ Unit test: Get audit values from the row """
    count = len(AUDIT_DEF.get(audit, []))
    return row[len(row) - count:] if len(row) > count else []


class Audit(object):

    def __init__(self):
        pass

    def get_audit_atts(self, audit_names, mutation_mode, pgm=__name__) -> [Att]:
        """ Get audit data in attributes """
        return [self._get_att(a, mutation_mode, pgm) for a in audit_names]

    def get_audit_values(self, audit_names, add_quotes=True, **kwargs) -> list:
        """ Get list of audit values """
        many = kwargs.get(MANY) is True
        pgm = kwargs.get(PGM) or __name__
        atts = [self._get_att(a, pgm=pgm) for a in audit_names]
        if many:
            return ['?' for _ in atts]
        else:
            if add_quotes:
                return [quote(a.value) for a in atts]
            else:
                return [a.value for a in atts]

    def add_audit_values(self, audit_names, rows, pgm):
        """ Add audit values to rows """
        if not audit_names:
            return rows
        out_rows = []
        for row in rows:
            row.extend(self.get_audit_values(audit_names, add_quotes=False, pgm=pgm))
            out_rows.append(row)
        return out_rows

    def add_audit_def(self, audit_names, table_def) -> dict:
        """ Add audit atts to table definition dict """
        if not audit_names:
            return table_def
        row_def_audit = table_def.copy()
        audit_start = len(table_def) + 2  # colno is 1-based
        for i in range(len(audit_names)):
            row_def_audit[audit_start + i] = self._get_att(audit_names[i])
        return row_def_audit

    @staticmethod
    def remove_audit(audit_names, rows, include_id):
        if not audit_names:
            return rows
        rows_out = []
        if not rows or len(rows[0]) - len(audit_names) < 1:
            return rows_out

        col_qty = len(rows[0]) - len(audit_names)
        s = 0 if include_id else 1
        return [row[s:col_qty] for row in rows]

    @staticmethod
    def _get_att(att_name, mode=None, pgm=__name__) -> Att:
        """ Get an audit Att """
        if att_name == Datetime_creation:
            return Att(
                att_name,
                value=str(datetime.datetime.now().isoformat() if not mode or mode == TransactionMode.C else NC),
                type=AttType.Timestamp)

        elif att_name == User_creation:
            return Att(att_name, getpass.getuser() if not mode or mode == TransactionMode.C else NC)

        elif att_name == Program_creation:
            return Att(att_name, pgm if not mode or mode == TransactionMode.C else NC)

        elif att_name == Datetime_mutation:
            return Att(
                att_name,
                value=str(datetime.datetime.now().isoformat() if mode == TransactionMode.U else 0),
                type=AttType.Timestamp)

        elif att_name == User_mutation:
            return Att(att_name, getpass.getuser() if mode == TransactionMode.U else EMPTY)

        elif att_name == Program_mutation:
            return Att(att_name, pgm if mode == TransactionMode.U else EMPTY)
