"""Stand-in service layer for the frontend branch.

Every query is parameterized (%s placeholders). Business rules that the
assignment says must live in the database (balance checks, signs, balance
updates) are delegated to the stored functions/triggers in
sql/dev_backend_stub.sql; this module only does access checks and plain CRUD.

When the frontend and backend branches are merged, gui/api.py is pointed at
the backend's real services and this package can be deleted.
"""
from decimal import Decimal

from .db import Database
from .errors import AppError

db = Database()

TRANSACTABLE_ROLES = ("Owner", "Co-Owner")


# ======================================================================
# Connection / auth
# ======================================================================
def test_connection() -> None:
    db.test_connection()


def login_admin(username: str, password: str) -> dict:
    row = db.query_one(
        "SELECT adminid, username FROM admins "
        "WHERE username = %s AND passwordhash = crypt(%s, passwordhash)",
        (username, password),
    )
    if not row:
        raise AppError("Invalid admin username or password.")
    return {"role": "admin", "adminid": row["adminid"], "username": row["username"],
            "display_name": row["username"]}


def login_player(email: str, password: str) -> dict:
    row = db.query_one(
        "SELECT playerid, firstname, lastname, email, isactive FROM players "
        "WHERE lower(email) = lower(%s) AND passwordhash = crypt(%s, passwordhash)",
        (email, password),
    )
    if not row:
        raise AppError("Invalid email or password.")
    if not row["isactive"]:
        raise AppError("This account has been deactivated. Contact an administrator.")
    return {"role": "player", "playerid": row["playerid"], "email": row["email"],
            "display_name": f"{row['firstname']} {row['lastname']}"}


def register_player(firstname, lastname, email, phone, dateofbirth, password) -> int:
    row = db.query_one(
        "INSERT INTO players (firstname, lastname, email, phone, dateofbirth, "
        "registrationdate, isactive, passwordhash) "
        "VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, TRUE, crypt(%s, gen_salt('bf'))) "
        "RETURNING playerid",
        (firstname, lastname, email, phone or None, dateofbirth, password),
    )
    return row["playerid"]


# ======================================================================
# Hubs
# ======================================================================
def list_hubs(active_only: bool = True) -> list[dict]:
    return db.query(
        "SELECT hubid, hubname, location, isactive FROM gaminghubs "
        "WHERE (%s = FALSE OR isactive) ORDER BY hubid",
        (active_only,),
    )


def search_hubs(term: str, active_only: bool = True) -> list[dict]:
    like = f"%{term}%"
    return db.query(
        "SELECT hubid, hubname, location, isactive FROM gaminghubs "
        "WHERE (hubname ILIKE %s OR location ILIKE %s) AND (%s = FALSE OR isactive) "
        "ORDER BY hubid",
        (like, like, active_only),
    )


def get_hub_details(hubid: int) -> dict:
    row = db.query_one(
        "SELECT h.hubid, h.hubname, h.location, h.isactive, "
        "       COUNT(w.walletid) AS total_wallets, "
        "       COUNT(w.walletid) FILTER (WHERE w.isactive) AS active_wallets, "
        "       COALESCE(SUM(w.balance), 0) AS total_balance "
        "FROM gaminghubs h LEFT JOIN wallets w ON w.hubid = h.hubid "
        "WHERE h.hubid = %s GROUP BY h.hubid",
        (hubid,),
    )
    if not row:
        raise AppError(f"Hub {hubid} does not exist.")
    return row


def add_hub(hubname: str, location: str) -> int:
    return db.query_one(
        "INSERT INTO gaminghubs (hubname, location, isactive) VALUES (%s, %s, TRUE) "
        "RETURNING hubid", (hubname, location),
    )["hubid"]


def update_hub(hubid: int, hubname: str, location: str) -> None:
    if db.execute("UPDATE gaminghubs SET hubname = %s, location = %s WHERE hubid = %s",
                  (hubname, location, hubid)) == 0:
        raise AppError(f"Hub {hubid} does not exist.")


