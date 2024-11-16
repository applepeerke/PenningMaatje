#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# -------------------------------------------------------------------------------------------------------------------
from src.DL.Model import FD
from src.DL.Objects.ConfigItem import ConfigItem
from src.DL.Table import Table
from src.VL.Data.Constants.Color import DEFAULT_FONT, DEFAULT_FONT_SIZE, DEFAULT_FONT_TABLE
from src.VL.Data.Constants.Const import *
from src.VL.Data.Constants.Enums import Pane
from src.DL.Lexicon import *
from src.GL import Enums
from src.GL.BusinessLayer.SessionManager import Singleton as Session
from src.GL.Const import EMPTY, APP_NAME, COMMA_DB, COMMA_SOURCE
from src.GL.Functions import is_valid_file
from src.GL.Validate import isDirname, isBool, isInt, isAlphaNumeric, isAmount, \
    isCsvText, isCommaRepresentation, isPathname, isIntOrNone, isAlphaNumericOrEmpty, isCsvTextOrNone, \
    isBookingCodeOrEmpty

CF_SETTINGS_PATH = 'CF_SETTINGS_PATH'
CF_OUTPUT_DIR = 'CF_OUTPUT_DIR'
CF_INPUT_DIR = 'CF_INPUT_DIR'
CF_RESTORE_BOOKING_DATA = 'CF_RESTORE_BOOKING_DATA'

CF_IMPORT_PATH_ACCOUNTS = 'CF_IMPORT_PATH_ACCOUNTS'
CF_IMPORT_PATH_BOOKINGS = 'CF_IMPORT_PATH_BOOKINGS'
CF_IMPORT_PATH_COUNTER_ACCOUNTS = 'CF_IMPORT_PATH_COUNTER_ACCOUNTS'
CF_IMPORT_PATH_OPENING_BALANCE = 'CF_IMPORT_PATH_OPENING_BALANCE'
CF_IMPORT_PATH_SEARCH_TERMS = 'CF_IMPORT_PATH_SEARCH_TERMS'
CF_IMPORT_PATH_ANNUAL_ACCOUNT = 'CF_IMPORT_PATH_ANNUAL_ACCOUNT'

CF_THEME = 'CF_THEME'
CF_FONT = 'CF_FONT'
CF_FONT_SIZE = 'CF_FONT_SIZE'
CF_FONT_TABLE = 'CF_FONT_TABLE'
CF_FONT_TABLE_SIZE = 'CF_FONT_TABLE_SIZE'
CF_TOOL_TIP = 'CF_TOOL_TIP'
CF_IMAGE_SUBSAMPLE = 'CF_IMAGE_SUBSAMPLE'
CF_COL_OVERBOOKING = 'CF_COL_OVERBOOKING'
CF_COL_COSTS = 'CF_COL_COSTS'
CF_COL_REVENUES = 'CF_COL_REVENUES'
CF_COL_SALDO_MINUS_CORRECTION = 'CF_COL_SALDO_MINUS_CORRECTION'

CF_LOG_LEVEL = 'CF_LOG_LEVEL'
CF_VERBOSE = 'CF_VERBOSE'
CF_SHOW_ALL_POPUPS = 'CF_SHOW_ALL_POPUPS'
CF_UNIT_TEST = 'CF_UNIT_TEST'
CF_AUTO_CLOSE_TIME_S = 'CF_AUTO_CLOSE_TIME_S'
CF_BACKUP_RETENTION_MONTHS = 'CF_BACKUP_RETENTION_MONTHS'
CF_AMOUNT_THRESHOLD_TO_OTHER = 'CF_AMOUNT_THRESHOLD_TO_OTHER'
CF_COMMA_REPRESENTATION_DB = 'CF_COMMA_REPRESENTATION_DB'
CF_COMMA_REPRESENTATION_DISPLAY = 'CF_COMMA_REPRESENTATION_DISPLAY'

