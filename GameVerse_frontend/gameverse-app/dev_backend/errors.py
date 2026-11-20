"""Turns database errors into short, user-friendly messages.

The GUI never shows a stack trace: every psycopg2 error is converted to an
AppError whose message is safe to show in a dialog.
"""
import psycopg2
from psycopg2 import errorcodes


class AppError(Exception):
    """An error whose message can be shown directly to the user."""


# Assignment 3 constraint name -> message shown to the user
CONSTRAINT_MESSAGES = {
    "chk_wallet_balance_min": "This would take the wallet below its minimum balance.",
    "chk_wallet_bonusrate": "Bonus rate must be between 0 and 5.",
    "chk_wallet_type": "Wallet type must be Standard, Vault or Guild.",
    "chk_txn_amount_nonzero": "Transaction amount cannot be zero.",
    "chk_txn_sign_matches_type": "The amount sign does not match the transaction type.",
    "chk_player_min_age": "Players must be at least 13 years old to register.",
    "chk_player_reg_not_future": "Registration date cannot be in the future.",
    "players_email_key": "That email address is already registered.",
    "uq_review_player_wallet": "You have already reviewed this wallet. Only one review per wallet is allowed.",
    "walletreviews_rating_check": "Rating must be between 1 and 5.",
    "chk_review_date_not_future": "Review date cannot be in the future.",
    "uq_one_owner_per_wallet": "This wallet already has an Owner.",
    "walletholders_pkey": "That player already holds this wallet.",
    "fk_holder_player": "That player does not exist.",
    "fk_holder_wallet": "That wallet does not exist.",
    "wallets_hubid_fkey": "That hub does not exist.",
    "gametransactions_walletid_fkey": "That wallet does not exist.",
    "walletreviews_walletid_fkey": "That wallet does not exist.",
    "walletreviews_playerid_fkey": "That player does not exist.",
    "admins_username_key": "That admin username is already taken.",
}

GENERIC_BY_CODE = {
    errorcodes.UNIQUE_VIOLATION: "A record with those details already exists.",
    errorcodes.CHECK_VIOLATION: "The values entered break a business rule.",
    errorcodes.FOREIGN_KEY_VIOLATION: "A referenced record does not exist or is still in use.",
    errorcodes.NOT_NULL_VIOLATION: "A required field is missing.",
    errorcodes.NUMERIC_VALUE_OUT_OF_RANGE: "A number entered is too large.",
    errorcodes.INVALID_TEXT_REPRESENTATION: "A value has the wrong format.",
    errorcodes.STRING_DATA_RIGHT_TRUNCATION: "A text value is too long.",
}


def friendly(err: Exception) -> AppError:
    """Convert any exception from the DB layer to an AppError."""
    if isinstance(err, AppError):
        return err
    if isinstance(err, psycopg2.OperationalError):
        return AppError(
            "Cannot reach the database. Check that PostgreSQL is running and "
            "that your .env settings (host, port, database, user, password) are correct."
        )
    if isinstance(err, psycopg2.Error):
        diag = getattr(err, "diag", None)
        constraint = getattr(diag, "constraint_name", None) if diag else None
        if constraint and constraint in CONSTRAINT_MESSAGES:
            return AppError(CONSTRAINT_MESSAGES[constraint])
        # RAISE EXCEPTION inside our PL/pgSQL functions/triggers
        if err.pgcode == errorcodes.RAISE_EXCEPTION and diag and diag.message_primary:
            return AppError(diag.message_primary)
        if err.pgcode in GENERIC_BY_CODE:
            return AppError(GENERIC_BY_CODE[err.pgcode])
        primary = diag.message_primary if diag else None
        return AppError(f"Database error: {primary or 'unknown error'}")
    return AppError(f"Unexpected error: {err}")