def set_hub_active(hubid: int, active: bool) -> None:
    if not active:
        n = db.query_one("SELECT COUNT(*) AS n FROM wallets WHERE hubid = %s AND isactive",
                         (hubid,))["n"]
        if n:
            raise AppError(f"Hub {hubid} still has {n} active wallet(s). "
                           "Deactivate or move them before deactivating the hub.")
    if db.execute("UPDATE gaminghubs SET isactive = %s WHERE hubid = %s", (active, hubid)) == 0:
        raise AppError(f"Hub {hubid} does not exist.")


def hub_summary_report() -> list[dict]:
    return db.query(
        "SELECT h.hubid, h.hubname, h.isactive, COUNT(w.walletid) AS wallet_count, "
        "       COALESCE(SUM(w.balance), 0) AS total_balance, "
        "       ROUND(AVG(w.bonusrate), 2) AS avg_bonus_rate "
        "FROM gaminghubs h LEFT JOIN wallets w ON w.hubid = h.hubid "
        "GROUP BY h.hubid ORDER BY h.hubid"
    )


# ======================================================================
# Wallets
# ======================================================================
_WALLET_COLS = ("w.walletid, w.wallettype, w.hubid, h.hubname, w.balance, w.bonusrate, "
                "w.walletdescription, w.opendate, w.minimumbalance, w.isactive")


def _holder_role(playerid: int, walletid: int) -> str | None:
    row = db.query_one("SELECT holderrole FROM walletholders WHERE playerid = %s AND walletid = %s",
                       (playerid, walletid))
    return row["holderrole"] if row else None


def _require_holder(playerid: int | None, walletid: int) -> None:
    if playerid is not None and _holder_role(playerid, walletid) is None:
        raise AppError(f"You do not hold wallet {walletid}.")


def list_player_wallets(playerid: int) -> list[dict]:
    return db.query(
        f"SELECT {_WALLET_COLS}, wh.holderrole FROM walletholders wh "
        "JOIN wallets w ON w.walletid = wh.walletid JOIN gaminghubs h ON h.hubid = w.hubid "
        "WHERE wh.playerid = %s ORDER BY w.walletid",
        (playerid,),
    )


def list_all_wallets() -> list[dict]:
    return db.query(
        f"SELECT {_WALLET_COLS}, "
        "  (SELECT p.firstname || ' ' || p.lastname FROM walletholders wh "
        "   JOIN players p ON p.playerid = wh.playerid "
        "   WHERE wh.walletid = w.walletid AND wh.holderrole = 'Owner') AS owner "
        "FROM wallets w JOIN gaminghubs h ON h.hubid = w.hubid ORDER BY w.walletid"
    )


def get_wallet(walletid: int, playerid: int | None = None) -> dict:
    _require_holder(playerid, walletid)
    row = db.query_one(
        f"SELECT {_WALLET_COLS} FROM wallets w JOIN gaminghubs h ON h.hubid = w.hubid "
        "WHERE w.walletid = %s", (walletid,))
    if not row:
        raise AppError(f"Wallet {walletid} does not exist.")
    return row


def get_wallet_summary(walletid: int, playerid: int | None = None) -> dict:
    _require_holder(playerid, walletid)
    return db.query_one("SELECT * FROM getWalletSummary(%s)", (walletid,))


def check_sufficient_balance(walletid: int, amount: Decimal) -> bool:
    return db.query_one("SELECT checkSufficientBalance(%s, %s) AS ok", (walletid, amount))["ok"]


def low_balance_alerts(threshold: Decimal, playerid: int | None = None) -> list[dict]:
    if playerid is None:
        return db.query("SELECT * FROM getLowBalanceAlerts(%s)", (threshold,))
    return db.query(
        "SELECT a.* FROM getLowBalanceAlerts(%s) a "
        "JOIN walletholders wh ON wh.walletid = a.walletid WHERE wh.playerid = %s",
        (threshold, playerid))


