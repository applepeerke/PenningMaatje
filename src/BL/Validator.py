#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from os import listdir

from src.DL.Config import CF_INPUT_DIR, CF_OUTPUT_DIR
from src.DL.Objects.TransactionFile import TransactionFile
from src.DL.Report import *
from src.DL.Lexicon import TRANSACTION, TRANSACTIONS, CSV_FILE, INPUT_DIR, OUTPUT_DIR
from src.GL.BusinessLayer.ConfigManager import ConfigManager, get_label
from src.GL.BusinessLayer.CsvManager import CsvManager
from src.GL.BusinessLayer.SessionManager import APP_OUTPUT_DIR
from src.GL.Const import APP_NAME
from src.GL.Enums import MessageSeverity as Sev, ResultCode
from src.GL.Result import Result
from src.GL.Validate import *


CM = ConfigManager()


class Validator:

    @property
    def transaction_files(self):
        return self._transaction_files

    def __init__(self):
        self._transaction_files = {}
        self._invalid_input_filenames = []

    def validate_config_dir(self, cf_code, dirname=None) -> Result:
        """
        Input folder requested:
        - Only valid bank transaction files may exist in the bank transactions folder (CF_INPUT_DIR).
        Output folder requested:
        - No bank transaction files may exist in the output folder (CF_OUTPUT_DIR).
        - Output folder must not be equal to the input folder.
        dirname: Only for "create demo" purpose
        """
        result = Result()
        self._transaction_files = {}

        # Folder naam
        if not dirname:
            dirname = CM.get_config_item(cf_code)
        title = f'{get_label(cf_code)} is ongeldig:\n"{dirname}".\n\n'

        if not dirname or not os.path.isdir(dirname):
            result.add_message(f'{title}Dit is geen folder.', Sev.Error)
            return result

        # Access control
        if not os.access(dirname, os.X_OK | os.W_OK):
            result.add_message(f'{title}Je hebt niet de nodige rechten voor deze folder.', Sev.Error)
            return result

        csv_files, valid_csv_files = [], []
        problem, solution = EMPTY, EMPTY
        self._transaction_files = {}

        if cf_code == CF_INPUT_DIR:
            # Selected input dir contains only valid csv files?
            self._invalid_input_filenames = []
            [self._validate_input_dir_filename(f) for f in [f for f in listdir(dirname)]]
            if len(self._invalid_input_filenames) == 1:
                problem = f'Probleem:\nDe folder bevat ongeldig item "{self._invalid_input_filenames[0]}".'
            elif self._invalid_input_filenames:
                bullets = '\n    o  '.join([f for f in self._invalid_input_filenames])
                problem = f'Probleem:\nDe folder bevat ongeldige items zoals:\n    o  {bullets}'

            if not problem:
                # Analyze bank transaction csv files
                try:
                    # Create sorted dir-list of valid files (only header-check, not in-depth)
                    csv_files = sorted([f for f in listdir(dirname) if f.lower().endswith('.csv')])
                    valid_csv_files = [self._get_valid_transaction_csv_file(dirname, f) for f in csv_files]
                    if len(csv_files) == len(valid_csv_files):
                        self._transaction_files = {M.key: M for M in valid_csv_files}
                except GeneralException as ge:
                    problem = f'Probleem:\n{ge.message}'
                    if cf_code == CF_INPUT_DIR:
                        solution = f'Kies een folder die alleen {CSV_FILE}en met geldige {TRANSACTIONS} bevat.\n'

        elif cf_code == CF_OUTPUT_DIR:
            input_dir = CM.get_config_item(CF_INPUT_DIR)
            if not input_dir:
                problem = f'Probleem:\n{INPUT_DIR} is nog niet geconfigureerd.'
            elif dirname == input_dir:
                problem = f'Probleem:\n{OUTPUT_DIR} is gelijk aan {INPUT_DIR}.'

        if not problem:
            if cf_code == CF_INPUT_DIR:
                solution = f'Kies een folder die alleen {CSV_FILE}en met geldige {TRANSACTIONS} bevat.\n'
                if not self._transaction_files:
                    # No valid bank transaction csv files found
                    problem = f'Probleem:\nGeen geldige {TRANSACTIONS} gevonden in\n"{dirname}"'
                elif self._transaction_files and len(csv_files) != len(self._transaction_files):
                    problem = f'Probleem:\nEr zijn andere bestanden dan {TRANSACTIONS} in de folder gevonden.'
            elif cf_code == CF_OUTPUT_DIR and csv_files:
                problem = f'Probleem:\nEr zijn {CSV_FILE}en in de folder gevonden.\n' \
                          f'Dit zou een mogelijke {INPUT_DIR} kunnen zijn.'
                solution = f'Kies een folder die geen {CSV_FILE}en bevat.\n'

        # Success`
        if not problem:
            if cf_code == CF_INPUT_DIR:
                text = 'geldig bestand' if len(self._transaction_files) == 1 else 'geldige bestanden'
                result.add_message(
                    f'{len(self._transaction_files)} {text} met {TRANSACTIONS} gevonden.', severity=Sev.Completion)
            return result

        # Fail
        if solution:
            solution = f'\n\nOplossing:\n{solution}'
        result.add_message(f'{title}{problem}{solution}', Sev.Error)
        return result

    @staticmethod
    def validate_move_output_dir(from_dir, to_dir) -> Result:
        from src.VL.Views.PopUps.PopUp import PopUp
        # Validate
        box_text = f'{OUTPUT_DIR} wijzigen is niet mogelijk.\n\nReden:\n'
        cancel_reason = None
        prefix = f'Subfolder "{APP_OUTPUT_DIR}" moet hierbij verplaatst worden\n'\
                 f'  van  "{from_dir}"\n  naar "{to_dir}".\n\n'
        path_parts = to_dir.split(f'{slash()}')
        if to_dir.startswith(from_dir) or from_dir.startswith(to_dir):
            cancel_reason = f'{prefix}Verplaatsen is niet mogelijk binnen het eigen folder pad.'
        elif APP_OUTPUT_DIR in path_parts:
            cancel_reason = f'{prefix}Folder "{APP_OUTPUT_DIR}" bestaat echter al in "{to_dir}".'

        if cancel_reason:
            return Result(ResultCode.Canceled, text=f'{box_text}{cancel_reason}')

        # Dialog
        if not PopUp().confirm(
                'Move_output_subfolder',
                title=f'{OUTPUT_DIR} wijzigen',
                text=f'De {OUTPUT_DIR} zal worden gewijzigd\n'
                     f'  van:  "{from_dir}"\n  naar: "{to_dir}".\n\n'
                     f'De {APP_NAME} gegevens (in subfolder "{APP_OUTPUT_DIR}") zullen naar de nieuwe {OUTPUT_DIR} '
                     f'verplaatst worden.\n'):
            return Result(ResultCode.Canceled)
        return Result()

    def _validate_input_dir_filename(self, filename, max_items=10):
        if not filename.lower().endswith('.csv') and not filename.startswith('.'):
            if len(self._invalid_input_filenames) < max_items:
                self._invalid_input_filenames.append(filename)
            elif len(self._invalid_input_filenames) == max_items:
                self._invalid_input_filenames.append('...')

    @staticmethod
    def _get_valid_transaction_csv_file(input_dir, filename) -> TransactionFile:
        """
        Validate transaction csv file. Check header and no of columns in every row.
        """
        path = f'{input_dir}{filename}'

        # 1. Get rows
        delimiter = ',' if len(CsvManager().get_first_row(data_path=path, delimiter=';')) == 1 else ';'
        inp_rows = CsvManager().get_rows(include_header_row=True, data_path=path, delimiter=delimiter)
        if not inp_rows or len(inp_rows) < 2:
            raise GeneralException(f'Geen regels gevonden in {TRANSACTION} "{filename}".')
        if any(len(r) != len(inp_rows[0]) for r in inp_rows):
            raise GeneralException(f'Niet alle regels bevatten even veel cellen in bestand "{filename}".')

        # 2. Check header
        try:
            colno_mapping = Report().get_transaction_file_colno_mapping(inp_rows[0])
        except GeneralException as e:
            raise GeneralException(f'Ongeldig bestand "{filename}" gevonden.\n{e}')

        return TransactionFile(path, colno_mapping=colno_mapping, delimiter=delimiter)