CF_ROWS_YEAR = 'CF_ROWS_YEAR'
CF_ROWS_MONTH = 'CF_ROWS_MONTH'
CF_ROWS_TRANSACTION = 'CF_ROWS_TRANSACTION'
CF_ROWS_BOOKING = 'CF_ROWS_BOOKING'
CF_ROWS_SEARCH_TERM = 'CF_ROWS_SEARCH_TERMS'
CF_ROWS_COMBO_MAX = 'CF_ROWS_COMBO_MAX'
CF_ROWS_ACCOUNT_WITHOUT_BOOKING = 'CF_ROWS_ACCOUNT_WITHOUT_BOOKING'

CF_IBAN = 'CF_IBAN'

CF_SEARCH_YEAR = 'CF_SEARCH_YEAR'
CF_SEARCH_MONTH = 'CF_SEARCH_MONTH'
CF_SEARCH_COUNTER_ACCOUNT = 'CF_SEARCH_COUNTER_ACCOUNT'
CF_SEARCH_BOOKING_CODE = 'CF_SEARCH_BOOKING_CODE'
CF_SEARCH_TRANSACTION_CODE = 'CF_SEARCH_TRANSACTION_CODE'
CF_SEARCH_AMOUNT = 'CF_SEARCH_AMOUNT'
CF_SEARCH_AMOUNT_TO = 'CF_SEARCH_AMOUNT_TO'
CF_SEARCH_AMOUNT_TOTAL = 'CF_SEARCH_AMOUNT_TOTAL'
CF_SEARCH_TRANSACTION_TYPE = 'CF_SEARCH_TRANSACTION_TYPE'
CF_SEARCH_TEXT = 'CF_SEARCH_NAME'
CF_SEARCH_REMARKS = 'CF_SEARCH_REMARKS'
CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION = 'CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION'
CF_REMARKS = 'CF_REMARKS'

# Summary popup
CF_COMBO_SUMMARY = 'CF_COMBO_SUMMARY'
CF_SUMMARY_YEAR = 'CF_SUMMARY_YEAR'
CF_SUMMARY_MONTH_FROM = 'CF_SUMMARY_MONTH_FROM'
CF_SUMMARY_MONTH_TO = 'CF_SUMMARY_MONTH_TO'
CF_SUMMARY_OPENING_BALANCE = 'CF_SUMMARY_OPENING_BALANCE'

# Hidden
CF_ROW_NO_YS = f'CF_ROW_NO_{Pane.YS}'
CF_ROW_NO_MS = f'CF_ROW_NO_{Pane.MS}'
CF_ROW_NO_ME = f'CF_ROW_NO_{Pane.TE}'
CF_ID_YS = f'CF_ID_{Pane.YS}'
CF_ID_MS = f'CF_ID_{Pane.MS}'
CF_ID_ME = f'CF_ID_{Pane.TE}'
CF_HIDDEN_POPUPS = 'CF_HIDDEN_POPUPS'
CF_WINDOW_LOCATIONS = 'CF_WINDOW_LOCATIONS'

CF_RADIO_ALL = 'CF_RADIO_ALL'
CF_RADIO_ONLY_THIS_ONE = 'CF_RADIO_ONLY_THIS_ONE'

CF_BOOKING_TYPE = 'CF_BOOKING_TYPE'
CF_BOOKING_MAINGROUP = 'CF_BOOKING_MAINGROUP'
CF_BOOKING_SUBGROUP = 'CF_BOOKING_SUBGROUP'
CF_BOOKING_CODE = 'CF_BOOKING_CODE'
CF_BOOKING_SEQNO = 'CF_BOOKING_SEQNO'
CF_BOOKING_PROTECTED = 'CF_BOOKING_PROTECTED'
CF_BOOKING_COUNT = 'CF_BOOKING_COUNT'

# csv
ACCOUNTS_CSV = 'Rekeningen.csv'
BOOKING_CODES_CSV = 'Boekingscodes.csv'
COUNTER_ACCOUNTS_CSV = 'Tegenrekeningen.csv'
OPENING_BALANCE_CSV = 'Beginsaldi.csv'
SEARCH_TERMS_CSV = 'Zoektermen.csv'
ANNUAL_ACCOUNT_CSV = 'Jaarrekening.csv'

COUNTER_ACCOUNTS_WITHOUT_BOOKING_CODE_CSV = 'Tegenrekeningen_zonder_boeking_code.csv'
DOUBLES_CSV = 'Dubbele_afschriften.csv'

