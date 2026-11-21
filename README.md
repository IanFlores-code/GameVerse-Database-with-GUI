GAMEVERSE WALLET MANAGER - HOW TO RUN
=====================================

NEED INSTALLED
--------------
- PostgreSQL 18 (or PostgreSQL 10+) + pgAdmin 4
- Python 3.10 or newer (Windows: tick "Add Python to PATH" when installing)


1. SET UP THE DATABASE (pgAdmin or psql)
----------------------------------------
a) Open pgAdmin 4, right-click Databases > Create > Database, and name it: gameverse
b) Click gameverse > Tools > Query Tool
c) Open the root file  gameverse_schema.sql  and execute it (F5)
d) Verify the schema and seed data loaded:
      SELECT COUNT(*) FROM gameverse.wallets;

   (Do NOT run sql/setup_gameverse_pgadmin.sql — that file was for the legacy frontend stub.)


2. INSTALL PYTHON PACKAGES (one time)
-------------------------------------
Open a terminal in the repository root folder (GameVerse-Database-with-GUI) and run:

   Windows:   python -m pip install -r GameVerse_frontend\gameverse-app\requirements.txt
   Mac/Linux: python3 -m pip install -r GameVerse_frontend/gameverse-app/requirements.txt


3. CONFIGURE DATABASE CONNECTION (one time)
-------------------------------------------
Make a copy of  config/config_template.py  and save it as  config/config.py
Open  config/config.py  and update DB_CONFIG with your local PostgreSQL credentials:

   DB_CONFIG = {
       "dbname": "gameverse",
       "user": "postgres",
       "password": "your_postgres_password",
       "host": "localhost",
       "port": 5432,
   }


4. RUN THE APP
--------------
From the repository root folder (GameVerse-Database-with-GUI):

   Windows (PowerShell):
      $env:PYTHONPATH=".;GameVerse_frontend\gameverse-app"; python GameVerse_frontend\gameverse-app\main.py

   Mac/Linux:
      PYTHONPATH=".:GameVerse_frontend/gameverse-app" python3 GameVerse_frontend/gameverse-app/main.py


5. LOG IN
---------
   Admin:   Admin tab   ->  admin  /  admin
   Player:  Player tab  ->  Use any registered player email & password from gameverse.players
                            (or click "Create account" on the Login screen to register a new player)


6. RUN AUTOMATED TESTS (optional)
---------------------------------
From the repository root folder:

   Windows (PowerShell):
      $env:PYTHONPATH=".;GameVerse_frontend\gameverse-app"; pytest


IF IT DOESN'T WORK
------------------
"Database connection failed"  -> Wrong password, port, or dbname in config/config.py, or PostgreSQL service is stopped
"relation ... does not exist" -> Step 1 (gameverse_schema.sql) was not run on the gameverse database
"No module named 'services'"  -> Make sure you run from the repo root with PYTHONPATH set (Step 4)
"No module named 'psycopg2'"  -> Re-run Step 2 to install requirements.txt
Admin login fails             -> Use username: admin and password: admin


START OVER WITH FRESH DATA
--------------------------
Close the app, drop/recreate the  gameverse  database in pgAdmin (or psql), and re-run Step 1.
