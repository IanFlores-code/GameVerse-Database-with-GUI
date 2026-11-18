# GameVerse Wallet Manager: Frontend (Tkinter GUI)

This is the **frontend branch** of our Assignment 4 project: a Python 3.10+ /
Tkinter GUI with role-based login (Admin / Player). It covers every module in
the assignment guide, plus Optional Task 4 (analytics chart, bonus projection
and balance notifications).

The frontend runs on its own today through a small **stand-in backend**
(`dev_backend/` + `sql/dev_backend_stub.sql`). When we merge with the backend
branch, the GUI switches to the real service layer by editing **one file**:
`gui/api.py`.

---

## 1. Running it

```bash
pip install -r requirements.txt          # psycopg2-binary, pytest
cp .env.example .env                     # then put your DB password in .env
```

1. Load the GameVerse schema + data from Assignment 3 (the `gameverse_schema.sql` dump).
2. Run `sql/dev_backend_stub.sql` top-to-bottom in pgAdmin4 (only needed until the merge).
3. Start the app:

```bash
python main.py
```

The app tests the connection first. If the database can't be reached, it
shows a readable message with a **Retry** option instead of a stack trace.

> Tkinter ships with the Windows/macOS Python installers. On Linux, install
> `python3-tk` if `import tkinter` fails.

### Test logins (created by the stub SQL)

| Role   | Login                         | Password    |
|--------|-------------------------------|-------------|
| Admin  | `admin`                       | `Admin@123` |
| Player | `alex.chen@gameverse.com`     | `player123` |
| Player | `bianca.ruiz@gameverse.com` (Co-Owner of 2002, 2007) | `player123` |
| Player | `carlos.nguyen@gameverse.com` (**Member** of 2012, can view but not transact) | `player123` |

All 15 seeded players use `player123`.

---

## 2. Project layout

```
main.py                     entry point
gui/
  api.py                    <-- the ONLY bridge between GUI and backend
  app.py                    window: connection test, login <-> shell switching
  theme.py                  colors, fonts, ttk styles
  widgets.py                DataTable, FormDialog, DetailsDialog, TableDialog, Segmented...
  validators.py             input-format parsing (money, dates, email...)
  session.py                who is logged in (role, playerid)
  views/
    login_view.py           Module 1: login + player registration
    shell.py                sidebar navigation; menu items depend on role
    overview_view.py        landing page with headline numbers
    hubs_view.py            Module 2
    wallets_view.py         Module 3
    players_view.py         Module 4 (admin)
    profile_view.py         Module 4 (player)
    transactions_view.py    Module 5
    reviews_view.py         Module 6
    analytics_view.py       Optional Task 4 (options 1 + 2)
dev_backend/                STAND-IN backend (delete after merge)
sql/dev_backend_stub.sql    STAND-IN SQL (replaced by the backend's script)
tests/test_gui_validators.py
docs/screenshots/           screenshots for the PDF user guide
```

Layers stay separate: **views → `gui/api.py` → backend services → DB**. No
view builds SQL; every query in the backend layer is parameterized (`%s`).

---

## 3. Feature checklist vs. the assignment guide

| Module | Where in the GUI |
|---|---|
| **1 Auth**: admin login, player login, roles, inactive players blocked, registration | Login screen; sidebar changes by role |
| **2 Hubs**: list active, details (wallet count + total balance), search, add, edit, deactivate/reactivate (blocked if active wallets), summary report | *Hubs* |
| **3 Wallets**: my wallets with role, details, low-balance alert, open wallet (Wallets + Owner row in 1 txn), edit bonus/description, (de)activate, inventory by type | *Wallets* |
| **4 Players**: register, update phone/email, profile; admin list, memberships, transaction history, review history | *My profile* / *Players* |
| **5 Transactions**: TopUp/Cashout/Purchase/Transfer, Member can't transact, destination wallet, balance check, history by date range/type, totals by payment method, admin reverse | *Transactions* |
| **6 Reviews**: write (1-5), duplicate rejected, my reviews; admin verify/unverify, per-wallet filter, average by type | *Reviews* |
| **Task 3 functions**: `performTransaction`, `transferFunds`, `getWalletSummary`, `checkSufficientBalance`, `getLowBalanceAlerts` | All called through `gui/api.py` |
| **Task 4 bonus**: option 2 monthly chart, option 1 bonus projection, option 5 notifications | *Analytics*; pop-ups after transactions |

Error handling: every backend error reaches the user as a short message
(dialog or inline in forms). Assignment 3 constraint violations are mapped to
plain-English messages in `dev_backend/errors.py`. The DB's own messages pass
straight through, e.g.
`Insufficient funds. Spendable balance: 2,400.00 (balance 2,500.00, minimum 100.00)`.

---

## 4. Merging with the backend branch

`gui/api.py` lists every function the GUI needs, with its arguments and
return shape in the docstring. To merge:

1. In `gui/api.py`, replace
   ```python
   from dev_backend import services as _svc
   from dev_backend.errors import AppError
   ```
   with the backend's modules/exception (alias the backend's user-facing
   exception as `AppError`).
2. For each function whose name or argument order differs in the backend,
   change its one-line body. **No file in `gui/views/` needs to change.**
3. Delete `dev_backend/` and `sql/dev_backend_stub.sql`; use the backend's SQL script.
4. Run `python main.py`, log in as admin and as a player, and click through each page.

### What the GUI expects the backend to provide

These are things the stub adds. If the backend already has its own version,
just map to it in `api.py`:

- **Login data:** a password for players and an admin account (stub: `players.passwordhash` + `admins` table, bcrypt via pgcrypto).
- **ID generation** for new hubs, wallets, players, transactions and reviews (the A2 tables have no defaults).
- **Return shapes:** functions return dicts / lists of dicts keyed by column
  name (e.g. `walletid`, `balance`, `holderrole`). `get_wallet_summary`'s keys are
  displayed generically, so any column names work there.
- **Access checks** take an optional `playerid` (`None` = admin): holder-only
  views, and Owner/Co-Owner only for transactions.
- **Reversal:** `reverse_transaction(txnid)` must restore the balance (stub
  inserts an offsetting `Reversal` row linked via `linkedtxnid`; transfers
  reverse both legs).

---

## 5. Tests

```bash
python -m pytest tests
```

`tests/test_gui_validators.py` covers the GUI's input parsing. The
business-rule tests (balance validation, trigger, transfers, member can't
transact, duplicate review/email) are the backend branch's job because they
run against the service layer.