CF_IMPORT_PATH = 'CF_IMPORT_PATH'
FILE_NAME = 'FILE_NAME'

LAYOUT_EXTRA_COLUMNS = {
    CF_COL_OVERBOOKING: FD.Overbooking,
    CF_COL_COSTS: FD.Costs,
    CF_COL_REVENUES: FD.Revenues,
    CF_COL_SALDO_MINUS_CORRECTION: FD.Balance_corrected
}

TABLE_PROPERTIES = {
    Table.Account: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_ACCOUNTS,
        FILE_NAME: ACCOUNTS_CSV},
    Table.AnnualAccount: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_ANNUAL_ACCOUNT,
        FILE_NAME: ANNUAL_ACCOUNT_CSV},
    Table.BookingCode: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_BOOKINGS,
        FILE_NAME: BOOKING_CODES_CSV},
    Table.CounterAccount: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_COUNTER_ACCOUNTS,
        FILE_NAME: COUNTER_ACCOUNTS_CSV},
    Table.OpeningBalance: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_OPENING_BALANCE,
        FILE_NAME: OPENING_BALANCE_CSV},
    Table.SearchTerm: {
        CF_IMPORT_PATH: CF_IMPORT_PATH_SEARCH_TERMS,
        FILE_NAME: SEARCH_TERMS_CSV},

}


def _border(text):
    return f'  {text}  '


def get_text_file(filename):
    session = Session()
    path = f'{session.resources_dir}{filename}.txt'
    if not is_valid_file(path):
        return EMPTY
    with open(path) as txtFile:
        lines = txtFile.readlines()
    lines = [substitute_vars(line) for line in lines]
    return EMPTY.join(lines)


