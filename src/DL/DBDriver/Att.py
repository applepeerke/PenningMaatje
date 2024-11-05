# ---------------------------------------------------------------------------------------------------------------------
# Attribute.py
#
# Author      : Peter Heijligers
# Description : DBDriver attribute
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2017-09-18 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------

import datetime

from .AttType import AttType
from .Const import EMPTY, TRUE, FALSE
from .SQLOperator import SQLOperator
from ...GL.Const import COMMA_DB, COMMA_SOURCE

oper = SQLOperator()


class Att(object):

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    @property
    def length(self):
        return self._length

    @property
    def description(self):
        return self._description

    @property
    def default(self):
        return self._default

    @property
    def colhdg_report(self):
        return self._colhdg_report

    @property
    def derived(self):
        return self._derived

    @property
    def relation(self):
        return self._relation

    @property
    def col_width(self):
        return self._col_width

    @property
    def seqno(self):
        return self._seqno

    @property
    def visible(self):
        return self._visible

    @property
    def optional(self):
        return self._optional

    @property
    def in_db(self):
        return self._in_db

    @property
    def user_representation(self):
        return self._user_representation
    """
    Setters
    """

    @value.setter
    def value(self, value):
        self._value = value
        self._set_user_representation()

    def __init__(
            self, name, value=EMPTY, type=AttType.Varchar, length=0, description=EMPTY, in_db=True, default=None,
            seqno=0, colhdg_report=None, derived=False, relation=oper.EQ, col_width=0, visible=True, optional=False):
        """

        :param name: Name
        :param value: Value
        :param type: Type
        :param length: Length
        :param description: Description (defaults to name.title())
        :param in_db: This attribute will appear in db (default True).
        :param default: Default value (if not set, will be set to default type)

        :param seqno: Seq. no. in a report
        :param colhdg_report: Column heading in a report (defaults to name)

        :param derived: Db derived
        :param relation: Db relation
        :param col_width: GUI table column width
        :param visible: GUI visible
        :param optional: Optional in e.g. csv to import in database.
        """
        self._name = name
        self._type = type
        self._length = length
        self._description = name.title() if description == EMPTY else description
        self._seqno = seqno
        self._colhdg_report = colhdg_report if colhdg_report else name
        self._derived = derived
        self._relation = relation
        self._col_width = col_width
        self._visible = visible
        self._optional = optional
        self._in_db = in_db
        self._user_representation = EMPTY
        self.value = value  # Also set user representation

        # Set the default
        if default is None:
            if type in AttType.sanitize_types:
                self._default = EMPTY
            elif type == AttType.Timestamp:
                self._default = datetime.date.min
            elif type in AttType.numeric_types:
                self._default = 0
            elif type == AttType.Bool:
                self._default = False
            else:
                self._default = None

        self.set_relation()

    def set_relation(self, relation=None):
        # Set relation LIKE
        if isinstance(self._value, str) and self._value and len(self._value) > 1 \
                and (self._value.startswith('%') or self._value.endswith('%')):
            self._relation = oper.LIKE
            return
        elif relation:
            self._relation = relation

    def _set_user_representation(self):
        """ Called from value setter """
        if self._type == AttType.Float:
            self._user_representation = self._float_to_amount()
        elif self._type == AttType.Bool:
            self._user_representation = TRUE if self.value is True else FALSE
        elif self._type in AttType.string_types:
            self._user_representation = self._value
        else:
            self._user_representation = str(self._value)

    def _float_to_amount(self) -> str:
        """ From float to user (view) amount representation"""
        amount = str(self._value)

        # Preparation
        # - Round decimals
        p_comma = amount.find(COMMA_DB)
        if p_comma > -1:
            decimal_part = amount[p_comma:]
            if len(decimal_part) > 3:
                amount = str(round(self._value, 2))

        decimal_point_source = '.' if COMMA_DB == ',' else ','
        decimal_point_target = '.' if COMMA_SOURCE == ',' else ','

        # Strip the amount and convert comma.
        # - Remove "-", '."  and blanks.
        f_amount = amount.replace(decimal_point_source, EMPTY).replace('-', EMPTY).strip()
        # - Replace komma (Opt)
        if COMMA_DB != COMMA_SOURCE:
            f_amount = f_amount.replace(COMMA_DB, COMMA_SOURCE)
        if not f_amount:
            f_amount = f'0{COMMA_SOURCE}00'

        # Decimal part
        p_comma = f_amount.find(COMMA_SOURCE)
        decimal_part = COMMA_SOURCE if p_comma == -1 else f_amount[p_comma:]
        decimal_part = decimal_part.ljust(3, '0')  # Pad trailing zeroes

        # Numeric part
        numeric_part = f_amount[:p_comma] if p_comma > -1 else f_amount

        # Add decimals
        result = []
        count = 0
        for i in range(len(numeric_part) - 1, -1, -1):
            count += 1
            result.append(numeric_part[i])
            if count % 3 == 0 and i > 0:
                result.append(decimal_point_target)
        result.reverse()
        numeric_part = EMPTY.join(result)

        # Combine the parts
        unsigned = f'{numeric_part or "0"}{decimal_part}'
        minus = '-' if '-' in amount else EMPTY
        result = f'{minus}{unsigned}'
        return result
