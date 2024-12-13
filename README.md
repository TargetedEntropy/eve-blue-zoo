# Eve Online Blue Zoo

This is portal for Eve Online players with features focused for users with multiple characters.

It uses the Eve Online SSO & ESI, Flask and the [Flask Dashboard Black](https://appseed.us/product/black-dashboard/flask/) template.

<br />

> Features

- Registration via Eve SSO
- [Associate multiple characters](https://i.imgur.com/rZzhefv.png)
- [Dashboard view of all associated added Characters](https://i.imgur.com/A8EwnC7.png)
- [Display consolidated Mining Ledger details across Characters](https://i.imgur.com/BuMGulJ.png)
- [SkillPoint Farm Notifications](https://i.imgur.com/U54ukKu.png) via [Discord Private DM](https://i.imgur.com/VONyNX4.png)
- [Consolidated Item Blueprint view across Characters](https://i.imgur.com/BG6egoJ.png)
<br />

> Dependencies
 - SQL Dumps: https://www.fuzzwork.co.uk/dump/latest/
    - invItems.sql.bz2 
    - invTypes.sql.bz2
    - invGroups.sql.bz2
    - industryBlueprints.sql.bz2
    - mapSolarSystems.sql.bz2
    - mapRegions.sql.bz2
 - [Eve Online Developer Application](https://developers.eveonline.com/applications)

<br />

## How to use it

```bash
$ # Get the code
$ git clone https://github.com/TargetedEntropy/eve-blue-zoo.git
$ cd eve-blue-zoo
$
$ # Virtualenv modules installation (Unix based systems)
$ virtualenv env
$ source env/bin/activate
$
$ # Virtualenv modules installation (Windows based systems)
$ # virtualenv env
$ # .\env\Scripts\activate
$
$ # Copy the env.sample and edit it
$ cp env-sample .env
$ vi .env
$
$ # Install modules - SQLite Database
$ pip3 install -r requirements.txt
$
$ # OR with PostgreSQL connector
$ # pip install -r requirements-pgsql.txt
$
$ # Set the FLASK_APP environment variable
$ (Unix/Mac) export FLASK_APP=run.py
$ (Windows) set FLASK_APP=run.py
$ (Powershell) $env:FLASK_APP = ".\run.py"
$
$ # Set up the DEBUG environment
$ # (Unix/Mac) export FLASK_ENV=development
$ # (Windows) set FLASK_ENV=development
$ # (Powershell) $env:FLASK_ENV = "development"
$
$ # Start the application (development mode)
$ # --host=0.0.0.0 - expose the app on all network interfaces (default 127.0.0.1)
$ # --port=5000    - specify the app port (default 5000)  
$ flask run --host=0.0.0.0 --port=5000
$
$ # Access the dashboard in browser: http://127.0.0.1:5000/
```

## ✨ Credits & Links

- 👉 [Eve Online Swagger](https://esi.evetech.net/)
- 👉 [Eve Online Developer Application](https://developers.eveonline.com/applications)
- 👉 [EsiPy](https://github.com/Kyria/EsiPy)
- 👉 [Flask Dashboard Black](https://appseed.us/product/black-dashboard/flask/)

