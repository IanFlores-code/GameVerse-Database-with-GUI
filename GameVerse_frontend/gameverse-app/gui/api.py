"""Bridge between the GameVerse GUI and GameVerseService / DatabaseManager."""
from datetime import date
from decimal import Decimal

from db.db_manager import DatabaseManager
from services.gameverse_service import GameVerseService

__all__ = ["AppError"]


class AppError(Exception):
    """User-facing error raised when a backend or database operation fails."""


TRANSACTION_TYPES = ["TopUp", "Cashout", "Purchase", "Transfer"]
PAYMENT_METHODS = ["App", "Kiosk", "Hub Counter", "Bank Transfer"]
WALLET_TYPES = ["Standard", "Vault", "Guild"]


def _unwrap(ok: bool, payload):
    if not ok:
        raise AppError(str(payload) if payload else "Operation failed.")
    return payload


def _not_implemented(name: str):
    raise AppError(f"'{name}' is not implemented in GameVerseService yet.")


# ---------------------------------------------------------------- auth
def test_connection() -> None:
    ok, msg = DatabaseManager.test_connection()
    _unwrap(ok, msg)


def login_admin(username: str, password: str) -> dict:
    # Local dev check until an admin table/service method exists in the backend
    if username.strip() == "admin" and password == "admin":
        return {"role": "admin", "username": "admin", "display_name": "Administrator"}
    raise AppError("Invalid admin credentials.")


def login_player(email: str, password: str) -> dict:
    ok, data = GameVerseService.authenticate_player(email.strip(), password)
    info = _unwrap(ok, data)
    return {
        "role": "player",
        "playerid": info["playerid"],
        "email": email.strip(),
        "display_name": info.get("name") or email.strip(),
    }


def register_player(firstname: str, lastname: str, email: str, phone: str,
                    dateofbirth: date, password: str) -> int:
    query = """
        INSERT INTO gameverse.players (
            playerid, firstname, lastname, email, phone, dateofbirth, registrationdate, isactive
        )
        VALUES (
            (SELECT COALESCE(MAX(playerid), 0) + 1 FROM gameverse.players),
            %s, %s, %s, %s, %s, CURRENT_DATE, TRUE
        )
        RETURNING playerid;
    """
    ok, rows = DatabaseManager.execute_query(
        query,
        (firstname.strip(), lastname.strip(), email.strip(), phone or None, dateofbirth),
        fetch=True,
    )
    result = _unwrap(ok, rows)
    return int(result[0][0])


# ---------------------------------------------------------------- hubs
def list_hubs(active_only: bool = True) -> list[dict]:
    ok, rows = GameVerseService.get_gaming_hubs()
    data = _unwrap(ok, rows)
    hubs = [
        {"hubid": r[0], "hubname": r[1], "location": r[2], "isactive": r[3]}
        for r in data
    ]
    if active_only:
        hubs = [h for h in hubs if h["isactive"]]
    return hubs


def search_hubs(term: str, active_only: bool = True) -> list[dict]:
    needle = term.strip().lower()
    hubs = list_hubs(active_only=active_only)
    if not needle:
        return hubs
    return [
        h for h in hubs
        if needle in str(h["hubname"]).lower() or needle in str(h["location"]).lower()
    ]


def add_hub(hubname: str, location: str) -> int:
    ok, hub_id = GameVerseService.add_hub(hubname, location)
    return int(_unwrap(ok, hub_id))


def update_hub(hubid: int, hubname: str, location: str) -> None:
    ok, res = GameVerseService.update_hub(hubid, hubname, location)
    _unwrap(ok, res)


def set_hub_active(hubid: int, active: bool) -> None:
    ok, res = GameVerseService.set_hub_active(hubid, active)
    _unwrap(ok, res)


def get_hub_details(hubid: int) -> dict:
    ok, row = GameVerseService.get_hub_details(hubid)
    r = _unwrap(ok, row)
    return {
        "hubid": r[0],
        "hubname": r[1],
        "location": r[2],
        "isactive": r[3],
        "wallet_count": r[4],
        "active_wallets": r[5],
        "total_balance": r[6],
        "avg_bonus_rate": r[7],
    }


def hub_summary_report() -> list[dict]:
    ok, rows = GameVerseService.hub_summary_report()
    data = _unwrap(ok, rows)
    return [
        {
            "hubid": r[0],
            "hubname": r[1],
            "location": r[2],
            "isactive": r[3],
            "wallet_count": r[4],
            "active_wallets": r[5],
            "total_balance": r[6],
            "avg_bonus_rate": r[7],
        }
        for r in data
    ]


