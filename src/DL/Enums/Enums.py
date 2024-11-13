from src.DL.Lexicon import SEARCH_RESULT, REVENUES, COSTS, OVERBOOKINGS, ANNUAL_ACCOUNT, ANNUAL_ACCOUNT_PLUS, \
    PERIODIC_ACCOUNT


class Summary:
    SearchResult = SEARCH_RESULT
    AnnualAccount = ANNUAL_ACCOUNT
    PeriodicAccount = PERIODIC_ACCOUNT
    AnnualAccountPlus = ANNUAL_ACCOUNT_PLUS

    @staticmethod
    def values():
        return [SEARCH_RESULT, ANNUAL_ACCOUNT, PERIODIC_ACCOUNT, ANNUAL_ACCOUNT_PLUS]


class BookingType:
    Costs = COSTS
    Revenues = REVENUES
    Overbookings = OVERBOOKINGS

    @staticmethod
    def values():
        return [REVENUES, COSTS, OVERBOOKINGS]

