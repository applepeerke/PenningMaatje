# AttType.py
#
# Author      : Peter Heijligers
# Description : DBDriver attribute
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-03-02 PHe Moved from Model


class AttType(object):
    Int = 'INT'
    Float = 'FLOAT'
    Text = 'TEXT'
    Bool = 'BOOL'
    Blob = 'BLOB'
    Id = 'ID'
    Varchar = 'VARCHAR'
    Timestamp = 'TIMESTAMP'
    FieldName = 'FIELDNAME'
    Raw = 'RAW'

    sanitize_types = [Varchar, Text, Raw]
    numeric_types = [Int, Id, Float]
    string_types = [Varchar, Text, FieldName, Raw]
    python_allowed_types = {
        Int: ['int'],
        Float: ['float', 'int'],
        Text: ['str'],
        Bool: ['bool', 'int'],
        Id: ['int'],
        Varchar: ['str'],
        Timestamp: ['str'],
        FieldName: ['str'],
        Raw: ['str'],
    }
