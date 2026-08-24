import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import engine, Base, get_db
from .models import User, Transaction
from .schemas import (
    UserRegister, UserLogin, UserProfile, TokenResponse,
    DepositRequest, WithdrawRequest, TransferRequest,
    TransactionResponse, DashboardSummary
)
from .security import (
    verify_password, create_access_token, get_current_user,
    get_password_hash
)
from .crud import (
    create_user, get_user_by_username, get_user_by_account_or_username,
    deposit_funds, withdraw_funds, transfer_funds,
    get_user_transactions, get_dashboard_summary, format_transaction_response
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BankMS Neo - Modern Banking System",
    description="Next-Generation Bank Management API with JWT Auth & Transaction Ledger",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure demo user exists on fresh install for easy exploration
@app.on_event("startup")
def startup_populate_demo():
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            # Create Demo User Alice
            alice = User(
                username="alice",
                email="alice@bankms.io",
                full_name="Alice Sterling",
                hashed_password=get_password_hash("password123"),
                balance=2500.0,
                account_number="8841029410"
            )
            bob = User(
                username="bob",
                email="bob@bankms.io",
                full_name="Robert Vance",
                hashed_password=get_password_hash("password123"),
                balance=750.0,
                account_number="5519203941"
            )
            db.add_all([alice, bob])
            db.commit()
            db.refresh(alice)
            db.refresh(bob)

            # Initial transactions
            t1 = Transaction(
                sender_id=None,
                receiver_id=alice.id,
                transaction_type="DEPOSIT",
                amount=3000.0,
                receiver_balance_after=3000.0,
                note="Initial Account Deposit",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
            )
            t2 = Transaction(
                sender_id=alice.id,
                receiver_id=bob.id,
                transaction_type="TRANSFER",
                amount=500.0,
                sender_balance_after=2500.0,
                receiver_balance_after=750.0,
                note="Dinner bill split",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
            )
            db.add_all([t1, t2])
            db.commit()
    finally:
        db.close()


# -------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# -------------------------------------------------------------

@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    user = create_user(db, user_data)
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/auth/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_username(db, login_data.username.strip())
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=UserProfile)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


# -------------------------------------------------------------
# ACCOUNT & DASHBOARD ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/account/summary", response_model=DashboardSummary)
def account_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_dashboard_summary(db, current_user)

@app.get("/api/account/lookup/{identifier}")
def lookup_recipient(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = get_user_by_account_or_username(db, identifier)
    if not target:
        raise HTTPException(status_code=404, detail="Recipient account not found")
    if target.id == current_user.id:
        return {"id": target.id, "username": target.username, "full_name": target.full_name, "is_self": True}
    return {
        "id": target.id,
        "username": target.username,
        "full_name": target.full_name,
        "account_number": target.account_number,
        "is_self": False
    }


# -------------------------------------------------------------
# TRANSACTION ENDPOINTS
# -------------------------------------------------------------

@app.post("/api/transactions/deposit", response_model=TransactionResponse)
def deposit(
    req: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn, _ = deposit_funds(db, current_user, req.amount, req.note)
    return format_transaction_response(txn, current_user.id)

@app.post("/api/transactions/withdraw", response_model=TransactionResponse)
def withdraw(
    req: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn, _ = withdraw_funds(db, current_user, req.amount, req.note)
    return format_transaction_response(txn, current_user.id)

@app.post("/api/transactions/transfer", response_model=TransactionResponse)
def transfer(
    req: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn, _, _ = transfer_funds(db, current_user, req.recipient, req.amount, req.note)
    return format_transaction_response(txn, current_user.id)

@app.get("/api/transactions/history", response_model=List[TransactionResponse])
def transaction_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_transactions(db, current_user.id, limit=limit, offset=offset, txn_type=type)


# -------------------------------------------------------------
# STATIC FRONTEND SERVING
# -------------------------------------------------------------

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "BankMS Backend Running. Visit /docs for Swagger UI."}
