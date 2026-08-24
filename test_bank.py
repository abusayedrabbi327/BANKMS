"""
Comprehensive Test Suite for BankMS Neo
"""
import os
import sys

# Set test database
os.environ["DATABASE_URL"] = "sqlite:///./test_bank.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, Transaction

client = TestClient(app)

def setup_module():
    # Clean test db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_bank.db"):
        try:
            os.remove("./test_bank.db")
        except PermissionError:
            pass

def test_full_banking_workflow():
    print("Testing user registration...")
    # 1. Register User 1 (Charlie)
    r1 = client.post("/api/auth/register", json={
        "username": "charlie",
        "password": "secretpassword",
        "full_name": "Charlie Chaplin",
        "email": "charlie@bankms.io"
    })
    assert r1.status_code == 201, r1.text
    token_charlie = r1.json()["access_token"]
    headers_charlie = {"Authorization": f"Bearer {token_charlie}"}

    # 2. Register User 2 (Diana)
    r2 = client.post("/api/auth/register", json={
        "username": "diana",
        "password": "secretpassword",
        "full_name": "Diana Prince",
        "email": "diana@bankms.io"
    })
    assert r2.status_code == 201, r2.text
    token_diana = r2.json()["access_token"]
    headers_diana = {"Authorization": f"Bearer {token_diana}"}

    # 3. Test Login
    login_res = client.post("/api/auth/login", json={
        "username": "charlie",
        "password": "secretpassword"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Deposit funds into Charlie's account
    dep_res = client.post("/api/transactions/deposit", headers=headers_charlie, json={
        "amount": 1500.0,
        "note": "Initial Paycheck"
    })
    assert dep_res.status_code == 200
    assert dep_res.json()["amount"] == 1500.0
    assert dep_res.json()["balance_after"] == 1500.0

    # 5. Withdraw funds from Charlie
    with_res = client.post("/api/transactions/withdraw", headers=headers_charlie, json={
        "amount": 200.0,
        "note": "ATM Cash Out"
    })
    assert with_res.status_code == 200
    assert with_res.json()["balance_after"] == 1300.0

    # 6. Test Overdraft protection
    bad_with = client.post("/api/transactions/withdraw", headers=headers_charlie, json={
        "amount": 5000.0,
        "note": "Exceeding balance"
    })
    assert bad_with.status_code == 400

    # 7. Transfer funds from Charlie to Diana ($300)
    transfer_res = client.post("/api/transactions/transfer", headers=headers_charlie, json={
        "recipient": "diana",
        "amount": 300.0,
        "note": "Birthday Gift"
    })
    assert transfer_res.status_code == 200
    assert transfer_res.json()["balance_after"] == 1000.0

    # 8. Check Diana's summary (should have $300 balance)
    diana_summary = client.get("/api/account/summary", headers=headers_diana)
    assert diana_summary.status_code == 200
    assert diana_summary.json()["balance"] == 300.0
    assert diana_summary.json()["total_inflow"] == 300.0

    # 9. Lookup recipient
    lookup = client.get("/api/account/lookup/charlie", headers=headers_diana)
    assert lookup.status_code == 200
    assert lookup.json()["username"] == "charlie"

    # 10. Check Transaction Ledger
    history = client.get("/api/transactions/history", headers=headers_charlie)
    assert history.status_code == 200
    assert len(history.json()) == 3  # deposit, withdraw, transfer

    print("All automated tests passed successfully!")

if __name__ == "__main__":
    setup_module()
    test_full_banking_workflow()
    teardown_module()
    print("[OK] Test suite completed with 100% success.")