# ---------------------------------------------------------------- wallets
def list_player_wallets(playerid: int) -> list[dict]:
    query = """
        SELECT w.walletid, w.wallettype, w.hubid, w.balance, w.minimumbalance,
               w.bonusrate, w.walletdescription, w.isactive, wh.holderrole
        FROM gameverse.walletholders wh
        JOIN gameverse.wallets w ON w.walletid = wh.walletid
        WHERE wh.playerid = %s
        ORDER BY w.walletid;
    """
    ok, rows = DatabaseManager.execute_query(query, (playerid,), fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "walletid": r[0],
            "wallettype": r[1],
            "hubid": r[2],
            "balance": r[3],
            "minimumbalance": r[4],
            "bonusrate": r[5],
            "description": r[6],
            "walletdescription": r[6],
            "isactive": r[7],
            "holderrole": r[8],
        }
        for r in data
    ]


def list_all_wallets() -> list[dict]:
    query = """
        SELECT walletid, wallettype, hubid, balance, minimumbalance, bonusrate, walletdescription, isactive
        FROM gameverse.wallets
        ORDER BY walletid;
    """
    ok, rows = DatabaseManager.execute_query(query, fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "walletid": r[0],
            "wallettype": r[1],
            "hubid": r[2],
            "balance": r[3],
            "minimumbalance": r[4],
            "bonusrate": r[5],
            "description": r[6],
            "walletdescription": r[6],
            "isactive": r[7],
        }
        for r in data
    ]


def get_wallet(walletid: int, playerid: int | None = None) -> dict:
    if playerid is not None:
        ok, _ = GameVerseService.verify_wallet_ownership(
            playerid, walletid, required_roles=("Owner", "Co-Owner", "Member")
        )
        _unwrap(ok, "Access denied to wallet.")
    query = """
        SELECT walletid, wallettype, hubid, balance, minimumbalance, bonusrate, walletdescription, isactive
        FROM gameverse.wallets
        WHERE walletid = %s;
    """
    ok, rows = DatabaseManager.execute_query(query, (walletid,), fetch=True)
    data = _unwrap(ok, rows)
    if not data:
        raise AppError("Wallet not found.")
    r = data[0]
    return {
        "walletid": r[0],
        "wallettype": r[1],
        "hubid": r[2],
        "balance": r[3],
        "minimumbalance": r[4],
        "bonusrate": r[5],
        "description": r[6],
        "walletdescription": r[6],
        "isactive": r[7],
    }


def get_wallet_summary(walletid: int, playerid: int | None = None) -> dict:
    if playerid is not None:
        ok, _ = GameVerseService.verify_wallet_ownership(
            playerid, walletid, required_roles=("Owner", "Co-Owner", "Member")
        )
        _unwrap(ok, "Access denied to wallet.")
    ok, row = GameVerseService.get_wallet_summary(walletid)
    data = _unwrap(ok, row)
    return {"walletid": data[0], "balance": data[1], "wallettype": data[2]}


def check_sufficient_balance(walletid: int, amount: Decimal) -> bool:
    ok, result = GameVerseService.check_sufficient_balance(walletid, amount)
    return bool(_unwrap(ok, result))


def low_balance_alerts(threshold: Decimal, playerid: int | None = None) -> list[dict]:
    ok, rows = GameVerseService.get_low_balance_alerts(threshold)
    data = _unwrap(ok, rows)
    alerts = [{"walletid": r[0], "balance": r[1]} for r in data]
    if playerid is not None:
        owned_ids = {w["walletid"] for w in list_player_wallets(playerid)}
        alerts = [a for a in alerts if a["walletid"] in owned_ids]
    return alerts


def open_wallet(playerid: int, wallettype: str, hubid: int, balance: Decimal,
                minimumbalance: Decimal, bonusrate: Decimal, description: str) -> int:
    """Creates Wallets + Owner WalletHolders row atomically. -> new walletid."""
    ok, wallet_id = GameVerseService.open_wallet(
        playerid, wallettype, hubid, balance, minimumbalance, bonusrate, description
    )
    return int(_unwrap(ok, wallet_id))


def update_wallet(walletid: int, bonusrate: Decimal, description: str) -> None:
    ok, res = GameVerseService.update_wallet(walletid, bonusrate, description)
    _unwrap(ok, res)


def set_wallet_active(walletid: int, active: bool) -> None:
    ok, res = GameVerseService.set_wallet_active(walletid, active)
    _unwrap(ok, res)


