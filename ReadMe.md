# Introductie
PenningMaatje is een boeking dashboard voor bankafschriften. Je kunt ze van boekingscodes voorzien en er in zoeken. 
De jaarrekening en zoekresultaten kun je exporteren naar csv bestanden. Deze kun je in Excel verder verwerken.

PenningMaatje werkt lokaal en is daardoor privé en veilig.

# Vereisten
De bankafschriften van de volgende banken worden ondersteund.
* Bunq
* ING
* Rabobank
* Triodos

De bankafschriften moeten in csv formaat zijn gedownload en in een input folder staan. Deze mag geen andere bestanden bevatten.

PenningMaatje is getest op MacOs en Windows 10/11. Het zou ook op Linux en Windows 7 moeten werken.

# Vereisten
- Python 3.8
- Als je de app in Python wilt starten heb je ook nodig:
  - pysimplegui

# Start de app
## a. Als App
De app, dat is het dashboard met alle mogelijkheden, start je met 
- PenningMaatje.app (Mac)
- PenningMaatje.exe (Windows) 


## b. Vanaf een opdrachtregel
Algemeen: start eerst de terminal (Mac) of command prompt (Windows), 
en ga met `cd` naar de PenningMaatje folder.

Typ `python penningmaatje.py` en druk op `Enter`.

De eerste keer toont de app een popup om de input en output folders vast te stellen.
### Maak de Jaarrekening
Typ `python pm.py` en druk op `Enter`.

Typ `python pm.py -h` en druk op `Enter` voor hulp bij de parameters. Met parameters kun je o.a. het jaar, 
en de invoer- en uitvoerfolders wijzigen. 

Als je niets opgeeft worden de bankafschriften geïmporteerd uit folder `..PenningMaatje/Input`. 
De overzichten worden dan gemaakt in `../PenningMaatje/Output`.

Er wordt een jaarrekening gemaakt in een csv bestand. Hierin komt de realisatie te staan over de maanden die in de bankafschriften aanwezig zijn. 
Als er in input bestand `resources/userdata/Jaarrekening.csv` ook begrotingen staan worden deze geïntegreerd. 

Daarnaast worden de bankafschriften per maand en per kwartaal geëxporteerd in csv bestanden. 



