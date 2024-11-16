from copy import copy

from src.BL.Functions import get_BBAN_from_IBAN
from src.DL.Config import CF_IBAN, CF_ROWS_TRANSACTION, CF_REMARKS
from src.DL.DBDriver.Att import Att
from src.DL.IO.AccountIO import AccountIO
from src.DL.IO.TransactionsIO import TransactionsIO
from src.DL.IO.YearMonthIO import YearMonthIO
from src.DL.Model import FD
from src.DL.Table import Table
from src.VL.Data.Constants.Enums import Pane
from src.DL.Lexicon import TRANSACTIONS, CMD_IMPORT_TE
from src.VL.Models.BaseModel import model, CM, DD
from src.VL.Models.BaseModelTable import BaseModelTable
from src.VL.Models.Panes.Accounts import Accounts
from src.VL.Models.Panes.Log import Log
from src.VL.Models.Panes.Months import Months
from src.VL.Models.Panes.TransactionsEnriched import TransactionsEnriched
from src.VL.Models.Panes.Years import Years
from src.VL.Models.TransactionModel import TransactionModel
from src.VL.Views.ConfigurationView import ConfigurationView
from src.GL.Const import EMPTY
from src.GL.Enums import MessageSeverity
from src.GL.Result import Result

TE_dict = model.get_colno_per_att_name(Table.TransactionEnriched, zero_based=False)


