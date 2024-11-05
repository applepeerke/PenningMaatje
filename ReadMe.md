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
- python 3.8
- pysimplegui (alleen als je de app met python wilt starten)

# Starten
## a. Vanaf een opdrachtregel
### Start PenningMaatje
Start Terminal (Mac) of Command (op Windows).\
Ga naar de PenningMaatje folder. 
Typ `python geldmaatje.py` en druk op `Enter`.
De app start op met een popup om de configuratie in te stellen.
### Maak een jaarrekening
Start Terminal (Mac) of Command (op Windows).\
Ga naar de PenningMaatje folder. 
Typ `python pm.py` en druk op `Enter`.
De bankafschriften worden geïmporteerd uit folder `..PenningMaatje/Input`. 
De overzichten worden gemaakt in `../PenningMaatje/Output`.