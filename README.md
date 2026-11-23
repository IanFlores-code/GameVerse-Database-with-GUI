GAMEVERSE WALLET MANAGER - HOW TO RUN
=====================================

IMPORTANT
--------------
The documentation and screenshots are in GameVerse_frontend\gameverse-app\docs\

NEED INSTALLED
--------------
- PostgreSQL + pgAdmin 4
- Python 3.10 or newer (Windows: tick "Add Python to PATH" when installing)


1. SET UP THE DATABASE (pgAdmin) - one time
-------------------------------------------
a) Right-click Databases > Create > Database. Name it: GameVerse
b) Click GameVerse > Tools > Query Tool
c) Open the file  gameverse_setup.sql  (repository root) and press F5
d) Check it worked:   SELECT COUNT(*) FROM gameverse.wallets;
   It should return 15.

   gameverse_setup.sql = the Assignment 2/3 schema and data + the stored
   functions, triggers and login accounts. It is the only SQL file to run.
   (gameverse_schema.sql is the raw pg_dump; pgAdmin cannot run it and
   reports  syntax error at or near "8001".)

   Already set up a GameVerse database earlier with
   sql/setup_gameverse_pgadmin.sql? It is the same, so you can keep it.


2. INSTALL PYTHON PACKAGES - one time
-------------------------------------
Open a terminal in the repository root (the folder with config, db, services) and run:

   Windows:  py -m pip install -r requirements.txt
   Mac:      python3 -m pip install -r requirements.txt


3. ADD YOUR DATABASE PASSWORD - one time
----------------------------------------
Copy  config\config_template.py  to  config\config.py

   Windows:  copy config\config_template.py config\config.py
   Mac:      cp config/config_template.py config/config.py

Open config\config.py and replace YOUR_PASSWORD_HERE with your PostgreSQL
password (keep the quotes). The database name is already GameVerse.
config.py is in .gitignore, so your password is never committed.


4. RUN THE APP
--------------
From the repository root, set PYTHONPATH and start main.py:

   PowerShell:      $env:PYTHONPATH=".;GameVerse_frontend\gameverse-app"; python GameVerse_frontend\gameverse-app\main.py
   Command Prompt:  set PYTHONPATH=.;GameVerse_frontend\gameverse-app
                    python GameVerse_frontend\gameverse-app\main.py
   Mac/Linux:       PYTHONPATH=".:GameVerse_frontend/gameverse-app" python3 GameVerse_frontend/gameverse-app/main.py

(main.py also adds these folders itself, so the app still starts if PYTHONPATH is not set.)


5. LOG IN
---------
   Admin:   Admin tab   ->  admin  /  Admin@123
   Player:  Player tab  ->  alex.chen@gameverse.com  /  player123

   Every seeded player's password is player123. New players can sign up with
   "Create an account". Passwords are stored as bcrypt hashes.

   Good accounts for testing:
     alex.chen@gameverse.com      Owner of wallets 2001 and 2002
     bianca.ruiz@gameverse.com    Co-Owner of 2002 and 2007
     carlos.nguyen@gameverse.com  Member of 2012 (can view, cannot transact)


6. RUN THE TESTS
----------------
From the repository root:

   PowerShell:  $env:PYTHONPATH=".;GameVerse_frontend\gameverse-app"; pytest -v tests\test_gameverse.py
   Mac/Linux:   PYTHONPATH=".:GameVerse_frontend/gameverse-app" pytest -v tests/test_gameverse.py

That runs the 17 business-rule tests (they need the database). Plain "pytest" from the
root runs those plus the 23 GUI input tests. The tests clean up after themselves,
so they can be run again and again.


PROJECT LAYOUT
--------------
   gameverse_setup.sql          database: schema, data, functions, triggers
   config/                      connection settings (config.py is yours, not committed)
   db/db_manager.py             one reused connection, readable error messages
   services/gameverse_service.py  backend: calls the stored functions, access checks
   GameVerse_frontend/gameverse-app/
       main.py                  start the app here
       gui/api.py               bridge between the screens and the service layer
       gui/views/               one file per screen
   tests/                       business-rule tests (pytest)


IF IT DOESN'T WORK
------------------
"Database connection failed"   -> wrong password or database name in config/config.py,
                                  or PostgreSQL is not running
"schema is missing tables"     -> step 1 was not run on the database named in config.py
"function crypt(...) does not exist" or login always fails
                               -> step 1 was not run on that database
"No module named psycopg2"     -> redo step 2
"py is not recognized"         -> try "python" instead of "py"


START OVER WITH FRESH DATA
--------------------------
Close the app, delete the GameVerse database in pgAdmin, then redo step 1.
