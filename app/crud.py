from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from fastapi import HTTPException, status
from .models import User, Transaction
from .schemas import UserRegister
from .security import get_password_hash

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_account_or_username(db: Session, identifier: str):
    clean_id = identifier.strip().replace(" ", "").replace("-", "")
    return db.query(User).filter(
        or_(
            User.username == identifier.strip(),
            User.account_number == clean_id,
            User.account_number == identifier.strip(),
            User.email == identifier.strip()
        )
    ).first()

def create_user(db: Session, user_data: UserRegister):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )

    hashed_pw = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username.strip(),
        email=user_data.email.strip() if user_data.email else None,
        full_name=user_data.full_name.strip() if user_data.full_name else None,
        hashed_password=hashed_pw,
        balance=0.0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def deposit_funds(db: Session, user: User, amount: float, note: str = None):
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than zero"
        )
    
    # Reload user in transaction
    user.balance = round(user.balance + amount, 2)
    
    txn = Transaction(
        sender_id=None,
        receiver_id=user.id,
        transaction_type="DEPOSIT",
        amount=round(amount, 2),
        receiver_balance_after=user.balance,
        note=note or "Cash In / Deposit",
        status="COMPLETED"
    )
    db.add(txn)
    db.commit()
    db.refresh(user)
    db.refresh(txn)
    return txn, user

def withdraw_funds(db: Session, user: User, amount: float, note: str = None):
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than zero"
        )
    if user.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds. Current balance: ${user.balance:,.2f}"
        )
    
    user.balance = round(user.balance - amount, 2)
    
    txn = Transaction(
        sender_id=user.id,
        receiver_id=None,
        transaction_type="WITHDRAWAL",
        amount=round(amount, 2),
        sender_balance_after=user.balance,
        note=note or "Cash Out / Withdrawal",
        status="COMPLETED"
    )
    db.add(txn)
    db.commit()
    db.refresh(user)
    db.refresh(txn)
    return txn, user

def transfer_funds(db: Session, sender: User, recipient_identifier: str, amount: float, note: str = None):
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than zero"
        )
    
    recipient = get_user_by_account_or_username(db, recipient_identifier)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient '{recipient_identifier}' not found"
        )
    
    if recipient.id == sender.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot transfer funds to yourself"
        )
    
    if sender.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: ${sender.balance:,.2f}"
        )
    
    # Atomic deduction and credit
    sender.balance = round(sender.balance - amount, 2)
    recipient.balance = round(recipient.balance + amount, 2)
    
    txn = Transaction(
        sender_id=sender.id,
        receiver_id=recipient.id,
        transaction_type="TRANSFER",
        amount=round(amount, 2),
        sender_balance_after=sender.balance,
        receiver_balance_after=recipient.balance,
        note=note or f"Transfer to {recipient.username}",
        status="COMPLETED"
    )
    db.add(txn)
    db.commit()
    db.refresh(sender)
    db.refresh(recipient)
    db.refresh(txn)
    return txn, sender, recipient

def format_transaction_response(txn: Transaction, current_user_id: int):
    # Determines balance_after based on perspective
    sender_name = txn.sender.username if txn.sender else "External / Cash In"
    receiver_name = txn.receiver.username if txn.receiver else "External / Cash Out"
    
    balance_after = None
    if txn.sender_id == current_user_id:
        balance_after = txn.sender_balance_after
    elif txn.receiver_id == current_user_id:
        balance_after = txn.receiver_balance_after

    return {
        "id": txn.id,
        "reference_id": txn.reference_id,
        "transaction_type": txn.transaction_type,
        "amount": txn.amount,
        "sender_id": txn.sender_id,
        "sender_username": sender_name,
        "receiver_id": txn.receiver_id,
        "receiver_username": receiver_name,
        "note": txn.note,
        "status": txn.status,
        "created_at": txn.created_at,
        "balance_after": balance_after
    }

def get_user_transactions(db: Session, user_id: int, limit: int = 50, offset: int = 0, txn_type: str = None):
    query = db.query(Transaction).filter(
        or_(Transaction.sender_id == user_id, Transaction.receiver_id == user_id)
    )
    if txn_type and txn_type.upper() in ["DEPOSIT", "WITHDRAWAL", "TRANSFER"]:
        query = query.filter(Transaction.transaction_type == txn_type.upper())
    
    txns = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
    return [format_transaction_response(t, user_id) for t in txns]

def get_dashboard_summary(db: Session, user: User):
    all_txns = db.query(Transaction).filter(
        or_(Transaction.sender_id == user.id, Transaction.receiver_id == user.id)
    ).order_by(desc(Transaction.created_at)).all()

    total_inflow = sum(
        t.amount for t in all_txns 
        if (t.transaction_type == "DEPOSIT" and t.receiver_id == user.id) or 
           (t.transaction_type == "TRANSFER" and t.receiver_id == user.id)
    )
    
    total_outflow = sum(
        t.amount for t in all_txns 
        if (t.transaction_type == "WITHDRAWAL" and t.sender_id == user.id) or 
           (t.transaction_type == "TRANSFER" and t.sender_id == user.id)
    )

    recent = [format_transaction_response(t, user.id) for t in all_txns[:10]]

    return {
        "user": user,
        "balance": user.balance,
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "transaction_count": len(all_txns),
        "recent_transactions": recent
    }
