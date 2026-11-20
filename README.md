GAMEVERSE WALLET MANAGER - HOW TO RUN
=====================================

NEED INSTALLED
--------------
- PostgreSQL + pgAdmin 4
- Python 3.10 or newer (Windows: tick "Add Python to PATH" when installing)


1. SET UP THE DATABASE (pgAdmin)
--------------------------------
a) Right-click Databases > Create > Database. Name it: GameVerse
b) Click GameVerse > Tools > Query Tool
c) Open the file  sql/setup_gameverse_pgadmin.sql  and press F5
d) Check it worked:   SELECT COUNT(*) FROM gameverse.wallets;
   It should return 15.

   (Do NOT run gameverse_schema.sql in pgAdmin. It will error.)


2. INSTALL PYTHON PACKAGES (one time)
-------------------------------------
Open a terminal in the project folder (the one with main.py) and run:

   Windows:  py -m pip install -r requirements.txt
   Mac:      python3 -m pip install -r requirements.txt


3. ADD YOUR DATABASE PASSWORD (one time)
----------------------------------------
Make a copy of  .env.example  and name it  .env
Open .env and set:

   GV_DB_NAME=GameVerse
   GV_DB_PASSWORD=your_postgres_password


4. RUN THE APP
--------------
   Windows:  py main.py
   Mac:      python3 main.py


5. LOG IN
---------
   Admin:   Admin tab   ->  admin  /  Admin@123
   Player:  Player tab  ->  alex.chen@gameverse.com  /  player123

   (Every player's password is player123)


IF IT DOESN'T WORK
------------------
"Cannot reach the database"   -> wrong password or database name in .env,
                                 or the file is named .env.txt by mistake
"schema is missing tables"    -> GV_DB_NAME is wrong, or step 1 was skipped
Login always fails            -> step 1 wasn't run on that database
"No module named psycopg2"    -> redo step 2
"py is not recognized"        -> try "python" instead of "py"


START OVER WITH FRESH DATA
--------------------------
Close the app, delete the GameVerse database in pgAdmin, then redo step 1.
