from src.DL.Lexicon import SEARCH_RESULT, REVENUES, COSTS, OVERBOOKINGS, ANNUAL_ACCOUNT


class Summary:
    SearchResult = SEARCH_RESULT
    AnnualAccount = ANNUAL_ACCOUNT

    @staticmethod
    def values():
        return [SEARCH_RESULT, ANNUAL_ACCOUNT]


class BookingType:
    Costs = COSTS
    Revenues = REVENUES
    Overbookings = OVERBOOKINGS

    @staticmethod
    def values():
        return [REVENUES, COSTS, OVERBOOKINGS]

