import pytest
from services.gameverse_service import GameVerseService

def test_get_wallet_summary():
    success, res = GameVerseService.get_wallet_summary(2001)
    assert success is True

def test_check_sufficient_balance():
    success, res = GameVerseService.check_sufficient_balance(2001, 100.00)
    assert success is True

def test_get_low_balance_alerts():
    success, res = GameVerseService.get_low_balance_alerts(500.00)
    assert success is True

def test_get_player_profile():
    success, res = GameVerseService.get_player_profile(3001)
    print(f"\n[DEBUG] get_player_profile: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_get_wallet_transactions():
    success, res = GameVerseService.get_wallet_transactions(2001)
    print(f"\n[DEBUG] get_wallet_transactions: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_record_transaction():
    success, res = GameVerseService.record_transaction(
        wallet_id=2001,
        amount=50.00,
        transaction_type="Deposit",
        recipient="Self",
        payment_method="Credit Card"
    )
    print(f"\n[DEBUG] record_transaction: success={success}, new_id={res}")
    assert success is True, f"Failed to record transaction: {res}"

def test_get_gaming_hubs():
    success, res = GameVerseService.get_gaming_hubs()
    print(f"\n[DEBUG] get_gaming_hubs: success={success}, res={res}")
    assert success is True, f"Failed to get hubs: {res}"

def test_atomic_transfer():
    success, res = GameVerseService.transfer_funds(2001, 2002, 25.00)
    print(f"\n[DEBUG] atomic_transfer: success={success}, res={res}")
    assert success is True, f"Transfer failed: {res}"