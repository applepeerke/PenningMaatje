import PySimpleGUI as sg

from src.DL.Config import *
from src.DL.Lexicon import ACCOUNT_NUMBER, LOG, DASHBOARD
from src.DL.Model import FD
from src.DL.Table import Table
from src.DL.UserCsvFiles.Cache.BookingCodeCache import Singleton as BookingCodeCache
from src.VL.Data.Constants.Color import *
from src.VL.Models.MainModel import MainModel
from src.VL.Views.BaseView import BaseView

BCM = BookingCodeCache()


class MainView(BaseView):

    def __init__(self, model: MainModel):
        super().__init__()
        self._model = model

    def get_view(self) -> list:
        VM_JO = self._model.models[Pane.YS]
        VM_MO = self._model.models[Pane.MS]
        VM_TE = self._model.models[Pane.TE]
        VM_TX = self._model.models[Pane.TX]
        VM_LG = self._model.models[Pane.LG]

        x_TX = max(len(self._get_label(ACCOUNT_NUMBER)),
                   len(self._get_label(DATE)),
                   len(self._get_label(NAME)),
                   len(self._get_label(AMOUNT)),
                   len(self._get_label(COMMENTS)),
                   len(self._get_label(COUNTER_ACCOUNT)),
                   len(self._get_label(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION)),
                   len(self._get_label(REMARKS)),
                   len(self._get_label(TRANSACTION_CODE)),
                   len(self._get_label(TRANSACTION_DATE)),
                   len(self._get_label(TRANSACTION_TIME)),
                   len(self._get_label(MUTATION_TYPE)),
                   )
        self._statusbar_width = 90
        # Dashboard
        layout_dashboard = [
            # Buttons and Status bar
            self.multi_frame('Dashboard_top', [

                self.multi_frame(FRAME_TOP_BUTTONS_OPTIONAL, [
                    self.frame(FRAME_SEARCH_COUNTER_ACCOUNTS_WITHOUT_BOOKING, [
                        [self.button(CMD_SEARCH_FOR_EMPTY_BOOKING_CODE, p=5)]],
                               border_width=3, p=2, relief=sg.RELIEF_RAISED),
                    [self.button(
                        CMD_SUMMARY, button_text=EMPTY, tip=True,
                        image_filename=f'{self._session.get_image_path("summary.png")}', transparent=True, p=0,
                        image_subsample=self._CM.get_config_item(CF_IMAGE_SUBSAMPLE))],
                    [self.button(
                        CMD_SEARCH, button_text=EMPTY, tip=True,
                        image_filename=f'{self._session.get_image_path("magnifying_glass.png")}', transparent=True, p=0,
                        image_subsample=self._CM.get_config_item(CF_IMAGE_SUBSAMPLE))],
                    [self.button(
                        CMD_UNDO, button_text=EMPTY, tip=True,
                        image_filename=f'{self._session.get_image_path("undo.png")}', transparent=True, p=0,
                        image_subsample=self._CM.get_config_item(CF_IMAGE_SUBSAMPLE)
                    )],
                ], p=2),
                [self.button(
                    CMD_CONFIG, button_text=EMPTY, tip=True,
                    image_filename=f'{self._session.get_image_path("settings.png")}', transparent=True, p=0,
                    image_subsample=self._CM.get_config_item(CF_IMAGE_SUBSAMPLE))],
                [self.button(
                    CMD_IMPORT_TE, button_text=EMPTY, tip=True,
                    image_filename=f'{self._session.get_image_path("refresh.png")}', transparent=True, p=0,
                    image_subsample=self._CM.get_config_item(CF_IMAGE_SUBSAMPLE))],
                self.frame(FRAME_TOP_RIGHT, [
                    self.frame(FRAME_IBAN, [
                        self.combo(CF_IBAN, [x for x in self._model.DD.get_combo_items(FD.Iban)],
                                   background_color=COLOR_BACKGROUND_DISABLED, text_color=COLOR_TEXT_DISABLED),
                    ], border_width=0, p=0, expand_x=True, justify='R'),
                ], border_width=0, p=2, expand_x=True, justify='L'),
            ], expand_x=True),
            # Jaren
            self.multi_frame(FRAME_PANE_YEAR_MONTH, [
                self.frame('Jaar_maand', [
                    self.frame(FRAME_YEAR, [
                        [self.label(name=PANE_YEARS, font=self.get_font(addition=2))],
                        [sg.Table(k=self.key_of(Table.Year), values=VM_JO.rows,
                                  headings=VM_JO.header,
                                  visible_column_map=VM_JO.visible_column_map,
                                  col_widths=VM_JO.col_widths,
                                  auto_size_columns=False,
                                  justification=TABLE_JUSTIFY,
                                  num_rows=min(max(VM_JO.table_height, 1), VM_JO.num_rows),
                                  selected_row_colors=TABLE_COLOR_SELECTED_ROW, enable_click_events=True,
                                  background_color=TABLE_COLOR_BACKGROUND, text_color=TABLE_COLOR_TEXT,
                                  font=self.get_font('TABLE'))],
                    ], border_width=1, p=0),

                    # Maanden
                    self.frame(FRAME_MONTH, [
                        [self.label(name=PANE_MONTHS, font=self.get_font(addition=2))],
                        [sg.Table(k=self.key_of(Table.Month), values=VM_MO.rows,
                                  headings=VM_MO.header,
                                  visible_column_map=VM_MO.visible_column_map,
                                  col_widths=VM_MO.col_widths,
                                  auto_size_columns=False,
                                  justification=TABLE_JUSTIFY,
                                  num_rows=min(max(VM_MO.table_height, 1), VM_MO.num_rows),
                                  selected_row_colors=TABLE_COLOR_SELECTED_ROW, enable_click_events=True,
                                  background_color=TABLE_COLOR_BACKGROUND, text_color=TABLE_COLOR_TEXT,
                                  font=self.get_font('TABLE'))],
                    ], border_width=1, p=0),
                ], border_width=1),

                # Transactie
                self.frame(FRAME_PANE_TRANSACTION, [
                    [self.label(name=PANE_TRANSACTION, font=self.get_font(addition=2))],
                    self.frame('Transaction attributes', [
                        self.inbox(ACCOUNT_NUMBER, dft=VM_TX.account_number, x=x_TX, disabled=True),
                        self.inbox(DATE, dft=VM_TX.date, x=x_TX, disabled=True),
                        self.frame('Frame_name', [
                            self.inbox(NAME, dft=VM_TX.name, x=x_TX, x2=512, disabled=True),
                        ], expand_x=True, p=0),
                        self.inbox(AMOUNT, dft=VM_TX.amount, x=x_TX, disabled=True),
                        self.frame(FRAME_COMMENTS, [
                            [self.label(COMMENTS, x=x_TX, text_color=COLOR_LABEL_DISABLED),
                             self.multi_line(COMMENTS, dft=VM_TX.comments, x=512, y=3, disabled=True), ]
                        ], expand_x=True, p=0),
                        self.inbox(COUNTER_ACCOUNT, dft=VM_TX.counter_account, x=x_TX, disabled=True),

                        # Enabled attributes
                        self.frame(FRAME_MUTATION_ENABLED, [
                            # - Boeking
                            self.frame(FRAME_TRANSACTION_BOOKING, [
                                self.combo(CF_COUNTER_ACCOUNT_BOOKING_DESCRIPTION,
                                           [x for x in BCM.get_booking_code_descriptions(include_protected=False)],
                                           dft=VM_TX.booking_description, x=x_TX,
                                           background_color=COLOR_BACKGROUND_DISABLED),
                            ], p=0, border_width=0),
                            # - Bijzonderheden
                            self.multi_frame(MULTI_FRAME_REMARKS, [
                                self.frame(FRAME_REMARKS, [
                                    [self.label(REMARKS, x=x_TX, text_color=TEXT_COLOR, tip=self.get_tooltip(CF_REMARKS)),
                                     self.multi_line(CF_REMARKS, dft=VM_TX.remarks, x=512, y=2, evt=True,
                                                     background_color=COLOR_BACKGROUND_DISABLED)]], p=0),
                            ], p=0, expand_x=True, border_width=0),
                        ], p=0),

                        # Rest
                        self.multi_frame('-REST-', [
                            self.frame('-REST_L', [
                                self.inbox(TRANSACTION_CODE, dft=VM_TX.transaction_code, x=x_TX, disabled=True),
                                self.inbox(MUTATION_TYPE, dft=VM_TX.mutation_type, x=x_TX, disabled=True),
                            ], p=0, border_width=0),
                            self.frame(FRAME_TX_DATETIME, [
                                self.inbox(TRANSACTION_DATE, dft=VM_TX.transaction_date, x=x_TX, disabled=True),
                                self.inbox(TRANSACTION_TIME, dft=VM_TX.transaction_time, x=x_TX, disabled=True),
                            ], p=0, border_width=0, visible=False),
                        ], p=0, border_width=0),
                    ], border_width=1, expand_x=True),
                ], border_width=1, expand_x=True),
            ], p=0, expand_x=True),
            # Transacties
            self.frame(FRAME_PANE_TRANSACTIONS, [
                [self.label(name=PANE_TRANSACTIONS, font=self.get_font(addition=2))],
                [sg.Table(k=self.key_of(Table.TransactionEnriched), values=VM_TE.rows,
                          headings=VM_TE.header,
                          visible_column_map=VM_TE.visible_column_map,
                          col_widths=VM_TE.col_widths,
                          auto_size_columns=False,
                          justification=TABLE_JUSTIFY,
                          num_rows=min(max(VM_TE.table_height, 1), VM_TE.num_rows),
                          selected_row_colors=TABLE_COLOR_SELECTED_ROW,
                          enable_click_events=True,
                          background_color=TABLE_COLOR_BACKGROUND,
                          text_color=TABLE_COLOR_TEXT,
                          font=self.get_font('TABLE'),
                          expand_y=True,
                          expand_x=True)]
            ], border_width=1, expand_y=True, expand_x=True),
        ]
        # Boekingen
        layout_bookings = [
            self.frame(
                'Help bij boekingen',
                [[self.button(CMD_HELP_WITH_BOOKING, button_text=' Help ', transparent=True, p=5)]],
                border_width=1),
            # - Boekingen
            self.frame(FRAME_BOOKING, [
                [self.label(name=MAINTAIN, font=self.get_font(addition=2))],
                # -  Boekingen onderhouden
                self.multi_frame(FRAME_WORK_WITH_BOOKINGS, [
                    self.button_frame(CMD_WORK_WITH_BOOKING_CODES),
                ]),
                self.button_frame(CMD_WORK_WITH_SEARCH_TERMS, p=10),
                self.button_frame(CMD_WORK_WITH_OPENING_BALANCES, p=10)
            ], border_width=1)
        ]

        # Log
        layout_log = [
            # Button Consistentie
            self.multi_frame('Log buttons', [
                self.frame(CMD_CONSISTENCY, [
                    [self.button(CMD_CONSISTENCY, tip=True)]], border_width=3, p=2, relief=sg.RELIEF_RAISED),
            ]),
            self.frame(FRAME_PANE_LOG, [
                [self.label(name=LOG, font=self.get_font(addition=2))],
                [sg.Table(k=self.key_of(Table.Log),
                          values=VM_LG.rows,
                          headings=VM_LG.header,
                          visible_column_map=VM_LG.visible_column_map,
                          col_widths=VM_LG.col_widths,
                          auto_size_columns=False,
                          justification=TABLE_JUSTIFY,
                          num_rows=min(max(VM_LG.table_height, 1), VM_LG.num_rows),
                          selected_row_colors=TABLE_COLOR_SELECTED_ROW, enable_click_events=True,
                          background_color=TABLE_COLOR_BACKGROUND,
                          text_color=TABLE_COLOR_TEXT,
                          font=self.get_font('TABLE'),
                          expand_x=True, expand_y=True),
                 ],
            ], border_width=1, expand_x=True, expand_y=True),
        ]

        # The TabGroup layout - WTyp.IN must contain only Tabs
        tab_group_layout = [[
            sg.Tab(DASHBOARD, layout_dashboard, key=DASHBOARD),
            sg.Tab(BOOKING_CODE, layout_bookings, key=BOOKING_CODE),
            sg.Tab(TAB_LOG, layout_log, key=TAB_LOG),
        ]]

        # The window layout - defines the entire window
        layout = [
            [sg.StatusBar(EMPTY, key=STATUS_MESSAGE, p=(5, 5), size=(
                self._statusbar_width, 1), expand_x=True, relief=sg.RELIEF_SUNKEN)],
            [sg.TabGroup(tab_group_layout, enable_events=True, key=TAB_GROUP, font=self.get_font(addition=2))],
            [sg.Text(key=EXPAND, font='ANY 1', pad=(0, 0))]]
        return layout
