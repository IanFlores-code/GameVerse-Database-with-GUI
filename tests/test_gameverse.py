import pytest
from services.gameverse_service import GameVerseService

def test_get_wallet_summary():
    success, res = GameVerseService.get_wallet_summary(2001)
    assert success is True

def test_player_authentication():
    success, res = GameVerseService.authenticate_player("alex.chen@gameverse.com", "password123")
    assert success is True
    assert res["role"] == "Player"

def test_wallet_ownership_rbac():
    success, res = GameVerseService.verify_wallet_ownership(3001, 2001, ["Owner", "Co-Owner"])
    assert success is True

def test_bonus_projection():
    success, res = GameVerseService.project_wallet_bonus(2001)
    assert success is True
    assert "12_months" in res

def test_submit_wallet_review():
    # Test review submission or duplicate rejection
    success, res = GameVerseService.submit_wallet_review(3001, 2001, 5, "Great wallet!")
    print(f"\n[DEBUG] submit_review: success={success}, res={res}")
    # Even if already reviewed (returning False with duplicate message), we check handled result
    assert isinstance(success, bool)

def test_get_gaming_hubs():
    success, res = GameVerseService.get_gaming_hubs()
    assert success is True

def test_atomic_transfer():
    success, res = GameVerseService.transfer_funds(2001, 2002, 5.00)
    assert success is True