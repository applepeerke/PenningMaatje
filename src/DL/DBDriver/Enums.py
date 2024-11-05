class FetchMode(object):
    WholeTable = 'All'
    First = 'First'
    Set = 'Set'


class IOStatus(object):
    OK = 'OK'
    VE = 'ValueError'
    ER = 'Error'
    NR = 'NotFound'
    EQ = 'Equal'
    CN = 'Cancel'
    WA = 'Warning'


class OrderType(object):
    ASC = 'ASC'
    DESC = 'DESC'


class TransactionMode(object):
    C = 'Create'
    R = 'Read'
    U = 'Update'
    D = 'Delete'


class Appearance(object):
    Label = 'Label'
    OptionBox = 'OptionBox'
    CheckBox = 'CheckBox'
    RadioButton = 'RadioButton'
    Entry = 'Entry'
    TextArea = 'TextArea'


class HTMLValuta(object):
    euro = '&euro;'
    dollar = '&#xf155;'
    pound = '&#xf154;'
