import pytest
from services.gameverse_service import GameVerseService

def test_get_player_profile():
    # Use valid player ID 3001 (Alex Chen)
    success, res = GameVerseService.get_player_profile(3001)
    print(f"\n[DEBUG] get_player_profile: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_get_wallet_transactions():
    # Test transaction history for valid wallet 2001
    success, res = GameVerseService.get_wallet_transactions(2001)
    print(f"\n[DEBUG] get_wallet_transactions: success={success}, res={res}")
    assert success is True, f"Service failed with error: {res}"

def test_record_transaction():
    # Test recording a new deposit transaction on wallet 2001
    success, res = GameVerseService.record_transaction(
        wallet_id=2001,
        amount=50.00,
        transaction_type="Deposit",
        recipient="Self",
        payment_method="Credit Card"
    )
    print(f"\n[DEBUG] record_transaction: success={success}, new_id={res}")
    assert success is True, f"Failed to record transaction: {res}"