def open_wallet(playerid, wallettype, hubid, balance, minimumbalance, bonusrate, description) -> int:
    """Creates the Wallets row and the Owner WalletHolders row in ONE transaction."""
    if wallettype not in ("Standard", "Vault", "Guild"):
        raise AppError("Wallet type must be Standard, Vault or Guild.")
    if balance < minimumbalance:
        raise AppError("Initial balance must be at least the minimum balance.")
    with db.transaction() as cur:
        cur.execute("SELECT isactive FROM players WHERE playerid = %s", (playerid,))
        p = cur.fetchone()
        if not p:
            raise AppError(f"Player {playerid} does not exist.")
        if not p["isactive"]:
            raise AppError(f"Player {playerid} is deactivated.")
        cur.execute("SELECT isactive FROM gaminghubs WHERE hubid = %s", (hubid,))
        h = cur.fetchone()
        if not h or not h["isactive"]:
            raise AppError("Choose an active hub.")
        cur.execute(
            "INSERT INTO wallets (wallettype, hubid, balance, bonusrate, walletdescription, "
            "opendate, minimumbalance, isactive) VALUES (%s,%s,%s,%s,%s,CURRENT_DATE,%s,TRUE) "
            "RETURNING walletid",
            (wallettype, hubid, balance, bonusrate, description, minimumbalance))
        walletid = cur.fetchone()["walletid"]
        cur.execute(
            "INSERT INTO walletholders (walletid, playerid, holderrole, joindate, depositamount) "
            "VALUES (%s, %s, 'Owner', CURRENT_DATE, %s)", (walletid, playerid, balance))
    return walletid


def update_wallet(walletid: int, bonusrate: Decimal, description: str) -> None:
    if db.execute("UPDATE wallets SET bonusrate = %s, walletdescription = %s WHERE walletid = %s",
                  (bonusrate, description, walletid)) == 0:
        raise AppError(f"Wallet {walletid} does not exist.")


def set_wallet_active(walletid: int, active: bool) -> None:
    if db.execute("UPDATE wallets SET isactive = %s WHERE walletid = %s", (active, walletid)) == 0:
        raise AppError(f"Wallet {walletid} does not exist.")


def wallet_inventory() -> list[dict]:
    return db.query(
        "SELECT wallettype, COUNT(*) AS wallet_count, "
        "       COUNT(*) FILTER (WHERE isactive) AS active_count, "
        "       SUM(balance) AS total_balance, ROUND(AVG(balance), 2) AS avg_balance "
        "FROM wallets GROUP BY wallettype ORDER BY wallettype")


# ======================================================================
# Players
# ======================================================================
_PLAYER_COLS = ("playerid, firstname, lastname, email, phone, dateofbirth, "
                "registrationdate, isactive")


def list_players() -> list[dict]:
    return db.query(f"SELECT {_PLAYER_COLS} FROM players ORDER BY playerid")


def get_player(playerid: int) -> dict:
    row = db.query_one(f"SELECT {_PLAYER_COLS} FROM players WHERE playerid = %s", (playerid,))
    if not row:
        raise AppError(f"Player {playerid} does not exist.")
    return row


def update_player_contact(playerid: int, email: str, phone: str) -> None:
    db.execute("UPDATE players SET email = %s, phone = %s WHERE playerid = %s",
               (email, phone or None, playerid))


def set_player_active(playerid: int, active: bool) -> None:
    if db.execute("UPDATE players SET isactive = %s WHERE playerid = %s", (active, playerid)) == 0:
        raise AppError(f"Player {playerid} does not exist.")


def player_memberships(playerid: int) -> list[dict]:
    return list_player_wallets(playerid)


