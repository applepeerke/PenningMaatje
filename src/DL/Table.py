#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------------------------
# Author      : Peter Heijligers
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2018-12-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Lexicon import COUNTER_ACCOUNTS, SEARCH_TERMS, BOOKING_CODES, ANNUAL_ACCOUNT, OPENING_BALANCE


class Table(object):
    Account = 'Account'
    AnnualAccount = 'AnnualAccount'  # Jaarrekening
    BookingCode = 'BookingCode'
    CounterAccount = 'CounterAccount'
    FlatFiles = 'FlatFiles'  # Key-value pairs in combo boxes (boeking, tegenrekening, transactie-soort etc.)
    Log = 'Log'
    Month = 'Month'
    OpeningBalance = 'OpeningBalance'
    SearchTerm = 'SearchTerm'
    Transaction = 'BankTransaction'   # Transaction is a reserved db word
    TransactionEnriched = 'TransactionEnriched'
    TransactionType = 'TransactionType'
    Year = 'Year'

    table_code = {
        Account: 'AC',
        AnnualAccount: 'AA',
        BookingCode: 'BC',
        CounterAccount: 'CA',
        FlatFiles: 'FF',
        Log: 'LG',
        Month: 'MO',
        OpeningBalance: 'OB',
        SearchTerm: 'ST',
        Transaction: 'TX',
        TransactionEnriched: 'TE',
        Year: 'YE'
    }

    # Description (for user-defined tables)
    description = {
        CounterAccount: COUNTER_ACCOUNTS,
        SearchTerm: SEARCH_TERMS,
        BookingCode: BOOKING_CODES,
        AnnualAccount: ANNUAL_ACCOUNT,
        OpeningBalance: OPENING_BALANCE
    }
