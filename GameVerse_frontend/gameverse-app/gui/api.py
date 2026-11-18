"""THE ONLY BRIDGE BETWEEN THE GUI AND THE BACKEND.

Every screen calls functions in this module and nothing else from the
backend. Each function:
  * returns plain Python values (dicts / lists of dicts / ints / bools), and
  * raises AppError(message) for anything the user should be told about.

MERGING WITH THE BACKEND BRANCH
-------------------------------
Right now these functions delegate to `dev_backend.services`, a stand-in
so the GUI can run on its own. To merge:
  1. Change the two imports below to point at the backend's modules
     (e.g. `from services import hub_service, wallet_service, ...`).
  2. Edit the one-line body of any function whose backend name or
     argument order differs.
  3. Make sure the backend raises (or is wrapped to raise) an exception
     whose str() is a user-friendly message, and alias it as AppError.
No view file needs to change.
"""
from decimal import Decimal
from datetime import date

from dev_backend import services as _svc          # <-- swap at merge time
from dev_backend.errors import AppError            # <-- swap at merge time

__all__ = ["AppError"]

TRANSACTION_TYPES = ["TopUp", "Cashout", "Purchase", "Transfer"]
PAYMENT_METHODS = ["App", "Kiosk", "Hub Counter", "Bank Transfer"]
WALLET_TYPES = ["Standard", "Vault", "Guild"]


# ---------------------------------------------------------------- auth
def test_connection() -> None:
    """Raise AppError if the database (and schema) cannot be reached."""
    _svc.test_connection()


def login_admin(username: str, password: str) -> dict:
    """-> {'role': 'admin', 'username', 'display_name'}"""
    return _svc.login_admin(username, password)


def login_player(email: str, password: str) -> dict:
    """-> {'role': 'player', 'playerid', 'email', 'display_name'}; inactive players rejected."""
    return _svc.login_player(email, password)


def register_player(firstname: str, lastname: str, email: str, phone: str,
                    dateofbirth: date, password: str) -> int:
    """-> new playerid. Age >= 13 and unique email enforced by DB constraints."""
    return _svc.register_player(firstname, lastname, email, phone, dateofbirth, password)


# ---------------------------------------------------------------- hubs
def list_hubs(active_only: bool = True) -> list[dict]:
    return _svc.list_hubs(active_only)


def search_hubs(term: str, active_only: bool = True) -> list[dict]:
    """Case-insensitive partial match on name or location."""
    return _svc.search_hubs(term, active_only)


def get_hub_details(hubid: int) -> dict:
    """-> hub row + total_wallets, active_wallets, total_balance."""
    return _svc.get_hub_details(hubid)


def add_hub(hubname: str, location: str) -> int:
    return _svc.add_hub(hubname, location)


def update_hub(hubid: int, hubname: str, location: str) -> None:
    _svc.update_hub(hubid, hubname, location)


def set_hub_active(hubid: int, active: bool) -> None:
    """Deactivation fails with AppError if the hub still has active wallets."""
    _svc.set_hub_active(hubid, active)


def hub_summary_report() -> list[dict]:
    """-> rows: hubid, hubname, isactive, wallet_count, total_balance, avg_bonus_rate."""
    return _svc.hub_summary_report()


# ---------------------------------------------------------------- wallets
def list_player_wallets(playerid: int) -> list[dict]:
    """Wallets the player holds, each with 'holderrole'."""
    return _svc.list_player_wallets(playerid)


def list_all_wallets() -> list[dict]:
    return _svc.list_all_wallets()


def get_wallet(walletid: int, playerid: int | None = None) -> dict:
    """playerid given -> must be a holder."""
    return _svc.get_wallet(walletid, playerid)


def get_wallet_summary(walletid: int, playerid: int | None = None) -> dict:
    """Result of getWalletSummary(walletID). Keys are displayed generically."""
    return _svc.get_wallet_summary(walletid, playerid)


def check_sufficient_balance(walletid: int, amount: Decimal) -> bool:
    """Calls checkSufficientBalance(walletID, requestedAmount)."""
    return _svc.check_sufficient_balance(walletid, amount)