def player_transactions(playerid: int) -> list[dict]:
    return db.query(
        "SELECT t.transactionid, t.walletid, t.transactiondate, t.amount, t.transactiontype, "
        "       t.recipient, t.paymentmethod, t.linkedtxnid "
        "FROM gametransactions t JOIN walletholders wh ON wh.walletid = t.walletid "
        "WHERE wh.playerid = %s ORDER BY t.transactiondate DESC, t.transactionid DESC",
        (playerid,))


def player_reviews(playerid: int) -> list[dict]:
    return db.query(
        "SELECT r.reviewid, r.walletid, w.wallettype, r.rating, r.reviewtext, r.reviewdate, "
        "       r.isverified FROM walletreviews r JOIN wallets w ON w.walletid = r.walletid "
        "WHERE r.playerid = %s ORDER BY r.reviewdate DESC", (playerid,))


# ======================================================================
# Transactions
# ======================================================================
def _require_transact_role(playerid: int | None, walletid: int) -> None:
    if playerid is None:          # admins may transact on any wallet
        return
    role = _holder_role(playerid, walletid)
    if role is None:
        raise AppError(f"You do not hold wallet {walletid}.")
    if role not in TRANSACTABLE_ROLES:
        raise AppError(f"Your role on wallet {walletid} is '{role}'. "
                       "Only an Owner or Co-Owner can make transactions.")


def perform_transaction(walletid, amount, transactiontype, paymentmethod, recipient,
                        playerid: int | None = None) -> int:
    _require_transact_role(playerid, walletid)
    return db.query_one("SELECT performTransaction(%s, %s, %s, %s, %s) AS id",
                        (walletid, amount, transactiontype, paymentmethod, recipient))["id"]


def transfer_funds(from_walletid, to_walletid, amount, paymentmethod,
                   playerid: int | None = None) -> int:
    _require_transact_role(playerid, from_walletid)
    return db.query_one("SELECT transferFunds(%s, %s, %s, %s) AS id",
                        (from_walletid, to_walletid, amount, paymentmethod))["id"]


def wallet_transactions(walletid: int, date_from=None, date_to=None, txn_type=None,
                        playerid: int | None = None) -> list[dict]:
    _require_holder(playerid, walletid)
    return db.query(
        "SELECT transactionid, walletid, transactiondate, amount, transactiontype, recipient, "
        "       paymentmethod, linkedtxnid FROM gametransactions "
        "WHERE walletid = %s "
        "  AND (%s::date IS NULL OR transactiondate >= %s::date) "
        "  AND (%s::date IS NULL OR transactiondate <= %s::date) "
        "  AND (%s::text IS NULL OR transactiontype = %s::text) "
        "ORDER BY transactiondate DESC, transactionid DESC",
        (walletid, date_from, date_from, date_to, date_to, txn_type, txn_type))


def totals_by_payment_method(walletid: int | None = None, playerid: int | None = None) -> list[dict]:
    if walletid is not None:
        _require_holder(playerid, walletid)
    return db.query(
        "SELECT t.paymentmethod, COUNT(*) AS txn_count, "
        "       SUM(t.amount) FILTER (WHERE t.amount > 0) AS total_in, "
        "       -SUM(t.amount) FILTER (WHERE t.amount < 0) AS total_out, "
        "       SUM(ABS(t.amount)) AS total_volume "
        "FROM gametransactions t "
        "WHERE (%s::int IS NULL OR t.walletid = %s::int) "
        "  AND (%s::int IS NULL OR t.walletid IN "
        "       (SELECT walletid FROM walletholders WHERE playerid = %s::int)) "
        "GROUP BY t.paymentmethod ORDER BY total_volume DESC",
        (walletid, walletid, playerid, playerid))


