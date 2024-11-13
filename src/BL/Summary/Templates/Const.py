TPL_HEADER = 'header'
TPL_BODY = 'body'
TPL_FOOTER = 'footer'

SUBGROUP = 'SUBGROUP'
# Singular
YEAR = 'JAAR'
YEAR_PREVIOUS = 'VORIG JAAR'

VAR_SINGULAR_DESC = {
    YEAR: 'Jaar',
    YEAR_PREVIOUS: 'Vorig jaar'
}
MONTH = 'MAAND'
MONTH_FROM = 'MAAND_VAN'
MONTH_TO = 'MAAND_TM'
OPENING_BALANCE = 'BEGINSALDO'
CLOSING_BALANCE = 'EINDSALDO'
TOTAL_REVENUES = 'TOTAAL INKOMSTEN'
TOTAL_COSTS = 'TOTAAL UITGAVEN'

# Plural (column headings)
TYPES = 'TYPEN'
MAINGROUPS = 'HOOFDGROEPEN'
SUBGROUPS = 'SUBGROEPEN'
AMOUNTS = 'BEDRAGEN'
DATES = 'DATUMS'
DESCRIPTIONS = 'OMSCHRIJVINGEN'
BOOKING_DESCRIPTIONS = 'BOEKING OMSCHRIJVINGEN'
REVENUES = 'INKOMSTEN'
COSTS = 'UITGAVEN'
GENERAL = 'GENERAAL'

# Plural totals (used in annual account processing)
TOTAL = 'TOTAAL'
TOTAL_GENERAL = f'TOTAAL {GENERAL}'
TOTAL_TYPE = f'TOTAAL {TYPES}'
TOTAL_MAINGROUP = f'TOTAAL {MAINGROUPS}'

VAR_NAMES_HEADER = [YEAR, YEAR_PREVIOUS, MONTH, OPENING_BALANCE, CLOSING_BALANCE, TOTAL_REVENUES, TOTAL_COSTS]
VAR_NAMES_DETAIL = [TYPES, MAINGROUPS, SUBGROUPS, AMOUNTS, DATES, DESCRIPTIONS, REVENUES, COSTS, BOOKING_DESCRIPTIONS]
VAR_NAMES_DETAIL_TOTAL = [TOTAL_TYPE, TOTAL_MAINGROUP, TOTAL_GENERAL]

FIRST = '*FIRST'
