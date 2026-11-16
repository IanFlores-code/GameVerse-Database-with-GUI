import pytest
from services.gameverse_service import GameVerseService

def test_check_sufficient_balance():
    # Use valid wallet ID 2001 which has a balance of 2500.00
    success, res = GameVerseService.check_sufficient_balance(2001, 10.00)
    print(f"\n[DEBUG] check_sufficient_balance: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_get_low_balance_alerts():
    # Test low balance alerts with a threshold
    success, res = GameVerseService.get_low_balance_alerts(500.00)
    print(f"\n[DEBUG] get_low_balance_alerts: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_wallet_summary_structure():
    # Test fetching wallet summary for wallet 2001
    success, res = GameVerseService.get_wallet_summary(2001)
    print(f"\n[DEBUG] get_wallet_summary: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"