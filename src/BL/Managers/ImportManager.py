#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.BL.Managers.BaseManager import BaseManager
from src.BL.Managers.ConsistencyManager import ConsistencyManager
from src.BL.Validator import Validator
from src.DL.Config import CF_VERBOSE, DOUBLES_CSV, \
    CSV_FILE, CF_COMMA_REPRESENTATION_DISPLAY, CF_INPUT_DIR, CF_IBAN, \
    CF_AMOUNT_THRESHOLD_TO_OTHER
from src.DL.DBDriver.Att import Att
from src.DL.DBDriver.Enums import FetchMode
from src.DL.IO.AccountIO import AccountIO
from src.DL.IO.CounterAccountIO import CounterAccountIO
from src.DL.IO.YearMonthIO import YearMonthIO
from src.DL.Model import FD, Model
from src.DL.Objects.CounterAccount import CounterAccount
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.DL.UserCsvFiles.Cache.CounterAccountCache import Singleton as CounterAccountCache
from src.DL.UserCsvFiles.Cache.SearchTermCache import Singleton as SearchTermCache
from src.DL.UserCsvFiles.Cache.UserMutationsCache import Singleton as UserMutationsCache, get_te_key
from src.DL.UserCsvFiles.UserCsvFileManager import UserCsvFileManager
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.Const import UNKNOWN, BLANK, EMPTY
from src.GL.Enums import Color, MessageSeverity as Sev, MessageSeverity, ActionCode
from src.GL.Functions import skip_blanks, remove_color_code, format_date, \
    is_formatted_ymd, try_to_get_date_format, toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import isInt
from src.VL.Data.Constants.Const import LEEG, NIET_LEEG, OTHER_COSTS, OTHER_REVENUES
from src.DL.Lexicon import TRANSACTIONS, AMOUNT_PLUS, \
    AMOUNT_MINUS, BOOKING_CODES


error_prefix = f'{Color.RED}Fout:{Color.NC} '
error_message = None

# Validation
total_count = 0
error_count = 0
warning_count = 0
row_count = 0

PGM = 'ImportManager'

model = Model()
csvm = CsvManager()
CM = ConfigManager()

BCM = BookingCodeCache()
ACM = CounterAccountCache()
STM = SearchTermCache()
UMC = UserMutationsCache()

TE_dict = model.get_colno_per_att_name(Table.TransactionEnriched)
TE_dict_1 = model.get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)
TX_dict = model.get_att_name_per_colno(Table.Transaction)
bk_dict = model.get_colno_per_att_name(Table.BookingCode, zero_based=False)

comma_source = CM.get_config_item(CF_COMMA_REPRESENTATION_DISPLAY, ',')
threshold_to_other_pos = CM.get_config_item(CF_AMOUNT_THRESHOLD_TO_OTHER, 0)
threshold_to_other_min = threshold_to_other_pos * -1


