from src.GL.Const import APP_NAME, BLANK


def _to_cmd_key(value):
    return value.upper().replace(BLANK, '_')


def _to_text_key(value):
    return value.capitalize().replace('_', BLANK)


# Colors
RED = 'Rood'
GREEN = 'Groen'
ORANGE = 'Oranje'
BLUE = 'Blauw'
PURPLE = 'Paars'
BROWN = 'Bruin'
PINK = 'Roze'
GREY = 'Grijs'
OLIVE = 'Olijfgroen'
CYAN = 'Cyaan'


# Words
ACCOUNT_NUMBER = 'Rekening'
ANNUAL_ACCOUNT = 'Jaarrekening'
AGE_MONTHS = 'Leeftijd (maanden)'
AGE_YEARS = 'Leeftijd (jaren)'
AMOUNT = 'Bedrag'
AMOUNT_MONTHLY = 'Bedrag p.m.'
AMOUNT_YEARLY = 'Bedrag p.j.'
AMOUNT_PLUS = 'Bij'
AMOUNT_MINUS = 'Af'
ANNUAL_BUDGET = 'Jaarbegroting'
ANNUAL_TREND = 'Trend'
BALANCE = 'Inkomsten min uitgaven min overboekingen'
BIRTHDAY = 'Geboortedatum'
BOOKING = 'Boeking'
BUDGET = 'Begroting'
COMMENTS = 'Mededelingen'
BOOKING_SEQNO = 'Volgnummer'
BOOKING_CODE = 'Boeking code'
BOOKING_CODES = 'Boeking codes'
BOOKING_TYPE = 'Boeking type'
CONFIG = 'Configuratie'
CORRECTION = 'Correctie'
COSTS = 'Uitgaven'
COUNTER_ACCOUNT = 'Tegenrekening'
COUNTER_ACCOUNTS = 'Tegenrekeningen'
CSV_FILE = 'csv bestand'
DASHBOARD = 'Dashboard'
DATE_FROM = 'Datum vanaf'
DATE_TO = 'Datum tot'
DESCRIPTION = 'Omschrijving'
EXPORT = 'Exporteer'
INPUT_DIR = 'Folder met Bankafschriften'
LOG = 'Log'
MAINTAIN = 'Onderhouden'
MONTH = 'Maand'
MONTHS = 'Maanden'
MUTATION_TYPE = 'Mutatiesoort'
NAME = 'Naam'
OR = 'of'
OTHER = 'Overige'
OUTPUT_DIR = 'Uitvoer folder'
OVERBOOKING = 'Overboeking'
OVERBOOKINGS = 'Overboekingen'
REALISATION = 'Realisatie'
REMARKS = 'Bijzonderheden'
REVENUES = 'Inkomsten'
SEARCH_RESULT = 'Zoekresultaat'
SEARCH_TERM = 'Zoekterm'
SEARCH_TERMS = 'Zoektermen'
SUBTOTALS = 'Subtotalen'
SUMMARY = 'Overzicht'
TOTAL = 'Totaal'
TOTALS = 'Totalen'
TRANSACTION = 'Bankafschrift'
TRANSACTION_CODE = 'Transactiecode'
TRANSACTION_COUNT = 'Aantal transacties'
TRANSACTION_DATE = 'Transactiedatum'
TRANSACTION_TIME = 'Transactietijd'
TRANSACTIONS = 'Bankafschriften'
TYPE = 'Type'
WORK_WITH = 'Werken met'
YEAR = 'Jaar'
YEARS = 'Jaren'

# Compound
SALDO_MINUS_CORRECTION = f'Saldo min {CORRECTION}'

CMD_IMPORT_TE = _to_cmd_key(f'IMPORTEER_{TRANSACTIONS}')
CMD_WORK_WITH_BOOKING_CODES = _to_cmd_key(BOOKING_CODES)
CMD_WORK_WITH_SEARCH_TERMS = _to_cmd_key(SEARCH_TERMS)
CMD_RESTORE_BOOKING_RELATED_DATA = _to_cmd_key(f'TERUGZETTEN_{BOOKING_CODES}')
CMD_SEARCH_FOR_EMPTY_BOOKING_CODE = _to_cmd_key(f'ONTBREKENDE_{BOOKING_CODES}')

# Help text
var_names = {
    'APP': APP_NAME,
    'ACCOUNT_NUMBER': ACCOUNT_NUMBER,
    'BASE_DIR': OUTPUT_DIR,
    'BOOKING': BOOKING,
    'BOOKINGS': BOOKING_CODES,
    'CMD_IMPORT_TE': _to_cmd_key(CMD_IMPORT_TE),
    'CMD_WORK_WITH_BOOKING_CODES': _to_text_key(CMD_WORK_WITH_BOOKING_CODES),
    'CMD_WORK_WITH_SEARCH_TERMS': _to_text_key(CMD_WORK_WITH_SEARCH_TERMS),
    'CMD_RESTORE_BOOKING_RELATED_DATA': _to_text_key(CMD_RESTORE_BOOKING_RELATED_DATA),
    'CMD_SEARCH_FOR_EMPTY_BOOKING': _to_text_key(CMD_SEARCH_FOR_EMPTY_BOOKING_CODE),
    'CONFIG': CONFIG,
    'COUNTER_ACCOUNT': COUNTER_ACCOUNT,
    'COUNTER_ACCOUNTS': COUNTER_ACCOUNTS,
    'CSV_FILE': CSV_FILE,
    'DASHBOARD': DASHBOARD,
    'INPUT_DIR': INPUT_DIR,
    'LOG': LOG,
    'MONTH': MONTH,
    'MONTHS': MONTHS,
    'SEARCH_TERM': SEARCH_TERM,
    'SEARCH_TERMS': SEARCH_TERMS,
    'TRANSACTION': TRANSACTION,
    'TRANSACTIONS': TRANSACTIONS,
    'YEAR': YEAR,
    'YEARS': YEARS,
    'WORK_WITH': WORK_WITH,
    'OVERBOOKING': OVERBOOKING,
    'CORRECTION': CORRECTION,
    'SALDO_MINUS_CORRECTION': SALDO_MINUS_CORRECTION,
}


def substitute_vars(line) -> str:
    s = -1
    while True:
        s = line.find('{', s + 1)
        e = line.find('}', s) if s > -1 else -1
        if -1 < s < e:
            var_name = line[s + 1:e]
            value = var_names.get(var_name, None)
            if value:
                line = line.replace(f'{{{line[s + 1:e]}}}', value)
        else:
            break
    return line
