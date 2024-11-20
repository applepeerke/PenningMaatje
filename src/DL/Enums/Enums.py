from src.DL.Lexicon import SEARCH_RESULT, REVENUES, COSTS, OVERBOOKINGS, TEMPLATE_ANNUAL_ACCOUNT, \
    TEMPLATE_ANNUAL_ACCOUNT_PLUS, PERIODIC_ACCOUNTS, TEMPLATE_REALISATION_PER_BOOKING_CODE


class Summary:
    SearchResult = SEARCH_RESULT
    AnnualAccount = TEMPLATE_ANNUAL_ACCOUNT
    PeriodicAccount = PERIODIC_ACCOUNTS
    AnnualAccountPlus = TEMPLATE_ANNUAL_ACCOUNT_PLUS
    RealisationPerBookingCode = TEMPLATE_REALISATION_PER_BOOKING_CODE

    @staticmethod
    def values():
        return [
            SEARCH_RESULT, TEMPLATE_ANNUAL_ACCOUNT, PERIODIC_ACCOUNTS, TEMPLATE_ANNUAL_ACCOUNT_PLUS,
            TEMPLATE_REALISATION_PER_BOOKING_CODE
        ]


class BookingType:
    Costs = COSTS
    Revenues = REVENUES
    Overbookings = OVERBOOKINGS

    @staticmethod
    def values():
        return [REVENUES, COSTS, OVERBOOKINGS]