def wallet_inventory() -> list[dict]:
    """Wallets grouped by type: wallettype, wallet_count, active_count, total_balance, avg_balance."""
    ok, rows = GameVerseService.wallet_inventory()
    data = _unwrap(ok, rows)
    return [
        {
            "wallettype": r[0],
            "wallet_count": r[1],
            "active_count": r[2],
            "total_balance": r[3],
            "avg_balance": r[4],
        }
        for r in data
    ]

# ---------------------------------------------------------------- players
def list_players() -> list[dict]:
    query = """
        SELECT playerid, firstname, lastname, email, phone, isactive
        FROM gameverse.players
        ORDER BY playerid;
    """
    ok, rows = DatabaseManager.execute_query(query, fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "playerid": r[0],
            "firstname": r[1],
            "lastname": r[2],
            "email": r[3],
            "phone": r[4],
            "isactive": r[5],
        }
        for r in data
    ]


def get_player(playerid: int) -> dict:
    ok, row = GameVerseService.get_player_profile(playerid)
    data = _unwrap(ok, row)
    return {
        "playerid": data[0],
        "firstname": data[1],
        "lastname": data[2],
        "email": data[3],
        "phone": data[4],
        "isactive": data[5],
        "dateofbirth": data[6],
        "registrationdate": data[7],
    }


def update_player_contact(playerid: int, email: str, phone: str) -> None:
    query = """
        UPDATE gameverse.players
        SET email = %s, phone = %s
        WHERE playerid = %s;
    """
    ok, res = DatabaseManager.execute_query(
        query,
        (email.strip(), phone.strip() or None, playerid),
        fetch=False,
    )
    _unwrap(ok, res)


def set_player_active(playerid: int, active: bool) -> None:
    ok, res = GameVerseService.set_player_active(playerid, active)
    _unwrap(ok, res)


def player_memberships(playerid: int) -> list[dict]:
    return list_player_wallets(playerid)


def player_transactions(playerid: int) -> list[dict]:
    query = """
        SELECT gt.transactionid, gt.walletid, gt.transactiondate, gt.amount,
               gt.transactiontype, gt.recipient, gt.paymentmethod
        FROM gameverse.gametransactions gt
        JOIN gameverse.walletholders wh ON wh.walletid = gt.walletid
        WHERE wh.playerid = %s
        ORDER BY gt.transactiondate DESC, gt.transactionid DESC;
    """
    ok, rows = DatabaseManager.execute_query(query, (playerid,), fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "transactionid": r[0],
            "walletid": r[1],
            "transactiondate": r[2],
            "amount": r[3],
            "transactiontype": r[4],
            "recipient": r[5],
            "paymentmethod": r[6],
        }
        for r in data
    ]


def player_reviews(playerid: int) -> list[dict]:
    query = """
        SELECT reviewid, playerid, walletid, rating, reviewtext, reviewdate, isverified
        FROM gameverse.walletreviews
        WHERE playerid = %s
        ORDER BY reviewdate DESC, reviewid DESC;
    """
    ok, rows = DatabaseManager.execute_query(query, (playerid,), fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "reviewid": r[0],
            "playerid": r[1],
            "walletid": r[2],
            "rating": r[3],
            "reviewtext": r[4],
            "comment": r[4],
            "reviewdate": r[5],
            "isverified": r[6],
        }
        for r in data
    ]


# ---------------------------------------------------------------- transactions
def perform_transaction(walletid: int, amount: Decimal, transactiontype: str,
                        paymentmethod: str, recipient: str,
                        playerid: int | None = None) -> int:
    if playerid is not None:
        ok, msg = GameVerseService.verify_wallet_ownership(playerid, walletid)
        _unwrap(ok, msg)
    ok, txn_id = GameVerseService.record_transaction(
        walletid, amount, transactiontype, recipient=recipient, payment_method=paymentmethod
    )
    return int(_unwrap(ok, txn_id))


def transfer_funds(from_walletid: int, to_walletid: int, amount: Decimal,
                   paymentmethod: str, playerid: int | None = None) -> int:
    if playerid is not None:
        ok, msg = GameVerseService.verify_wallet_ownership(playerid, from_walletid)
        _unwrap(ok, msg)
    ok, msg = GameVerseService.transfer_funds(from_walletid, to_walletid, amount)
    _unwrap(ok, msg)
    return 0