class ImportManager(BaseManager):

    def __init__(self, unit_test=False):
        super().__init__()
        self._unit_test = unit_test
        self._verbose = False
        self._counter = 0

        self._validation_manager = Validator()
        self._user_csv_manager = UserCsvFileManager()
        self._account_io = AccountIO()
        self._counter_account_manager = CounterAccountIO()

        self._unique_account_bban = set()
        self._unique_year = set()
        self._unique_counter_account_id = set()
        self._unique_transaction_code = set()
        self._unique_mutation_type = set()
        self._unique_card_seqno = set()
        self._unique_booking_types = set()
        self._progress_steps_total = 0
        self._amounts_are_signed = False

    def start(self, import_user_csv_files=True) -> Result:
        global error_count, total_count, warning_count

        self._verbose = CM.get_config_item(CF_VERBOSE)

        error_count, total_count, warning_count = 0, 0, 0

        popup = None
        if not self._session.SessionManager.CLI_mode:
            from src.VL.Views.PopUps.PopUp import PopUp
            popup = PopUp()

        # Validate transactions folder
        self._progress_steps_total = 6
        #  Validate import transactions .csv files: Check file headers.
        self._result = self._validation_manager.validate_config_dir(CF_INPUT_DIR)
        if not self._result.OK:
            self._result.add_message('\nImporteren is afgebroken.', MessageSeverity.Error)
            return self._result

        # Validate optional user data: base tables (bookings, accounts, search-terms)
        if import_user_csv_files:
            self._result = self._user_csv_manager.validate_resource_files(full_check=True)
            if self._result.ER:  # Warnings allowed
                return self._result

        # Validate bookings paths to csv files (warning only)
        result = BCM.is_valid_config()
        if not result.OK:
            self._result.messages.extend(result.messages)
            if not result.get_box_message(min_severity=MessageSeverity.Warning, cont_text=True):
                self._result.action_code = ActionCode.Cancel
                return self._result

        # Go!
        # a. Clear DB tables
        self._account_io = AccountIO()  # Clear accounts in memory
        self._progress(1, 'Leeg maken database tabellen')
        if import_user_csv_files:
            [self._db.clear(table) for table in model.DB_tables]
        else:
            [self._db.clear(table) for table in model.DB_tables if table not in model.user_maintainable_tables]
        self._result.add_message('\nDatabase tabellen zijn leeg gemaakt.', Sev.Completion)

        # b. Repopulate booking related user data: base tables
        #   (bookings, accounts, search-terms), even if not working with bookings.
        self._progress(2, f'{CSV_FILE.title()}en importeren')
        if import_user_csv_files:
            self._user_csv_manager.import_user_defined_csv_files()
            self._result.add_message(f'{CSV_FILE.title()}en zijn geïmporteerd.', Sev.Completion)

        # c. Import the raw bank transaction files and the accounts.
        self._progress(3, f'{TRANSACTIONS} importeren')
        self.import_bank_transactions(self._db)
        self._result.add_message(f'{TRANSACTIONS} zijn geïmporteerd.', Sev.Completion)

        # d. Evaluate doubles
        self._progress(4, 'Controleren op dubbele')
        rows = self._db.fetch(Table.Transaction, mode=FetchMode.WholeTable)
        count = 0
        if self._has_consecutive_doubles(rows):
            count = self.export_doubles(rows)
        # - Completion
        count_text = f'{Color.GREEN}geen{Color.NC}' if count == 0 else f'{Color.ORANGE}{count}{Color.NC}'
        ref_text = f'\nZie "{DOUBLES_CSV}" in "{self._session.output_dir}"' if count > 0 else EMPTY
        if self._verbose or count > 0:
            message = f'Er zijn {count_text} dubbele {TRANSACTIONS} batches gevonden.{ref_text}'
            if count > 0:
                text = f'{remove_color_code(message)}\n\nDoorgaan?'
                if (not popup or
                        (popup and not popup.confirm(popup_key=f'{PGM}.doubles_found', text=text))):
                    self._result.action_code = ActionCode.Cancel
                    self._result.add_message(f'{message}\n\nImport is GEANNULEERD.', Sev.Completion)
                    return self._result
            self._result.add_message(message, Sev.Completion)

        # e. Enrich transacties
        self._progress(5, f'{TRANSACTIONS}  verrijken')
        self.create_enriched_mutations(self._db)
        self._result.add_message(f'{TRANSACTIONS} zijn verrijkt met {BOOKING_CODES}.', Sev.Completion)
        self._progress(6, 'Combo boxen vullen')
        self._save_combo_data()  # Flat files

        # f. Consistency check
        # Jaar: Support selection of years / months.
        cm = ConsistencyManager()
        result = cm.run()
        self._result.messages.extend(result.messages)
        self._result.add_message('Consistentie check is gedaan.\n', Sev.Completion)

        # g. Create Maand- en jaarOverzicht
        if not self._result.ER:
            result = YearMonthIO().refresh_data()
            self._result.messages.extend(result.messages)
            if result.OK:
                self._result.add_message('Jaar- en maandoverzicht is gemaakt.', Sev.Completion)
        return self._result

    def _progress(self, step_no, message):
        if not self._session.unit_test and CM.get_config_item(CF_VERBOSE) and not self._session.CLI_mode:
            from src.VL.Functions import progress_meter
            progress_meter(
                step_no - 1, self._progress_steps_total, 'Importeren', 'Importeren', message_1=message)

    def _has_consecutive_doubles(self, rows) -> bool:
        """ Multiple consecutive doubles indicate a double batch.  """
        count = 0
        key_p = EMPTY
        for row in rows:
            where = model.get_pk_atts_from_row(Table.Transaction, row)
            key = '|'.join(str(a.value) for a in where)
            if len(self._db.fetch(Table.Transaction, where=where)) > 1:
                if count > 0 and key_p and key_p != key:
                    return True
                count += 1
            else:
                count = 0  # reset
            key_p = key
        return False

    def export_doubles(self, rows) -> int:
        count = 0
        out_rows = []
        for row in rows:
            # Only when there are 2 consecutive doubles
            where = model.get_pk_atts_from_row(Table.Transaction, row)
            if len(self._db.fetch(Table.Transaction, where=where)) > 1:
                count += 1
                where_clause = ', '.join([str(att.value) for att in where])
                message = f'Record "{Color.GREEN}{where_clause}{Color.NC}" lijkt een {Color.ORANGE}dubbel{Color.NC}.'
                out_rows.append([remove_color_code(message)])
                if self._verbose:
                    self._result.add_message(message, severity=Sev.Warning)
        # - Write to csv
        csvm.write_rows(out_rows, open_mode='w', data_path=f'{self._session.output_dir}{DOUBLES_CSV}')
        return count

    def import_bank_transactions(self, db):
        """
        a. Import user bank transactions into table Transactions in the original raw format.
        b. Add non-existing CounterAccounts to the database (with booking=EMPTY)
        """
        counter_accounts = {}
        # Populate transaction files (Checking has been done before).
        self._validation_manager.validate_config_dir(CF_INPUT_DIR)
        TransactieFiles = sorted(self._validation_manager.transaction_files.values(), key=lambda m: m.key)
        if len(TransactieFiles) > 1 and not self._session.CLI_mode:
            from src.VL.Windows.General.MessageBox import message_box
            message_box(f'Een moment geduld a.u.b...\n'
                        f'{len(TransactieFiles)} bestanden met {TRANSACTIONS} moeten worden geimporteerd.\n'
                        f'Daarna wordt de app opnieuw gestart.')

        # a. Import transactie csv files in DB.
        #    N.B. Validation has been done already.
        self._amounts_are_signed = False
        for i in range(len(TransactieFiles)):
            # Read csv file definition
            M = TransactieFiles[i]
            colnos = M.colno_mapping  # { model_colno: csv_colno } (zero_based)
            d = {TX_dict[m]: c for m, c in colnos.items()}
            # Read csv file
            csv_rows = csvm.get_rows(data_path=M.path, delimiter=M.delimiter)
            # Bepaal datum formaat over max. 1000 regels.
            date_format = try_to_get_date_format(csv_rows, d[FD.Date], M.path)
            # Format rows
            out_rows = []
            for row in csv_rows:
                amount = toFloat(row[d[FD.Amount]], comma_source=comma_source)
                # Sanitize amount
                row[d[FD.Amount]] = amount
                # Remember if amount is signed
                if not self._amounts_are_signed and amount < 0:
                    self._amounts_are_signed = True
                # Remember Accounts
                self._account_io.add_account_to_cache(row[d[FD.Account_number]])
                # Remember CounterAccounts (first one)
                counter_account_number = row[d[FD.Counter_account_number]]
                if counter_account_number and counter_account_number not in counter_accounts:
                    counter_accounts[counter_account_number] = [row[d[FD.Name]], row[d[FD.Comments]]]
                # Map csv to model
                # (optional csv col is substituted by EMPTY, e.g. "TransactionCode" not present)
                out_row = []
                for colno, att_name in TX_dict.items():
                    if colno in colnos:
                        out_row.append(row[colnos[colno]])
                    else:
                        # Derived: date format
                        out_row.append(date_format if att_name == FD.Date_format else EMPTY)
                # Add row
                out_rows.append(out_row)  # More redundant fields may have been added
            # Insert into Transaction
            db.insert_many(Table.Transaction, out_rows, add_audit_values=True, pgm=PGM)

        # b. Add accounts.
        self._account_io.persist_accounts()
        iban = self._account_io.get_current_iban(CM.get_config_item(CF_IBAN))
        CM.set_config_item(CF_IBAN, iban)

        # b. Add counter accounts (without booking yet).
        for counter_account_number, row in counter_accounts.items():
            self._counter_account_manager.insert(
                CounterAccount(
                    counter_account_number,
                    account_name=row[0],
                    first_comment=row[1])
            )
        return

    def _set_search_booking_codes(self, te_row):
        self._unique_account_bban.add(te_row[TE_dict[FD.Account_bban]])
        self._unique_year.add(te_row[TE_dict[FD.Year]])
        self._unique_counter_account_id.add(te_row[TE_dict[FD.Counter_account_id]])
        self._unique_transaction_code.add(te_row[TE_dict[FD.Transaction_code]])
        self._unique_mutation_type.add(te_row[TE_dict[FD.Transaction_type]])

    def _save_combo_data(self):
        FF = Table.FlatFiles
        # Account number
        [self._db.insert(FF, [FD.Account_number, value], pgm=PGM) for value in self._unique_account_bban if value]

        # Year
        [self._db.insert(FF, [FD.Year, value], pgm=PGM) for value in self._unique_year if value]

        # Counter account number (incl. *Leeg* and *Niet leeg*)
        [self._db.insert(FF, [FD.Counter_account_number, self._db.fetch_value(
            Table.CounterAccount, name=FD.Counter_account_number, where=[Att(FD.ID, value)])], pgm=PGM)
         for value in self._unique_counter_account_id if value > 0]
        self._db.insert(FF, [FD.Counter_account_number, LEEG], pgm=PGM)
        self._db.insert(FF, [FD.Counter_account_number, NIET_LEEG], pgm=PGM)

        # Transaction code
        [self._db.insert(FF, [FD.Transaction_code, value], pgm=PGM) for value in self._unique_transaction_code if value]

        # Transaction type
        [self._db.insert(FF, [FD.Transaction_type, value], pgm=PGM) for value in self._unique_mutation_type if value]

        # Booking type
        [self._unique_booking_types.add(r[bk_dict[FD.Booking_type]]) for r in self._db.fetch(Table.BookingCode)]
        [self._db.insert(FF, [FD.Booking_type, value], pgm=PGM) for value in self._unique_booking_types if value]

    def create_enriched_mutations(self, db):
        """
        Populate table TransactionEnriched from Transactions and CounterAccount.
        """
        mapping = {}
        derived = {}

        # get enriched { name: colno } sorted by colno (zero-based)

        TX_dict_1 = model.get_colno_per_att_name(Table.Transaction, zero_based=False)
        for name, seqno in TE_dict.items():
            if name in TX_dict_1:
                mapping[seqno] = TX_dict_1[name]
            else:
                derived[name] = [seqno, UNKNOWN]
                mapping[seqno] = -1

        c_bban = TE_dict[FD.Account_bban]
        c_counter_account_id = TE_dict[FD.Counter_account_id]
        c_booking_code = TE_dict[FD.Booking_code]
        c_booking_id = TE_dict[FD.Booking_id]
        c_name = TE_dict[FD.Name]
        c_comments = TE_dict[FD.Comments]
        c_transaction_code = TE_dict[FD.Transaction_code]
        c_add_sub = TE_dict[FD.Add_Sub]
        c_amount = TE_dict[FD.Amount]
        c_amount_signed = TE_dict[FD.Amount_signed]
        c_remarks = TE_dict[FD.Remarks]
        i_date = TX_dict_1[FD.Date]
        i_date_format = TX_dict_1[FD.Date_format]

        out_rows = []
        TX_rows = db.fetch(Table.Transaction, mode=FetchMode.WholeTable)

        # Transactie
        for row in TX_rows:
            out_row = [row[mapping[c_enriched]] for name, c_enriched in TE_dict.items()]

            # Datum: convert to yyyy-mm-dd
            date = format_date(row[i_date], input_format=row[i_date_format], output_format='YMD')
            if not is_formatted_ymd(date):
                raise GeneralException(f'{PGM}: Datum "{row[i_date]}" is ongeldig in {Table.Transaction}.')

            date_target = int(date.replace('-', EMPTY))
            out_row[1] = date_target
            out_row[TE_dict[FD.Year]] = int(date[:4])
            out_row[TE_dict[FD.Month]] = int(date[5:7])

            # Rekening (Bban)
            bban, iban = self._account_io.get_bban_iban_from_account_number(row[TX_dict_1[FD.Account_number]])
            out_row[c_bban] = bban

            # Naam
            out_row[c_name] = row[TX_dict_1[FD.Name]]

            # Tegenrekening (FK)
            counter_account_number = row[TX_dict_1[FD.Counter_account_number]]
            counter_account_bban = ACM.get_BBAN_from_IBAN(counter_account_number)
            counter_account_id = db.fetch_id(
                Table.CounterAccount, where=[Att(FD.Counter_account_number, counter_account_number)])
            out_row[c_counter_account_id] = counter_account_id

            # Comments
            comments = out_row[c_comments]

            # Bedrag (unsigned)
            amount = str(out_row[c_amount])
            add_sub = out_row[c_add_sub]
            sign = EMPTY  # No sign = "+"
            if self._amounts_are_signed:
                if '-' in amount:
                    sign = '-'
                    amount = amount.strip('-')
            else:  # Separate Af/Bij column (ING)
                if add_sub.lower() not in ('bij', 'credit'):
                    sign = '-'

            out_row[c_amount] = float(amount)

            # BedragSigned
            amount_signed = f'{sign}{amount}'
            out_row[c_amount_signed] = float(amount_signed)

            # Add/sub
            if not out_row[c_add_sub]:
                out_row[c_add_sub] = AMOUNT_MINUS if sign else AMOUNT_PLUS

            # Boeking
            # - Bedrag lager dan drempel
            if threshold_to_other_min < out_row[c_amount] < threshold_to_other_pos:
                protected_maingroup = OTHER_COSTS if sign else OTHER_REVENUES
                booking_code = BCM.get_protected_booking_code(protected_maingroup)
            else:
                # - Initialiseer eerst vanuit UserMutations, dan CounterAccount, dan SearchTerms, dan BookingCode
                booking_code = UMC.get_booking_code(bban, str(date_target), counter_account_number, comments)
                if not booking_code:
                    booking_code = ACM.get_booking_code(counter_account_bban)
                if not booking_code:
                    booking_code = STM.get_booking_code(row[TX_dict_1[FD.Name]], row[TX_dict_1[FD.Comments]])
                if not booking_code:
                    booking_code = BCM.get_booking_code(row[TX_dict_1[FD.Name]], row[TX_dict_1[FD.Comments]])

                # - Nog geen boeking en ook geen tegenrekening, dan "Overige uitgaven"/"Overige inkomsten".
                if not booking_code and not counter_account_number:
                    protected_maingroup = OTHER_COSTS if sign else OTHER_REVENUES
                    booking_code = BCM.get_protected_booking_code(protected_maingroup)

            booking_id = db.fetch_id(Table.BookingCode, where=[Att(FD.Booking_code, booking_code)]) \
                if booking_code else 0

            out_row[c_booking_code] = booking_code  # derived
            out_row[c_booking_id] = booking_id

            te_key = get_te_key(bban, date_target, counter_account_number, comments)
            # Remarks
            out_row[c_remarks] = UMC.get_remarks(te_key)

            # Betaalpas data
            if out_row[c_transaction_code] == 'BA':
                kwargs = {'mededelingen': comments}
                if comments.lower().lstrip().startswith('pasvolgnr'):
                    pasvolgnr, date, tijd = self._get_pas_data('A', **kwargs)
                elif comments.find('***') > -1:
                    pasvolgnr, date, tijd = self._get_pas_data('B', **kwargs)
                else:
                    pasvolgnr, date, tijd = self._get_pas_data('C', **kwargs)
                if out_row[c_booking_id] <= 0:  # Nog geen rekening booking
                    out_row[c_booking_id] = 0
            else:
                pasvolgnr, date, tijd = EMPTY, EMPTY, EMPTY

            out_row[TE_dict[FD.Transaction_date]] = date
            out_row[TE_dict[FD.Transaction_time]] = tijd

            # Add the ME-row
            out_rows.append(out_row)

            # Set search bookings
            self._set_search_booking_codes(out_row)

        sorted_out_rows = sorted(out_rows, key=lambda r: r[0])
        db.insert_many(Table.TransactionEnriched, sorted_out_rows, add_audit_values=True, pgm=PGM)

    def _get_pas_data(self, format_char, mededelingen) -> (str, str, str):
        pasvolgnr, datum, tijd = EMPTY, EMPTY, EMPTY  # output

        if format_char == 'A':
            # Example (Mededelingen):
            # "Pasvolgnr:001 13-01-2020 23:37 Transactie:12Z9V4 Term:1F7Z01"
            # " PASVOLGNR 002     23-05-2019 14:51 TRANSACTIENR 1234567"
            s = mededelingen.lower().find('pasvolgnr')
            if s > -1:
                pasvolgnr, s = self._get_pasvolgnr(mededelingen, s + 10)
                datum, tijd = self._get_datum_tijd(mededelingen)

        # Example: (Mededelingen)
        # "1234567 MIJN CLUB LEIDEN>LEIDEN PASNR ***A001 23-06-2019 16:39 TRANSACTIENR 1234567"
        elif format_char == 'B':
            s = mededelingen.find('***')
            if s > -1 and s + 4 < len(mededelingen):
                pasvolgnr, e = self._get_pasvolgnr(mededelingen, s + 4)
                datum, tijd = self._get_datum_tijd(mededelingen)

        # Example (Naam, Mededelingen):
        # "19-07-99 18:12 BETAALAUTOMAAT", " SUPERMARKT / AMSTERDAM 001 123456 1234567 ING BANK NV PASTRANSACTIES"
        else:
            s = 0
            while pasvolgnr == EMPTY and -1 < s < len(mededelingen):
                s = mededelingen.find(BLANK, s)
                if s > -1:
                    s = skip_blanks(mededelingen, s)
                    pasvolgnr, s = self._get_pasvolgnr(mededelingen, s)
            datum, tijd = self._get_datum_tijd(mededelingen)

        return pasvolgnr, datum, tijd

    @staticmethod
    def _get_pasvolgnr(value, s) -> (str, int):
        pasvolgnr = EMPTY
        # look for 3 consecutive numbers...
        e = s
        while e < len(value) and '0' <= value[e] <= '9':
            e += 1
        # ... followed by space
        if e - s == 3 and e < len(value) and value[e] == BLANK:
            pasvolgnr = value[s:e]  # found!
        # Skip blanks
        e = skip_blanks(value, e)
        return pasvolgnr, e

    @staticmethod
    def _get_datum_tijd(value) -> (str, str):
        datum, tijd = EMPTY, EMPTY  # output

        # Find "-xx-"
        s = 0
        found = False
        while not found and -1 < s < len(value):
            s = value.find('-', s)
            if s == -1:
                break
            if s < len(value) - 3 and value[s + 3] == '-':
                found = True
            else:
                s += 1  # skip '-'

        if found:
            dd = value[s - 2:s]
            mm = value[s + 1:s + 3]
            jjjj = f'20{value[s + 4:s + 6]}' if value[s + 6] == BLANK else f'{value[s + 4:s + 8]}'

            d = f'{jjjj}{mm}{dd}'
            if isInt(d):
                # Transactiedatum
                datum = f'{jjjj}-{mm}-{dd}'

            # Tijd
            s = (s + 7) if value[s + 6] == BLANK else (s + 9)
            hh = value[s:s + 2]
            mm = value[s + 3:s + 5]
            t = f'{hh}{mm}'
            if isInt(t):
                # Transactietijd
                tijd = f'{hh}:{mm}'

        return datum, tijd