class MainModel(BaseModelTable):

    @property
    def account_numbers(self):
        return self._account_numbers

    @property
    def models(self):
        return self._models

    @property
    def dashboard_refreshed(self):
        return self._dashboard_refreshed

    """
    Setters
    """

    @account_numbers.setter
    def account_numbers(self, value):
        self._account_numbers = value

    @dashboard_refreshed.setter
    def dashboard_refreshed(self, value):
        self._dashboard_refreshed = value

    def __init__(self):
        super().__init__(table_name=None)
        self._result = Result()
        self._account_numbers = []
        self._account_io = None
        self._year_month_io = None
        self._transactions_io = None
        self._dashboard_refreshed = False
        self._search_mode = False

        self._models = {
            Pane.AC: Accounts(),
            Pane.YS: Years(),
            Pane.MS: Months(),
            Pane.TE: TransactionsEnriched(),
            Pane.TX: TransactionModel(),
            Pane.CF: ConfigurationView(),
            Pane.LG: Log()
        }

    def start_io(self):
        """ After controller has set the db in the session """
        self._account_io = AccountIO()
        self._year_month_io = YearMonthIO()
        self._transactions_io = TransactionsIO()

    def build_all_panes(self):
        self.refresh_dashboard()
        self.refresh_table_rows(Pane.LG)

    def refresh_dashboard(
            self, pane=None, pane_row_no=0, TX_only=False, search_mode=False, duration_change=False) -> Result:
        """
        Full refresh: No pane and no pane_row_no.
        Partly refresh: pane and pane_row_no are specified after clicking on a row.
        """
        self._result = Result()
        self._search_mode = search_mode
        self._dashboard_refreshed = True

        # Data
        # - Year month overview (after changing account number)
        year_row_no = pane_row_no
        month_row_no = pane_row_no if pane == Pane.MS \
            else CM.get_config_item(f'CF_ROW_NO_{Pane.MS}', 0) if pane == Pane.TE \
            else 0

        # In search_empty mode the TE_row may have been disappeared.
        if pane == Pane.TX and CM.is_search_for_empty_booking_mode():
            pane_row_no = 0

        # Full refresh
        if not pane:
            if not duration_change:
                # Populate combos
                DD.initialize_combos()
                self._account_numbers = DD.get_combo_items(FD.Iban)
                # Other account number selected, or 1st time: set new iban.
                iban = self._account_io.get_current_iban(CM.get_config_item(CF_IBAN))
                CM.set_config_item(CF_IBAN, iban)
            # Set year/month data
            self._year_month_io.refresh_data()
            if not duration_change:
                # Get rid of pending values in config
                CM.set_config_item(CF_REMARKS, EMPTY)
                # Set the months row from the first month with data and a reasonable transaction window.
                year_row_no, month_row_no = self._initialize_ym_and_set_transaction_pane()

        # Config
        if duration_change:
            # Use current row numbers
            year_row_no = CM.get_config_item(f'CF_ROW_NO_{Pane.YS}')
            month_row_no = CM.get_config_item(f'CF_ROW_NO_{Pane.MS}')
        else:
            # Set current row numbers
            if not pane or pane == Pane.YS:
                CM.set_config_item(f'CF_ROW_NO_{Pane.YS}', year_row_no)
                CM.set_config_item(f'CF_ROW_NO_{Pane.MS}', 0)
                CM.set_config_item(f'CF_ROW_NO_{Pane.TE}', 0)
            elif not pane or pane == Pane.MS:
                CM.set_config_item(f'CF_ROW_NO_{Pane.MS}', month_row_no)
                CM.set_config_item(f'CF_ROW_NO_{Pane.TE}', 0)
            elif not pane or pane == Pane.TE:
                CM.set_config_item(f'CF_ROW_NO_{Pane.TE}', pane_row_no)

        # Set pane data
        # - Years
        if not pane:
            row_no = year_row_no if duration_change else -1
            count_Y = self._refresh_target_table_rows(Pane.YS, pane_target=Pane.YS, current_row_no=row_no)
            if count_Y == 0 and self._result.OK:
                self._result.add_message(
                    f'Er zijn nog geen {TRANSACTIONS} geïmporteerd.\n'
                    f'Hiervoor kun je op de knop "{CMD_IMPORT_TE}" drukken (de dubbele pijl).',
                    severity=MessageSeverity.Warning)
        # - Months
        if not pane or pane == Pane.YS:
            self._refresh_target_table_rows(Pane.YS, pane_target=Pane.MS, current_row_no=year_row_no)

        # - Transactions
        if not pane or (pane in (Pane.YS, Pane.MS, Pane.TE) and not TX_only):
            count = self._refresh_target_table_rows(Pane.MS, pane_target=Pane.TE, current_row_no=month_row_no)
            if self._result.OK and CM.is_search_for_empty_booking_mode():
                self._result.text = f'{count} {TRANSACTIONS} gevonden.'

        # - Transaction (detail pane)
        current_row_no = CM.get_config_item(f'CF_ROW_NO_{Pane.TE}', 0)
        self.set_transaction_pane(current_row_no=current_row_no)
        return self._result

    def _initialize_ym_and_set_transaction_pane(self) -> (int, int):
        # a. Get the most recent year for the selected account number
        bban = get_BBAN_from_IBAN(CM.get_config_item(CF_IBAN))
        TE_row = DD.db.fetch_one(
            Table.TransactionEnriched,
            where=[Att(FD.Account_bban, bban)],
            order_by=[[Att(FD.Date), 'DESC']])
        if not TE_row:
            return 0, 0

        # b. Get the month with the most "reasonable" amount of month transactions.
        max_rows = CM.get_config_item(CF_ROWS_TRANSACTION, 0)
        year = int(TE_row[TE_dict[FD.Year]])
        month_counts = [self._get_month_transactions_count(bban, year, month) for month in range(1, 13)]
        month = 0
        # b1. Get first month having defined transaction window size
        for c in range(12):
            if 0 < max_rows <= month_counts[c]:
                month = c + 1
                break
        # b2. Not found (only few transactions): Get month with most transactions.
        if month == 0:
            month_count_max = 0
            for c in range(12):
                if month_counts[c] > month_count_max:
                    month_count_max = month_counts[c]
                    month = c + 1
        # Now month must be present.
        if month == 0:
            return 0, 0

        month_row_no = month - 1

        # c. Get year-row-no.
        years = DD.db.select(Table.Year, name=FD.Year, order_by=[[Att(FD.Year), 'DESC']])
        year_row_no = years.index(year)

        # d. Set transaction pane
        self.models[Pane.TE].set_data(DD.fetch_set(
            Table.TransactionEnriched, where=[Att(FD.Year, year), Att(FD.Month, month)]))

        return year_row_no, month_row_no

    @staticmethod
    def _get_month_transactions_count(bban, year, month) -> int:
        return len(DD.fetch_set(
            Table.TransactionEnriched,
            where=[Att(FD.Account_bban, bban), Att(FD.Year, year), Att(FD.Month, month)]))

    def _refresh_target_table_rows(self, pane_current, pane_target=None, current_row_no=0) -> int:
        """
        Smart refresh of target view model rows. Based on click on current pane row.
        """
        # Set pane data
        # Master panes via logical key if there is a target pane,
        # else just refresh the whole table (like booking).
        view_current = self.models.get(pane_current)
        view_target = self.models.get(pane_target)

        # Fetch current row
        row = self._get_current_row(pane_current, current_row_no)
        pk_target = self._get_pk_target(view_current, view_target, pane_target, row)

        if not view_target:
            view_target = view_current

        # Fetch target rows
        rows = self._get_table_rows(view_target.table_name, pk_target)

        # Set view model
        count = view_target.set_data(rows)
        if count == 0:
            self._result.add_message('Geen gegevens gevonden.')
        return count

    def _get_table_rows(self, table_name, pk) -> list:
        # - In search mode, re-search transactions
        if table_name == Table.TransactionEnriched and self._search_mode:
            self._transactions_io.search()
            # Header + details
            rows = [model.get_report_colhdg_names(Table.TransactionEnriched)]
            rows.extend(self._transactions_io.rows)
            return rows

        # Other tables
        rows = DD.fetch_set(table_name, where=pk)  # Incl. header
        if table_name == Table.Month:
            rows = self._pad_month_rows(rows)
        return rows

    @staticmethod
    def _get_pk_target(view_current, view_target, pane_target, row):
        pk_current, pk_target = None, None
        if pane_target == Pane.TE:
            pk_target = [Att(FD.Account_bban, get_BBAN_from_IBAN(CM.get_config_item(CF_IBAN)))]
        if view_target:
            pk_current = model.get_pk_atts_from_row(view_current.table_name, row)
            if pk_target:
                pk_target.extend(pk_current)
            else:
                pk_target = pk_current
        return pk_target

    @staticmethod
    def _pad_month_rows(rows):
        # Pad Month pane
        net_rows_count = len(rows) - 1  # Skip header
        if 0 < net_rows_count < 12:  # Skip header
            last_row = copy(rows[len(rows) - 1])
            for i in range(3, len(last_row) - 6):  # All amounts to 0
                last_row[i] = 0
            # Pad rows until 12 is reached
            for i in range(net_rows_count, 12):
                last_row[2] = i + 1
                rows.append(last_row)
        return rows

    def set_current_row_in_config(self, pane, row_no) -> int:
        Id = self._get_current_row_id(pane, row_no)
        CM.set_config_item(f'CF_ID_{pane}', Id)
        if row_no > -1:
            CM.set_config_item(f'CF_ROW_NO_{pane}', row_no)
        return Id

    def _get_current_row_id(self, pane, row_no) -> int:
        view = self.models.get(pane)
        if view and view.rows and -1 < row_no < len(view.rows):
            return view.rows[row_no][0]
        return 0

    def _get_current_row(self, pane, row_no) -> list:
        Id = self.set_current_row_in_config(pane, row_no)
        return DD.fetch_1_row(table_name=self.models.get(pane).table_name, where=[Att(FD.ID, value=Id)])

    def set_transaction_pane(self, current_row_no=None):
        """
        Smart refresh of Transaction pane. Based on click on Transactions row.
        """
        # Populate View model
        row = self._get_current_row(Pane.TE, current_row_no)
        self.models[Pane.TX].set_data(row)

    def refresh_table_rows(self, pane, where=None):
        vm = self.models[pane]
        vm.set_data(DD.fetch_set(vm.table_name, where=where))

    """
    Log 
    """

    def refresh_log(self):
        self.refresh_table_rows(Pane.LG)
