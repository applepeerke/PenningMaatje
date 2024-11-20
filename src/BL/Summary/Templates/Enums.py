from src.DL.Model import FD


class HeaderVars(object):
    Year = 'JAAR'
    YearPrevious = 'VORIG JAAR'
    AccountNumber = 'REKENING NUMMER'
    AccountDescription = 'REKENING OMSCHRIJVING'
    Month = 'MAAND'
    MonthFrom = 'MAAND_VAN'
    MonthTo = 'MAAND_TM'
    OpeningBalance = 'BEGINSALDO'
    ClosingBalance = 'EINDSALDO'
    TotalRevenues = 'TOTAAL INKOMSTEN'
    TotalCosts = 'TOTAAL UITGAVEN'

    descriptions = {
        Year: 'Jaar',
        YearPrevious: 'Vorig jaar',
    }

    values = [
        AccountDescription, AccountNumber, Year, YearPrevious, Month, OpeningBalance, ClosingBalance,
        TotalRevenues, TotalCosts
    ]


class DetailVars(object):
    Types = 'TYPEN'
    Maingroups = 'HOOFDGROEPEN'
    Subgroups = 'SUBGROEPEN'
    Amounts = 'BEDRAGEN'
    Dates = 'DATUMS'
    Descriptions = 'OMSCHRIJVINGEN'
    BookingCodes = 'BOEKING CODES'
    BookingDescriptions = 'BOEKING OMSCHRIJVINGEN'
    Revenues = 'INKOMSTEN'
    Costs = 'UITGAVEN'

    values = [
        Types, Maingroups, Subgroups, Amounts, Dates, Descriptions, Revenues, Costs, BookingCodes,
        BookingDescriptions
    ]
    mapping = {
        Types: FD.Booking_type,
        Maingroups: FD.Booking_maingroup,
        Subgroups: FD.Booking_subgroup,
        Amounts: FD.Amount_signed,
        Dates: FD.Date,
        Costs: FD.Amount_signed,
        Revenues: FD.Amount_signed,
        Descriptions: FD.Comments,
        BookingCodes: FD.Booking_code,
        BookingDescriptions: FD.Booking_code  # Not in model, derived from code
    }


class DetailTotalVars(object):
    General = 'GENERAAL'
    Total = 'TOTAAL'
    TotalGeneral = f'TOTAAL {General}'
    TotalType = f'TOTAAL {DetailVars.Types}'
    TotalMaingroup = f'TOTAAL {DetailVars.Maingroups}'

    values = [TotalType, TotalMaingroup, TotalGeneral]
