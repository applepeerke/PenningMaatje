#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-30 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Functions import get_BBAN_from_IBAN
from src.BL.Managers.BaseManager import BaseManager
from src.DL.Config import CF_VERBOSE, CF_IMPORT_PATH_COUNTER_ACCOUNTS, CF_IBAN, COUNTER_ACCOUNTS_CSV, \
    SEARCH_TERMS_CSV
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.AttType import AttType
from src.DL.IO.YearMonthIO import YearMonthIO
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCache import Singleton as BookingCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.UserCsvFiles.Cache.SearchTermCache import Singleton as SearchTermCache
from src.DL.UserCsvFiles.Cache.UserMutationsCache import Singleton as UserMutationsCache
from src.DL.Lexicon import TRANSACTIONS, COUNTER_ACCOUNTS, BOOKING_CODE, SEARCH_TERMS
from src.VL.Functions import progress_meter
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.Const import EMPTY, USER_MUTATIONS_FILE_NAME, EXT_CSV
from src.GL.Enums import Color, MessageSeverity
from src.GL.Result import Result

# Working fields
PGM = 'Consistentie'
error_prefix = f'{Color.RED}Er is een fout opgetreden{Color.NC}: '
remark_prefix = f'{Color.BLUE}Opmerking{Color.NC}: '

model = Model()

CM = ConfigManager()
CsvM = CsvManager()
BCM = BookingCache()
ACM = CounterAccountCache()
STM = SearchTermCache()
UMC = UserMutationsCache()
TE_dict = model.get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)