def low_balance_alerts(threshold: Decimal, playerid: int | None = None) -> list[dict]:
    """Calls getLowBalanceAlerts(threshold); restricted to the player's wallets if given."""
    return _svc.low_balance_alerts(threshold, playerid)


def open_wallet(playerid: int, wallettype: str, hubid: int, balance: Decimal,
                minimumbalance: Decimal, bonusrate: Decimal, description: str) -> int:
    """Creates Wallets + Owner WalletHolders row atomically. -> new walletid."""
    return _svc.open_wallet(playerid, wallettype, hubid, balance, minimumbalance,
                            bonusrate, description)


def update_wallet(walletid: int, bonusrate: Decimal, description: str) -> None:
    _svc.update_wallet(walletid, bonusrate, description)


def set_wallet_active(walletid: int, active: bool) -> None:
    _svc.set_wallet_active(walletid, active)


def wallet_inventory() -> list[dict]:
    """Wallets grouped by type: wallettype, wallet_count, active_count, total_balance, avg_balance."""
    return _svc.wallet_inventory()


# ---------------------------------------------------------------- players
def list_players() -> list[dict]:
    return _svc.list_players()


def get_player(playerid: int) -> dict:
    return _svc.get_player(playerid)


def update_player_contact(playerid: int, email: str, phone: str) -> None:
    _svc.update_player_contact(playerid, email, phone)


def set_player_active(playerid: int, active: bool) -> None:
    _svc.set_player_active(playerid, active)


def player_memberships(playerid: int) -> list[dict]:
    return _svc.player_memberships(playerid)


def player_transactions(playerid: int) -> list[dict]:
    return _svc.player_transactions(playerid)


def player_reviews(playerid: int) -> list[dict]:
    return _svc.player_reviews(playerid)


# ---------------------------------------------------------------- transactions
def perform_transaction(walletid: int, amount: Decimal, transactiontype: str,
                        paymentmethod: str, recipient: str,
                        playerid: int | None = None) -> int:
    """TopUp / Cashout / Purchase via performTransaction(). amount is POSITIVE.
    playerid given -> must be Owner or Co-Owner. -> new transactionid."""
    return _svc.perform_transaction(walletid, amount, transactiontype, paymentmethod,
                                    recipient, playerid)


def transfer_funds(from_walletid: int, to_walletid: int, amount: Decimal,
                   paymentmethod: str, playerid: int | None = None) -> int:
    """Calls transferFunds(). -> sending transactionid."""
    return _svc.transfer_funds(from_walletid, to_walletid, amount, paymentmethod, playerid)


def wallet_transactions(walletid: int, date_from: date | None = None,
                        date_to: date | None = None, txn_type: str | None = None,
                        playerid: int | None = None) -> list[dict]:
    return _svc.wallet_transactions(walletid, date_from, date_to, txn_type, playerid)


def totals_by_payment_method(walletid: int | None = None,
                             playerid: int | None = None) -> list[dict]:
    return _svc.totals_by_payment_method(walletid, playerid)


def reverse_transaction(transactionid: int) -> list[int]:
    """Admin only. Restores the balance. -> ids of the reversal rows."""
    return _svc.reverse_transaction(transactionid)


# ---------------------------------------------------------------- reviews
def add_review(playerid: int, walletid: int, rating: int, reviewtext: str) -> int:
    return _svc.add_review(playerid, walletid, rating, reviewtext)


def list_reviews(walletid: int | None = None) -> list[dict]:
    return _svc.list_reviews(walletid)


def set_review_verified(reviewid: int, verified: bool) -> None:
    _svc.set_review_verified(reviewid, verified)


def avg_rating_by_wallet_type() -> list[dict]:
    return _svc.avg_rating_by_wallet_type()


# ---------------------------------------------------------------- analytics (bonus)
def monthly_flows(walletid: int | None = None, playerid: int | None = None) -> list[dict]:
    """-> rows: month ('YYYY-MM'), topups, cashouts, purchases."""
    return _svc.monthly_flows(walletid, playerid)