def wallet_transactions(walletid: int, date_from: date | None = None,
                        date_to: date | None = None, txn_type: str | None = None,
                        playerid: int | None = None) -> list[dict]:
    if playerid is not None:
        ok, _ = GameVerseService.verify_wallet_ownership(
            playerid, walletid, required_roles=("Owner", "Co-Owner", "Member")
        )
        _unwrap(ok, "Access denied to wallet.")
    ok, rows = GameVerseService.get_wallet_transactions(walletid)
    data = _unwrap(ok, rows)
    txns = [
        {
            "transactionid": r[0],
            "transactiondate": r[1],
            "amount": r[2],
            "transactiontype": r[3],
            "recipient": r[4],
            "paymentmethod": r[5],
        }
        for r in data
    ]
    if date_from is not None:
        txns = [t for t in txns if t["transactiondate"] and t["transactiondate"] >= date_from]
    if date_to is not None:
        txns = [t for t in txns if t["transactiondate"] and t["transactiondate"] <= date_to]
    if txn_type:
        txns = [t for t in txns if t["transactiontype"] == txn_type]
    return txns


def reverse_transaction(transactionid: int) -> int:
    ok, rev_id = GameVerseService.reverse_transaction(transactionid)
    return int(_unwrap(ok, rev_id))


def totals_by_payment_method() -> list[dict]:
    ok, rows = GameVerseService.totals_by_payment_method()
    data = _unwrap(ok, rows)
    return [
        {
            "paymentmethod": r[0],
            "tx_count": r[1],
            "net_amount": r[2],
            "total_amount": r[3],
        }
        for r in data
    ]


# ---------------------------------------------------------------- reviews
def add_review(playerid: int, walletid: int, rating: int, reviewtext: str) -> int:
    ok, review_id = GameVerseService.submit_wallet_review(
        playerid, walletid, rating, comment=reviewtext
    )
    return int(_unwrap(ok, review_id))


def list_reviews(walletid: int | None = None) -> list[dict]:
    query = """
        SELECT reviewid, playerid, walletid, rating, reviewtext, reviewdate, isverified
        FROM gameverse.walletreviews
        {where_clause}
        ORDER BY reviewdate DESC, reviewid DESC;
    """
    where_clause = "WHERE walletid = %s" if walletid is not None else ""
    params = (walletid,) if walletid is not None else ()
    ok, rows = DatabaseManager.execute_query(query.format(where_clause=where_clause), params, fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "reviewid": r[0],
            "playerid": r[1],
            "walletid": r[2],
            "rating": r[3],
            "reviewtext": r[4],
            "comment": r[4],
            "reviewdate": r[5],
            "isverified": r[6],
        }
        for r in data
    ]


def set_review_verified(reviewid: int, verified: bool) -> None:
    ok, res = GameVerseService.set_review_verified(reviewid, verified)
    _unwrap(ok, res)


def avg_rating_by_wallet_type() -> list[dict]:
    ok, rows = GameVerseService.get_average_rating_per_wallet_type()
    data = _unwrap(ok, rows)
    return [{"wallettype": r[0], "avg_rating": r[1]} for r in data]


# ---------------------------------------------------------------- analytics (bonus)
def monthly_flows(walletid: int | None = None, playerid: int | None = None) -> list[dict]:
    """-> rows: month ('YYYY-MM'), topups, cashouts, purchases."""
    conditions = []
    params: list = []
    joins = ""

    if playerid is not None:
        joins = "JOIN gameverse.walletholders wh ON wh.walletid = gt.walletid"
        conditions.append("wh.playerid = %s")
        params.append(playerid)

    if walletid is not None:
        conditions.append("gt.walletid = %s")
        params.append(walletid)

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            TO_CHAR(gt.transactiondate, 'YYYY-MM') AS month,
            COALESCE(SUM(CASE WHEN gt.transactiontype IN ('TopUp', 'Deposit') THEN ABS(gt.amount) ELSE 0 END), 0) AS topups,
            COALESCE(SUM(CASE WHEN gt.transactiontype = 'Cashout' THEN ABS(gt.amount) ELSE 0 END), 0) AS cashouts,
            COALESCE(SUM(CASE WHEN gt.transactiontype = 'Purchase' THEN ABS(gt.amount) ELSE 0 END), 0) AS purchases
        FROM gameverse.gametransactions gt
        {joins}
        {where_sql}
        GROUP BY TO_CHAR(gt.transactiondate, 'YYYY-MM')
        ORDER BY month;
    """
    ok, rows = DatabaseManager.execute_query(query, tuple(params), fetch=True)
    data = _unwrap(ok, rows)
    return [
        {
            "month": r[0],
            "topups": r[1],
            "cashouts": r[2],
            "purchases": r[3],
        }
        for r in data
    ]