"""Frontend-only tests: input parsing used by the GUI forms (no database needed).

The business-rule tests (balance validation, trigger, transfers...) belong to
the backend branch because they test the service layer against the real DB.
"""
from datetime import date
from decimal import Decimal

import pytest

from gui import validators as v


@pytest.mark.parametrize("raw,expected", [
    ("250", Decimal("250.00")), ("1,500.50", Decimal("1500.50")), ("$3000", Decimal("3000.00")),
])
def test_money_accepts_valid_amounts(raw, expected):
    assert v.money(raw) == expected


@pytest.mark.parametrize("raw", ["abc", "-5", "0", "1.234", "nan", "inf", "99999999999"])
def test_money_rejects_bad_amounts(raw):
    with pytest.raises(ValueError):
        v.money(raw)


def test_money_or_zero_allows_zero():
    assert v.money_or_zero("0") == Decimal("0.00")


@pytest.mark.parametrize("raw,ok", [("0", True), ("5", True), ("2.5", True), ("5.01", False),
                                    ("-1", False), ("x", False)])
def test_bonus_rate_range(raw, ok):
    if ok:
        assert 0 <= v.rate_0_to_5(raw) <= 5
    else:
        with pytest.raises(ValueError):
            v.rate_0_to_5(raw)


def test_iso_date():
    assert v.iso_date("2000-07-22") == date(2000, 7, 22)
    with pytest.raises(ValueError):
        v.iso_date("22/07/2000")


@pytest.mark.parametrize("raw,ok", [("a@b.com", True), ("bad", False), ("a@b", False)])
def test_email(raw, ok):
    if ok:
        assert v.email(raw) == raw
    else:
        with pytest.raises(ValueError):
            v.email(raw)


def test_password_min_length():
    assert v.password("secret1") == "secret1"
    with pytest.raises(ValueError):
        v.password("123")


def test_integer():
    assert v.integer(" 2001 ") == 2001
    with pytest.raises(ValueError):
        v.integer("20x1")