class ConsistencyManager(BaseManager):

    @property
    def is_consistent(self):
        return self._is_consistent

    def __init__(self):
        super().__init__()
        self._YM_IO = YearMonthIO()
        self._entities_without_ca = {}
        self._is_consistent = False
        self._verbose = False
        self._initialize_singletons = False
        self._progress_steps_total = 0
        self._non_existent_bookings = {}
        self._reason = EMPTY

    def run(self) -> Result:
        self._result = Result()
        self._verbose = CM.get_config_item(CF_VERBOSE)
        self._initialize_singletons = self._verbose
        self._is_consistent = False

        transaction_count = self._db.count(Table.Transaction)
        transaction_enriched_count = self._db.count(Table.TransactionEnriched)

        kwargs = self._YM_IO.get_default_kwargs()
        if not kwargs:
            self._result.add_message(
                f'Geen verrijkte {TRANSACTIONS} gevonden.\n'
                f'  Mogelijke oorzaak: De import is tussentijds geannuleerd.\n'
                f'  Remedie: Doe de import opnieuw.', MessageSeverity.Warning)
            return self._result
        # Go!
        from_year = kwargs['from_year']
        from_month = kwargs['from_month']
        to_month = kwargs['to_month']
        to_year = kwargs['to_year']

        self._progress_steps_total = to_year - from_year + 1 if transaction_enriched_count > 0 else 1
        self._is_consistent = True
        self._result.add_message(
            f'\n'
            f'------------------\n'
            f'Consistentie check\n'
            f'------------------\n', MessageSeverity.Info)

        # Validate booking-related csv files (cache)
        self._progress(1, f'{BOOKING_CODE} in "{CM.get_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS)}"')
        self._validate_bookings_imported_from_csv_files()

        # Validate ME
        if transaction_enriched_count != transaction_count:
            self._is_consistent = False
            self._result.add_message(
                f'Niet alle {TRANSACTIONS} zijn verrijkt.\n'
                f'  Mogelijke oorzaak: De import is tussentijds geannuleerd.\n'
                f'  Remedie: Doe de import opnieuw.', MessageSeverity.Warning)

        # - Validate rows per year/month
        account_bban = get_BBAN_from_IBAN(CM.get_config_item(CF_IBAN))
        if transaction_enriched_count > 0:
            yy = from_year
            mm = from_month
            while yy <= to_year:
                # Progress
                step = self._progress_steps_total - (to_year - yy)
                self._progress(step, f'Verrijkte transacties - jaar {yy}')
                # Month
                mm_2 = 12 if yy < to_year else to_month
                while mm <= mm_2:
                    # Get rows
                    month_rows = self._db.fetch(
                        Table.TransactionEnriched,
                        where=[Att(FD.Account_bban, account_bban),
                               Att(FD.Year, yy, type=AttType.Int),
                               Att(FD.Month, mm, type=AttType.Int)])
                    # Calculate results
                    self._validate_month(month_rows)
                    mm += 1
                mm = 1
                yy += 1
        # Remarks
        self._booking_message(Table.CounterAccount, COUNTER_ACCOUNTS)

        # Completion
        count = to_year - from_year + 1 if transaction_enriched_count > 0 else 0
        zijn = 'zijn' if count != 1 else 'is'
        jaren = 'jaren' if count != 1 else 'jaar'
        suffix = f'Deze {zijn} consistent.' if self._is_consistent else 'Er zijn waarschuwingen.'
        self._completion_message(f'Er {zijn} {count} {jaren} gecontroleerd. {suffix}')

        # BookingCodes
        result: Result = BCM.is_valid_config()
        if not result.OK:
            self._result.messages.extend(result.messages)

        return self._result

    def _validate_bookings_imported_from_csv_files(self):
        """ Validate booking-related csv files (before import) """
        ACM.initialize(force=self._initialize_singletons)
        BCM.initialize(force=self._initialize_singletons)
        STM.initialize(force=self._initialize_singletons)
        UMC.initialize(force=self._initialize_singletons)
        # Gevulde Tegenrekening-boeking-code moet bestaan in BoekingsCode
        [self._validate_booking(k, booking_code, COUNTER_ACCOUNTS_CSV, FD.Counter_account_number)
         for k, booking_code in ACM.booking_codes.items()]
        self._completion_message(f'Er zijn {len(ACM.booking_codes.items())} {COUNTER_ACCOUNTS} gecontroleerd.')
        # Gevulde Zoekterm-boeking-code moet bestaan in BoekingsCode
        [self._validate_booking(k, booking_code, SEARCH_TERMS_CSV, FD.SearchTerm)
         for k, booking_code in STM.search_terms.items()]
        # Gevulde UserMutations-boeking-code moet bestaan in BoekingsCode
        [self._validate_booking(EMPTY, booking_code, f'{USER_MUTATIONS_FILE_NAME}{EXT_CSV}', FD.Booking_code)
         for booking_code in UMC.booking_codes]
        self._completion_message(f'Er zijn {len(STM.search_terms.items())} {SEARCH_TERMS} gecontroleerd.')

    def _validate_booking(self, key, booking_code, table_name, key_name):
        """ Save booking names that don't exist in BookingCode. """
        if table_name not in self._non_existent_bookings:
            self._non_existent_bookings[table_name] = set()
        if (not booking_code or
                booking_code in BCM.booking_codes or
                booking_code in self._non_existent_bookings[table_name]
        ):
            return
        # Boeking not found and not listed yet.
        warning = f'\nBestand {table_name}: {key_name} {key} {BOOKING_CODE} ' \
                  f'"{Color.ORANGE}{booking_code}{Color.NC}" bestaat niet. ' \
                  f'Pas {key_name} in het bestand aan of voeg de {BOOKING_CODE} toe.'
        self._result.add_message(warning, MessageSeverity.Warning)
        self._non_existent_bookings[table_name].add(booking_code)

    def _booking_message(self, table_name, entity_name):
        count = len(self._entities_without_ca.get(table_name, {}))
        if count > 0:
            self._result.add_message(
                f'{remark_prefix}{count} {entity_name} hebben geen {BOOKING_CODE}.', MessageSeverity.Warning)

    def _progress(self, step_no, message):
        if not self._session.unit_test and CM.get_config_item(CF_VERBOSE) and not self._session.CLI_mode:
            progress_meter(
                step_no - 1, self._progress_steps_total, 'Consistentie check', 'Consistentie check', message_1=message)

    def _validate_month(self, month_rows):
        """ Validate all ME rows of a month """
        year, month, p_year, p_month = None, None, None, None
        first = True

        row_no = 0
        for month_row in month_rows:
            row_no += 1
            year = month_row[TE_dict[FD.Year]]
            month = month_row[TE_dict[FD.Month]]
            name = month_row[TE_dict[FD.Name]]
            comments = month_row[TE_dict[FD.Comments]]
            # Booking
            booking_code = BCM.get_value_from_id(month_row[TE_dict[FD.Booking_id]], FD.Booking_code)
            counter_account_id = month_row[TE_dict[FD.Counter_account_id]]
            counter_account_number = self._db.fetch_value(
                Table.CounterAccount, name=FD.Counter_account_number, where=[Att(FD.ID, counter_account_id)])

            if first:
                first = False
                p_year = year
                p_month = month
            if year != p_year or month != p_month:
                self._is_consistent = False
                self._result.add_message(
                    f'{error_prefix}Niet alle maanden of jaren zijn gelijk in de set {year}-{month}. '
                    f'Maand {month} is ABNORMAAL beëindigd.', MessageSeverity.Error)
                return

            # Booking code is empty
            if not booking_code and counter_account_number:
                self._increment_missing_booking(Table.CounterAccount, counter_account_number, name, comments)

    def _increment_missing_booking(self, table_name, key, name, comments):
        if table_name not in self._entities_without_ca:
            self._entities_without_ca[table_name] = {}
        if not self._entities_without_ca[table_name].get(key):
            self._entities_without_ca[table_name][key] = [1, name, comments]
        else:
            self._entities_without_ca[table_name][key][0] += 1

    def _completion_message(self, text):
        self._result.add_message(text, MessageSeverity.Completion)
