"""Input parsers used by forms. Each raises ValueError with a short message.

These only check *format* (is it a number? a date?). Business rules such as
minimum balance, age >= 13 or one review per wallet stay in the database.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\-\s]{7,20}$")


def text(max_len: int):
    def parse(raw: str) -> str:
        if len(raw) > max_len:
            raise ValueError(f"must be at most {max_len} characters")
        return raw
    return parse


def money(raw: str, allow_zero: bool = False) -> Decimal:
    cleaned = raw.replace(",", "").replace("$", "").strip()
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError("enter a number like 250.00") from None
    if not value.is_finite():
        raise ValueError("enter a number like 250.00")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError("must be greater than zero" if not allow_zero else "cannot be negative")
    if value.as_tuple().exponent < -2:
        raise ValueError("use at most 2 decimal places")
    if value >= Decimal("10000000000"):
        raise ValueError("amount is too large")
    return value.quantize(Decimal("0.01"))


def money_or_zero(raw: str) -> Decimal:
    return money(raw, allow_zero=True)


def integer(raw: str) -> int:
    try:
        return int(raw.strip())
    except ValueError:
        raise ValueError("enter a whole number") from None


def rate_0_to_5(raw: str) -> Decimal:
    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        raise ValueError("enter a number between 0 and 5") from None
    if not (0 <= value <= 5):
        raise ValueError("must be between 0 and 5")
    return value.quantize(Decimal("0.01"))


def iso_date(raw: str) -> date:
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("use the format YYYY-MM-DD") from None


def email(raw: str) -> str:
    raw = raw.strip()
    if not EMAIL_RE.match(raw):
        raise ValueError("enter a valid email address")
    if len(raw) > 150:
        raise ValueError("must be at most 150 characters")
    return raw


def phone(raw: str) -> str:
    raw = raw.strip()
    if not PHONE_RE.match(raw):
        raise ValueError("enter a valid phone number, e.g. 904-555-0201")
    return raw


def password(raw: str) -> str:
    if len(raw) < 6:
        raise ValueError("must be at least 6 characters")
    return raw
