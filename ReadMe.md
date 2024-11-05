# Introductie
PenningMaatje is een boeking dashboard voor bankafschriften. Je kunt ze van boekingscodes voorzien en er in zoeken. 
De jaarrekening en zoekresultaten kun je exporteren naar CSV bestanden. Deze kun je in Excel verder verwerken.

PenningMaatje werkt lokaal en is daardoor privé en veilig.

# Vereisten
De bankafschriften van de volgende banken worden ondersteund.
* Bunq
* ING
* Rabobank
* Triodos

De bankafschriften moeten in csv formaat zijn gedownload en in een input folder staan. 

PenningMaatje is getest op MacOS en Windows 10/11. Het zou ook op linux en Windows 7 moeten werken.

# Vereisten
- Python 3.8
- Als je de app in Python wilt starten heb je ook nodig:
  - pysimplegui
  - dateutil

# Start de app
## a. Als App
De app, dat wil zeggen het dashboard met alle mogelijkheden, kun je starten met 
- PenningMaatje.app (Mac)
- PenningMaatje.exe (Windows) 


## b. Vanaf een opdrachtregel
Algemeen: start eerst de terminal (Mac) of command prompt (Windows), 
en ga met `cd` naar de PenningMaatje folder.

Typ `python penningmaatje.py` en druk op `Enter`.

De eerste keer toont de app een popup om de input en output folders vast te stellen.
### Maak de Jaarrekening
Typ `python pm.py` en druk op `Enter`.

Typ `python pm.py -h` en druk op `Enter` voor hulp bij de parameters. Met parameters kun je het jaar, 
en de invoer- en uitvoerfolders wijzigen. 


Er wordt een jaarrekening gemaakt in een csv bestand. Standaard is dat het huidige jaar. Hierin komt de realisatie te staan over de maanden die in de bankafschriften aanwezig zijn. 
Als er in input bestand resources/Jaarrekening.csv ook begrotingen staan worden deze geïntegreerd. 

Ook worden de bankafschriften per maand en per kwartaal geëxporteerd in csv bestanden. 

De bankafschriften worden standaard geïmporteerd uit folder `..PenningMaatje/Input`. 
De overzichten worden gemaakt in `../PenningMaatje/Output`.