def reverse_transaction(transactionid: int) -> list[int]:
    """Admin only: insert offsetting 'Reversal' rows (both legs for a transfer)."""
    with db.transaction() as cur:
        cur.execute("SELECT * FROM gametransactions WHERE transactionid = %s", (transactionid,))
        txn = cur.fetchone()
        if not txn:
            raise AppError(f"Transaction {transactionid} does not exist.")
        if txn["transactiontype"] == "Reversal":
            raise AppError("A reversal cannot itself be reversed.")
        ids = [transactionid]
        if txn["transactiontype"] == "Transfer" and txn["linkedtxnid"]:
            ids.append(txn["linkedtxnid"])
        cur.execute("SELECT 1 FROM gametransactions WHERE transactiontype = 'Reversal' "
                    "AND linkedtxnid = ANY(%s)", (ids,))
        if cur.fetchone():
            raise AppError(f"Transaction {transactionid} has already been reversed.")
        new_ids = []
        for tid in ids:
            cur.execute(
                "INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, "
                "recipient, paymentmethod, linkedtxnid) "
                "SELECT walletid, CURRENT_DATE, -amount, 'Reversal', 'Reversal of #' || transactionid, "
                "paymentmethod, transactionid FROM gametransactions WHERE transactionid = %s "
                "RETURNING transactionid", (tid,))
            new_ids.append(cur.fetchone()["transactionid"])
    return new_ids


# ======================================================================
# Reviews
# ======================================================================
def add_review(playerid: int, walletid: int, rating: int, reviewtext: str) -> int:
    _require_holder(playerid, walletid)
    return db.query_one(
        "INSERT INTO walletreviews (playerid, walletid, rating, reviewtext, reviewdate, isverified) "
        "VALUES (%s, %s, %s, %s, CURRENT_DATE, FALSE) RETURNING reviewid",
        (playerid, walletid, rating, reviewtext))["reviewid"]


def list_reviews(walletid: int | None = None) -> list[dict]:
    return db.query(
        "SELECT r.reviewid, r.walletid, w.wallettype, r.playerid, "
        "       p.firstname || ' ' || p.lastname AS player, r.rating, r.reviewtext, "
        "       r.reviewdate, r.isverified "
        "FROM walletreviews r JOIN wallets w ON w.walletid = r.walletid "
        "JOIN players p ON p.playerid = r.playerid "
        "WHERE (%s::int IS NULL OR r.walletid = %s::int) ORDER BY r.reviewdate DESC",
        (walletid, walletid))


def set_review_verified(reviewid: int, verified: bool) -> None:
    if db.execute("UPDATE walletreviews SET isverified = %s WHERE reviewid = %s",
                  (verified, reviewid)) == 0:
        raise AppError(f"Review {reviewid} does not exist.")


def avg_rating_by_wallet_type() -> list[dict]:
    return db.query(
        "SELECT w.wallettype, COUNT(r.reviewid) AS review_count, "
        "       ROUND(AVG(r.rating), 2) AS avg_rating "
        "FROM wallets w LEFT JOIN walletreviews r ON r.walletid = w.walletid "
        "GROUP BY w.wallettype ORDER BY w.wallettype")


# ======================================================================
# Analytics (Optional Task 4)
# ======================================================================
def monthly_flows(walletid: int | None = None, playerid: int | None = None) -> list[dict]:
    """Monthly top-ups vs cash-outs+purchases (option 2)."""
    if walletid is not None:
        _require_holder(playerid, walletid)
    return db.query(
        "SELECT to_char(date_trunc('month', transactiondate), 'YYYY-MM') AS month, "
        "       COALESCE(SUM(amount) FILTER (WHERE transactiontype = 'TopUp'), 0) AS topups, "
        "       COALESCE(-SUM(amount) FILTER (WHERE transactiontype = 'Cashout'), 0) AS cashouts, "
        "       COALESCE(-SUM(amount) FILTER (WHERE transactiontype = 'Purchase'), 0) AS purchases "
        "FROM gametransactions "
        "WHERE (%s::int IS NULL OR walletid = %s::int) "
        "  AND (%s::int IS NULL OR walletid IN "
        "       (SELECT walletid FROM walletholders WHERE playerid = %s::int)) "
        "GROUP BY 1 ORDER BY 1",
        (walletid, walletid, playerid, playerid))
