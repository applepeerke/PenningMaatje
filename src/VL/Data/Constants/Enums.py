class Pane(object):
    AC = 'Rekeningen'
    CA = 'Tegenrekeningen'
    CF = 'Configuratie'
    BS = 'Boekingen'
    BK = 'Boeking'
    LG = 'Log'
    LO = 'Layout opties'
    MS = 'Maanden'
    SC = 'Zoeken in transacties'
    SS = 'Zoektermen'
    ST = 'Zoekterm'
    TE = 'Transacties verrijkt'
    TX = 'Transacties'
    YS = 'Jaren'


class OutputType(object):
    MB = 'Message box'
    SB = 'Status bar'


class BoxCommand(object):
    Add = 'Toevoegen'
    Update = 'Wijzigen'
    Delete = 'Verwijderen'
    Display = 'Tonen'
    Rename = 'Hernoemen'


class WindowType(object):
    Main = 'Main'
    Detail = 'Detail'
    Detail_with_statusbar = 'Detail'
    PopUp = 'PopUp'
    PopUp_with_statusbar = 'PopUp_with_statusbar'
    List = 'List'
    ListItem = 'ListItem'

    detail = [Detail, ListItem, PopUp]
    has_statusbar = [Main, List, Detail_with_statusbar, PopUp_with_statusbar]