configDef = {
    CF_SETTINGS_PATH: ConfigItem('Configuratie folder', EMPTY, EMPTY, isPathname),
    CF_OUTPUT_DIR: ConfigItem(
        OUTPUT_DIR, None,
        _border(
            f'"{OUTPUT_DIR}" bevat de uitvoer van {APP_NAME}.  \n\n'
            f'  Bij uitvoer moet je denken aan  \n'
            f'    o  Database  \n'
            f'    o  Log  \n'
            f'    o  Backups'
        ), isDirname),
    CF_INPUT_DIR: ConfigItem(
        INPUT_DIR, None,
        _border(
            f'"{INPUT_DIR}" bevat je {TRANSACTIONS}.  \n\n'
            f'  De folder mag alleen {CSV_FILE}en bevatten met {TRANSACTIONS}.'
        ), isDirname),
    CF_RESTORE_BOOKING_DATA: ConfigItem(
        f'Backup datum', EMPTY,
        _border(f'Je kunt hier een backup kiezen om {BOOKING_CODE} gerelateerde gegevens terug te zetten.'), isDirname),
    CF_THEME: ConfigItem(
        'Kleuren thema', False,
        _border('Kleuren thema'), isAlphaNumeric),
    CF_FONT: ConfigItem(
        'Font', DEFAULT_FONT,
        _border('Font'), isAlphaNumeric),
    CF_FONT_SIZE: ConfigItem(
        'Font grootte', DEFAULT_FONT_SIZE,
        _border('Font grootte'), isInt),
    CF_FONT_TABLE: ConfigItem(
        'Font voor gegevens', DEFAULT_FONT_TABLE,
        _border('Font voor tabel gegevens'), isAlphaNumeric),
    CF_FONT_TABLE_SIZE: ConfigItem(
        'Font grootte voor gegevens', DEFAULT_FONT_SIZE,
        _border('Font grootte voor tabel gegevens'), isInt),
    CF_IMAGE_SUBSAMPLE: ConfigItem(
        'Knop grootte (hoger is kleiner)', 10,
        _border('Knop grootte'), isInt),
    # Layout extra columns
    CF_COL_OVERBOOKING: ConfigItem(
        f'Toon kolom {OVERBOOKING}', False,
        _border(f'Toon kolom {OVERBOOKING} in paneel {YEARS} en {MONTHS}'), isBool),
    CF_COL_COSTS: ConfigItem(
        f'Toon kolom {COSTS}', False,
        _border(f'Toon kolom {COSTS} in paneel {YEARS} en {MONTHS}'), isBool),
    CF_COL_REVENUES: ConfigItem(
        f'Toon kolom {REVENUES}', False,
        _border(f'Toon kolom {REVENUES} in paneel {YEARS} en {MONTHS}'), isBool),
    CF_COL_SALDO_MINUS_CORRECTION: ConfigItem(
        f'Toon kolom {SALDO_MINUS_CORRECTION}', False,
        _border(f'Toon kolom {SALDO_MINUS_CORRECTION} in paneel {YEARS} en {MONTHS}'), isBool),
    CF_TOOL_TIP: ConfigItem(
        'Toon tips bij de muisaanwijzer', False,
        _border('Toon tips'), isBool),
    CF_LOG_LEVEL: ConfigItem(
        'Log niveau\n', Enums.LogLevel.Warning,
        _border('Log niveau'), isAlphaNumeric),
    CF_VERBOSE: ConfigItem(
        'Toon uitgebreide informatie', False,
        _border('Toon uitgebreide informatie in de log, en toon de voortgang.'),
        isBool),
    CF_SHOW_ALL_POPUPS: ConfigItem(
        'Toon alle meldingen', False,
        _border('Bij sommige meldingen heb je misschien aangegeven dat de melding niet meer moet verschijnen.  \n'
                'Als je deze optie aanvinkt verschijnen ze weer.'),
        isBool),
    CF_UNIT_TEST: ConfigItem('Unit test', False, EMPTY, isBool),
    CF_AUTO_CLOSE_TIME_S: ConfigItem(
        'Berichten-box automatische sluittijd', 3,
        _border(
            'Automatische sluittijd van PopUps in seconden.  \n'
            '  Bij fouten of waarschuwingen blijft de PopUp staan.  \n'
            '  Na een succesvolle actie wordt hij automatisch gesloten.  \n\n'
            '  Hier geef je aan hoeveel seconden hij dan open blijft staan.  \n'
            '    0=Niet automatisch sluiten.'
        ), isInt),
    CF_BACKUP_RETENTION_MONTHS: ConfigItem(
        'Backup bewaartijd in maanden', 6,
        _border(
            'Het aantal maanden dat log- en backup-bestanden worden bewaard.  \n'
            '  Bestanden die ouder zijn worden automatisch verwijderd bij het sluiten van de app.'
        ), isInt),
    CF_AMOUNT_THRESHOLD_TO_OTHER: ConfigItem(
        'Drempelbedrag om bij import in de "overige" post geboekt te worden', 0,
        _border(
            f'Drempelbedrag. Als een bedrag tijdens de import lager is wordt het bij {OTHER_COSTS} '
            f'of {OTHER_REVENUES} geboekt.'
        ), isInt),
    # Not user visible
    CF_COMMA_REPRESENTATION_DB: ConfigItem(
        'Komma representatie in de database.', COMMA_DB,
        _border(
            'Komma representatie in de database.  \n'
            '  Dit is het teken ("." of ",") dat in de database wordt gebruikt om getallen '
            'voor en na de komma te onderscheiden.'
        ), isCommaRepresentation),
    # Not user visible
    CF_COMMA_REPRESENTATION_DISPLAY: ConfigItem(
        'Komma representatie in de uitvoer in schermen.', COMMA_SOURCE,
        _border(
            'Komma representatie in de schermen.\n'
            '  Dit is het teken ("." of ",") dat in de schermen wordt gebruikt om getallen '
            'voor en na de komma te onderscheiden.'
        ), isCommaRepresentation),
    CF_ROWS_YEAR: ConfigItem(
        f'Aantal te tonen {YEARS}', 5, _border(f'Het aantal rijen in de {YEAR} lijst.'), isInt),
    CF_ROWS_MONTH: ConfigItem(
        f'Aantal te tonen {MONTHS}', 12, _border(f'Het aantal rijen in de {MONTH} lijst.'), isInt),
    CF_ROWS_TRANSACTION: ConfigItem(
        f'Aantal te tonen {TRANSACTIONS}', 20, _border(f'Het aantal rijen in de {TRANSACTION} lijst.'), isInt),
    CF_ROWS_BOOKING: ConfigItem(
        f'Aantal te tonen {BOOKING_CODES}', 20, _border(f'Het aantal rijen in de {BOOKING_CODE} lijst.'), isInt),
    CF_ROWS_SEARCH_TERM: ConfigItem(
        f'Aantal te tonen {SEARCH_TERMS}', 20, _border(f'Het aantal rijen in de {SEARCH_TERMS} lijst.'), isInt),
    CF_ROWS_COMBO_MAX: ConfigItem(
        f'Maximum aantal combo box items', 30, _border(f'Het maximum aantal te tonen items in een combo box.'), isInt),
    CF_ROWS_ACCOUNT_WITHOUT_BOOKING: ConfigItem(None, 50, None, None),
    # Rekening
    CF_IBAN: ConfigItem('Rekening', EMPTY, None, isAlphaNumeric),
    # Search
    CF_SEARCH_YEAR: ConfigItem('Jaar', EMPTY, None, isIntOrNone),
    CF_SEARCH_MONTH: ConfigItem('Maand', EMPTY, None, isIntOrNone),
    CF_SEARCH_COUNTER_ACCOUNT: ConfigItem('Tegenrekening', EMPTY, None, isAlphaNumericOrEmpty),
    CF_SEARCH_TRANSACTION_CODE: ConfigItem('TransactieCode', EMPTY, None, isAlphaNumeric),
    CF_SEARCH_AMOUNT: ConfigItem('Bedrag', EMPTY, None, isAmount),
    CF_SEARCH_AMOUNT_TO: ConfigItem('Bedrag t/m', EMPTY, None, isAmount),
    CF_SEARCH_AMOUNT_TOTAL: ConfigItem('Totaal', EMPTY, None, isAmount),
    CF_SEARCH_TRANSACTION_TYPE: ConfigItem('Mutatiesoort', EMPTY, None, isAlphaNumeric),
    CF_SEARCH_BOOKING_CODE: ConfigItem('Boeking code', EMPTY, None, isAlphaNumericOrEmpty),
    CF_SEARCH_TEXT: ConfigItem(
        'Naam *', EMPTY,
        _border(
            'Zoek in de naam, mededelingen en bijzonderheden van de begunstigde.  \n'
            '  Als wildcard kun je "*" gebruiken (alleen vóór en/of na de zoekterm). '), isCsvText),
    CF_SEARCH_REMARKS: ConfigItem(
        'Bijzonderheden', EMPTY, _border('Zoek transacties waaraan je bijzonderheden hebt toegevoegd.'), isBool),
    CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION: ConfigItem('Boeking', EMPTY, None, isAlphaNumericOrEmpty),
    # Booking
    CF_BOOKING_TYPE: ConfigItem('Boeking type', EMPTY, None, isAlphaNumeric),
    CF_BOOKING_MAINGROUP: ConfigItem('Hoofdgroep', EMPTY, None, isAlphaNumeric),
    CF_BOOKING_SUBGROUP: ConfigItem('Subgroep', EMPTY, None, isAlphaNumericOrEmpty),
    CF_BOOKING_CODE: ConfigItem('Code', EMPTY, None, isBookingCodeOrEmpty),
    CF_BOOKING_SEQNO: ConfigItem('Volgnummer', EMPTY, None, isIntOrNone),
    CF_BOOKING_COUNT: ConfigItem('Aantal', EMPTY, None, isIntOrNone),
    # Editable
    CF_REMARKS: ConfigItem(
        REMARKS, EMPTY,
        _border(
            f'Wat je hier invult komt in kolom "{REMARKS}" te staan van paneel {PANE_TRANSACTIONS}.'
        ), isCsvTextOrNone),
    CF_RADIO_ALL: ConfigItem(
        f'Alle {TRANSACTIONS} wijzigen', True,
        _border(f'Als je deze kiest worden alle bijbehorende {TRANSACTIONS} gewijzigd'), isBool),
    CF_RADIO_ONLY_THIS_ONE: ConfigItem(
        f'Alleen de gekozen {TRANSACTION} wijzigen', False,
        _border(f'Als je deze kiest wordt alleen deze {TRANSACTION} gewijzigd'), isBool),
    # Hidden
    CF_IMPORT_PATH_ACCOUNTS: ConfigItem(f'Pad naar {ACCOUNTS_CSV}'),
    CF_IMPORT_PATH_ANNUAL_ACCOUNT: ConfigItem(f'Pad naar {ANNUAL_ACCOUNT_CSV}'),
    CF_IMPORT_PATH_BOOKINGS: ConfigItem(f'Pad naar {BOOKING_CODES_CSV}'),
    CF_IMPORT_PATH_SEARCH_TERMS: ConfigItem(f'Pad naar {SEARCH_TERMS_CSV}'),
    CF_IMPORT_PATH_COUNTER_ACCOUNTS: ConfigItem(f'Pad naar {COUNTER_ACCOUNTS_CSV}'),
    CF_IMPORT_PATH_OPENING_BALANCE: ConfigItem(f'Pad naar {OPENING_BALANCE_CSV}'),
    CF_ROW_NO_YS: ConfigItem(),
    CF_ROW_NO_MS: ConfigItem(),
    CF_ROW_NO_ME: ConfigItem(),
    CF_ID_YS: ConfigItem(),
    CF_ID_MS: ConfigItem(),
    CF_ID_ME: ConfigItem(),
    CF_HIDDEN_POPUPS: ConfigItem(),
    CF_WINDOW_LOCATIONS: ConfigItem(),

    # Summary
    CF_COMBO_SUMMARY: ConfigItem(f'Kies het soort {SUMMARY}'),
    CF_SUMMARY_YEAR: ConfigItem('Kies het Jaar', validation_method=isIntOrNone),
    CF_SUMMARY_MONTH_FROM: ConfigItem('Maand vanaf', 0, validation_method=isIntOrNone),
    CF_SUMMARY_MONTH_TO: ConfigItem('Maand t/m', 0, validation_method=isIntOrNone),
    CF_SUMMARY_OPENING_BALANCE: ConfigItem('Begin saldo', 0.0, validation_method=isAmount),

    # Commands
    CMD_IMPORT_TE: ConfigItem(tooltip=_border(
        f'Importeer je {TRANSACTIONS} in de database.\n'
        f'  Deze staan in de {INPUT_DIR} (zie {CONFIG}).'
    )),
    CMD_SEARCH_FOR_EMPTY_BOOKING_CODE: ConfigItem(tooltip=_border(f'Ken {BOOKING_CODES} aan {TRANSACTIONS} toe.')),
    CMD_CONSISTENCY: ConfigItem(tooltip=_border(
        f'Check de consistentie van de gegevens.\n'
        f'  De uitvoer komt te staan in\n'
        f'    o  Tab {TAB_LOG}\n'
        f'    o  Een {CSV_FILE} in de {OUTPUT_DIR}.'
    )),

    CMD_FACTORY_RESET: ConfigItem(tooltip=_border(
        f'{to_text_key(CMD_FACTORY_RESET)}.\n\n'
        f'  Alle configuratie- en database gegevens worden verwijderd.\n'
        f'  Je {TRANSACTIONS} blijven gewoon staan. Importeer ze dan opnieuw.'
    )),
    CMD_CONFIG: ConfigItem(tooltip='Configuratie en layout wijzigen.'),
    CMD_SEARCH: ConfigItem(tooltip='Zoek met de opgegeven criteria.'),
    CMD_SUMMARY: ConfigItem(tooltip=f'Maak een {SUMMARY}.'),
    CMD_SEARCH_RESET: ConfigItem(tooltip='Maak je zoek-criteria weer leeg.'),
    CMD_EXPORT: ConfigItem(tooltip=f'Exporteer de zoekresultaten naar een {CSV_FILE}.'),
    CMD_UNDO: ConfigItem(tooltip=f'Maak laatste {BOOKING_CODE} wijziging ongedaan.'),
    CMD_HELP_WITH_OUTPUT_DIR: ConfigItem(),
    CMD_HELP_WITH_INPUT_DIR: ConfigItem(),
    CMD_HELP_WITH_BOOKING: ConfigItem(tooltip=get_text_file('Help_with_BookingCodes')),
    CMD_HELP_WITH_SEARCH: ConfigItem(tooltip=get_text_file('Help_with_Search')),
}


def get_label(key) -> str:
    if key not in configDef:
        return key
    return configDef[key].label
