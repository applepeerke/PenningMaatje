#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
import os
from os import listdir
from random import randrange, choice

from src.BL.Validator import Validator
from src.DL.Config import CF_INPUT_DIR, CF_OUTPUT_DIR
from src.DL.Model import FD, Model
from src.DL.Table import Table
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.Const import EXT_CSV, BLANK
from src.GL.Functions import toFloat
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import normalize_dir
from src.VL.Views.PopUps.Input import Input
from src.VL.Views.PopUps.PopUp import PopUp

PGM = 'DemoManager'
EXTRACT_WORDS = 'EXTRACT_WORDS'
CREATE_DEMO = 'CREATE_DEMO'

csvm = CsvManager()

TX_dict = Model().get_att_name_per_colno(Table.Transaction)


class DemoManager:

    def __init__(self, input_dirname=None, output_dirname=None, wordlist_path=None):
        super().__init__()
        self._result = Result()
        self._validation_manager = Validator()
        self._counter_account_numbers = {}
        self._input_dirname = input_dirname
        self._output_dirname = normalize_dir(output_dirname)
        self._demo_dirname = normalize_dir(f'{self._output_dirname}Demo', create=True) if self._output_dirname else None
        self._wordlist_path = wordlist_path
        self._names = {}  # Trx file "Naam"
        self._wordlist = {}  # Mapping of words (manually maintained)
        self._words_to_translate = {}
        self._words_to_translate_upper = {}
        self._extracted_words = {}  # Extracted words, per "Naam" and "Opmerkingen"
        self._total_amounts_changed_randomly = 0
        self._total_sensitive_replacements_made = 0
        self._messages = []

    """ A. Extract words """

    def extract_all_words(self):
        self._process_transaction_files(EXTRACT_WORDS)
        return Result()

    """ B. Create Demo """

    def create(self) -> Result:
        """
        Create a 1:1 transaction set of csv files in a demo folder.
        Convert the amount randomly and also privacy related names.
        """
        valid = self._process_transaction_files(EXTRACT_WORDS)
        if not self._words_to_translate:
            self._messages.append(
                'Vertalen van gevoelige informatie is zinloos. Er is nog geen  gevoelige informatie bepaald.')
            valid = False
        if valid:
            self._messages.append(f'De demo wordt gemaakt vanuit folder "{self._input_dirname}"')
            self._messages.append(f'Er kunnen {len(self._words_to_translate)} gevoelige woorden vertaald worden.')
            self._messages.append(f'De demo wordt gemaakt in folder "{self._demo_dirname}"')
            if listdir(self._demo_dirname):
                self._messages.append(f'\nDe uitvoer folder is niet leeg.\nDoorgaan?')
        if PopUp().confirm('create_demo', '\n'.join(self._messages)) and valid:
            self._process_transaction_files(CREATE_DEMO)
        return Result()

    """ General """

    def _process_transaction_files(self, process_action) -> bool:
        # Validate input and get transaction files
        TransactieFiles = self._initialize(process_action)

        # Convert transaction csv files.
        for i, M in enumerate(TransactieFiles):
            # Read csv file definition
            colnos = M.colno_mapping  # { model_colno: csv_colno } (zero_based)
            d = {TX_dict[m]: c for m, c in colnos.items()}
            # Read csv file
            csv_rows = csvm.get_rows(data_path=M.path, delimiter=M.delimiter, include_header_row=True)
            out_rows = [csv_rows[0]]
            details = csv_rows[1:]
            if process_action == CREATE_DEMO:
                if not self._wordlist:
                    raise GeneralException(f'{PGM}: No privacy terms have been defined yet.')
                # Format rows, convert data
                out_rows.extend([self._get_converted_row(d, row) for row in details])
                # Write csv file
                csvm.write_rows(
                    out_rows, open_mode='w',
                    data_path=f'{normalize_dir(self._demo_dirname)}{os.path.basename(M.path)}')
            elif process_action == EXTRACT_WORDS:
                [self._extract_words_from_row(d, row) for row in details]
            else:
                raise NotImplementedError(f'{PGM}: Process action "{process_action}" has not been implemented.')

        if process_action == CREATE_DEMO:
            print(f'{len(TransactieFiles)} bestanden zijn geschreven in "{self._demo_dirname}"')
            print(f'{self._total_amounts_changed_randomly} bedragen zijn met een random percentage gewijzigd.')
            print(f'{self._total_sensitive_replacements_made} gevoelige woorden zijn vertaald.')

        elif process_action == EXTRACT_WORDS:
            keys = list(self._extracted_words)
            valid = True
            for key in keys:
                out_rows = sorted([[word] for word in self._extracted_words[key] if word not in self._wordlist])
                if out_rows:
                    valid = False
                    path = f'{normalize_dir(self._output_dirname)}sensitive_data_for_{key.replace(BLANK, "_")}{EXT_CSV}'
                    if csvm.write_rows(out_rows, open_mode='w', data_path=path):
                        self._messages.append(f'{len(out_rows)} woorden zijn geschreven in "{path}".'
                                              f'\nVoeg deze toe aan {self._wordlist_path}.')
            if valid:
                merged_words = set()
                for key in keys:
                    merged_words.update(self._extracted_words[key])
                self._messages.append(
                    f'Alle {len(merged_words)} woorden in de bank transacties zijn aanwezig in de woordenlijst '
                    f'(van {len(self._wordlist)} woorden).')
        return True

    def _initialize(self, process_action) -> dict:
        # a. Validate parameters
        self._validate_input(process_action)

        # b. Get word list with alias names
        self._wordlist = {row[0]: row[1] for row in csvm.get_rows(data_path=self._wordlist_path)}
        self._words_to_translate = {word: alias for word, alias in self._wordlist.items() if alias}
        self._words_to_translate_upper = {
            word.upper(): alias.upper() for word, alias in self._words_to_translate.items()}

        # c. Get Transaction .csv files
        self._result = self._validation_manager.validate_config_dir(CF_INPUT_DIR, self._input_dirname)
        return sorted(self._validation_manager.transaction_files.values(), key=lambda m: m.key) \
            if self._result.OK else {}

    def _validate_input(self, process_action):
        if not self._input_dirname:
            self._input_dirname = Input().get_folder(CF_INPUT_DIR)
        if not self._output_dirname:
            self._output_dirname = Input().get_folder(CF_OUTPUT_DIR)
        self._output_dirname = normalize_dir(self._output_dirname)

        if not self._wordlist_path:
            self._wordlist_path = Input().get_path(CF_OUTPUT_DIR)
        self._input_dirname = normalize_dir(self._input_dirname)

        if not self._input_dirname or not os.path.isdir(self._input_dirname):
            raise GeneralException(f'{PGM}: Invalid input directory "{self._input_dirname}"')

        if process_action == CREATE_DEMO and (not self._demo_dirname or not os.path.isdir(self._demo_dirname)):
            raise GeneralException(f'{PGM}: Invalid output directory "{self._demo_dirname}"')
        elif not self._output_dirname or not os.path.isdir(self._output_dirname):
            raise GeneralException(f'{PGM}: Invalid output directory "{self._output_dirname}"')

        if not self._wordlist_path or not os.path.isfile(self._wordlist_path):
            raise GeneralException(f'{PGM}: Invalid word list path "{self._wordlist_path}"')

        if (process_action == CREATE_DEMO and self._input_dirname == self._demo_dirname) or \
                self._input_dirname == self._output_dirname:
            raise GeneralException(f'{PGM}: Output dir must not be equal to input dir "{self._input_dirname}"')

    """ A. Extract words """

    def _extract_words_from_row(self, d, row):
        self._extract_words_from_cell(FD.Name, row[d[FD.Name]])
        self._extract_words_from_cell(FD.Comments, row[d[FD.Comments]])

    def _extract_words_from_cell(self, key, cell) -> str:
        if cell:
            if key not in self._extracted_words:
                self._extracted_words[key] = set()
            words = cell.split()
            [self._extracted_words[key].add(word) for word in words if self._is_sensitive(word)]
        return cell

    @staticmethod
    def _is_sensitive(word) -> bool:
        """ word must be alpha, lowercase or title, no special chars """
        word_upper = word.upper()
        return len(word) > 2 and word.isalpha() and word != word_upper and word_upper not in ('TRUE', 'WAAR')

    """ B. Create Demo """

    def _get_converted_row(self, d, row) -> list:
        # Sanitize amount and +/- random amount.
        row[d[FD.Amount]] = self._get_converted_amount(
            row[d[FD.Amount]], row[d[FD.Counter_account_number]], row[d[FD.Name]])
        # Sanitize private cells: "name" and "comments".
        return self._sanitize_sensitive_info(d, row)

    def _get_converted_amount(self, amount, counter_account_number, name) -> str:
        amount = toFloat(amount)
        if counter_account_number:
            # Create a random % per counter account to lower or higher amounts (20-50%)
            if counter_account_number not in self._counter_account_numbers:
                self._counter_account_numbers[counter_account_number] = randrange(20, 50) * choice([1, -1])
            diff = round(amount * self._counter_account_numbers[counter_account_number] / 100, 2)
        elif name:
            if name not in self._names:
                self._names[name] = randrange(20, 50) * choice([1, -1])
            diff = round(amount * self._names[name] / 100, 2)
        else:
            raise GeneralException(f'{PGM}: No counter account number or name present in transaction.')
        if diff != 0:
            self._total_amounts_changed_randomly += 1
        return str(toFloat(amount + diff, comma_source='.'))

    def _sanitize_sensitive_info(self, d, row) -> list:
        row[d[FD.Name]] = self._sanitize_cell(row[d[FD.Name]])
        row[d[FD.Comments]] = self._sanitize_cell(row[d[FD.Comments]])
        return row

    def _sanitize_cell(self, cell) -> str:
        self._cell = cell
        [self._replace(word, alias) for word, alias in self._words_to_translate.items() if self._cell]
        [self._replace(word, alias) for word, alias in self._words_to_translate_upper.items() if self._cell]
        if self._cell != cell:
            self._total_sensitive_replacements_made += 1
        return self._cell

    def _replace(self, word, alias):
        self._cell = self._cell.replace(word, alias)


if __name__ == '__main__':
    input_folder = "/Users/Peter/Documents/Peter/Adm/Bank/Finad/Input/Bankafschriften"
    output_folder = "/Users/Peter/Documents/Peter/Adm/Bank/Finad/BankApp_output"
    word_list = "/Users/Peter/Apps/PenningMaatje/UT/Basisfolder/Input/DemoWoordenlijst.csv"

    while True:
        action = input('Actie (1=Extract words, 2=Create demo, None=Exit):')
        if not action:
            break
        if str(action) == '1':
            DemoManager(input_folder, output_folder, word_list).extract_all_words()
            break
        elif str(action) == '2':
            DemoManager(input_folder, output_folder, word_list).create()
            break
