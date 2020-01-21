# WhatTheFridge

# Projectplan
## Samenvatting
Met behulp van onze applicatie kan je recepten vinden met ingrediënten die je in huis hebt. De ontbrekende ingrediënten worden getoond als lijst. Je kan de resultaten filteren op vlees, vis en groentes. Je kan ook je favoriete recepten opslaan en delen met een andere gebruiken. Zo bespaart men geld en gaan we voedselverspilling tegen. Je kan de resultaten sorteren op bereidingstijd, prijsklasse en aantal extra benodigde ingrediënten. Deze applicatie is voornamelijk bedoeld voor studenten en helpt voedselverspilling tegen te gaan.
## Features
- **Vind een recept op basis van ingrediënten (automatisch aanvullen bij zoeken ingredient)**
- **Stel (eventueel) een boodschappenlijst op met de ontbrekende ingrediënten**
- Knop om boodschappen toe te voegen aan Albert Heijn-lijst.
- Filter resultaten op groente, vlees en vis
- **Sla je favoriete recepten op**
- **Deel recepten met andere gebruikers**
- **Sorteren op bereidingstijd, prijsklasse en aantal extra benodigde ingrediënten**

_Vetgedrukt = MVP_
## Afhankelijkheden
### API
Food API: [https://spoonacular.com/food-api](https://slack-redir.net/link?url=https%3A%2F%2Fspoonacular.com%2Ffood-api)
AH API: [https://www.ah.nl/partnerprogramma](https://slack-redir.net/link?url=https%3A%2F%2Fwww.ah.nl%2Fpartnerprogramma)
### Frameworks
- Bootstrap
- flask
- Javascript (+JQuery)
- GitHub
- Code Editing Software met Git-support
### Concurrentie
- Receptenzoeker.com
- Smulweb
- AH Recepten
### Uitdagingen
API-integraties, filteren, sharing, zoekresultaten verwerken (sorteren?)

# Technisch ontwerp
## Controllers
- "/" - Home (not logged in) - splashpage (GET)
- "/register" - Register (not logged in) - registratie voor gebruikers (GET/POST)
- "/login" - Login (not logged in) - inloggen (GET/POST)
- "/search" - Zoekopdracht - ingredienten invullen en zoek button (GET)
- "/results" - Zoekresultaten - resultaten van zoekopdracht tonen (POST)
- "/profile" - Profiel - bewerken profiel, voorkeur qua dieet, wachtwoord (GET/POST)
- "/favorites" - Favorieten - bekijk opgeslagen recepten (GET)
- "/support" - FAQ/Contact - veelgestelde vragen/contact e-mail (GET)

_Default is authentication required_

## Views

Zie prototype op Invision voor schetsen: [open](https://whatthefridge.invisionapp.com/public/share/C4Y2UJFW5)

## Models/helpers
- login_required - herleid gebruiker naar login pagina als authenticatie vereist is
- server_error - verzorgt error pagina bij fout
- lookup - doet een aanvraag bij de FoodAPI
- lookup_recipe(id) - zoekt in de FoodAPI een recept op basis van een ID.

## Plugins en frameworks
- Bootstrap - [Docs](https://getbootstrap.com/docs/4.4/getting-started/introduction/)
- Flask - [Docs](http://flask.palletsprojects.com/en/1.1.x/)
- Jinja - [Docs](https://jinja.palletsprojects.com/en/2.10.x/)
- JQuery (+ JS) - [Docs](https://api.jquery.com/)

## ERD
![ERD](https://github.com/StijnMichiels00/WhatTheFridge/blob/master/ERD-WhatTheFridge2.png)
In deze database structure zijn twee tabellen te zien. In de bovenste tabel worden
gebruikers geregistreerd door middel van een user id, username, een gehasd wachtwoord
en een exclusion voor een bepaald dieet (dit kan later worden aangepast bij de profielpagina).
In de onderste tabel worden recepten opgeslagen. Verschillende gebruikers kunnen meerdere
gerechten opslaan per gebruiker. Vandaar de aanwezigheid van een many to many verband.