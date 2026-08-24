import uuid
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from .database import Base

def generate_account_number():
    # Deterministic-length clean account number
    uid = uuid.uuid4().int % 10000000000
    return f"{uid:010d}"

def generate_reference_id():
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    account_number = Column(String(20), unique=True, index=True, default=generate_account_number)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    sent_transactions = relationship(
        "Transaction",
        foreign_keys="[Transaction.sender_id]",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_transactions = relationship(
        "Transaction",
        foreign_keys="[Transaction.receiver_id]",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String(30), unique=True, index=True, default=generate_reference_id)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    transaction_type = Column(String(20), nullable=False)  # DEPOSIT, WITHDRAWAL, TRANSFER
    amount = Column(Float, nullable=False)
    sender_balance_after = Column(Float, nullable=True)
    receiver_balance_after = Column(Float, nullable=True)
    note = Column(String(255), nullable=True)
    status = Column(String(20), default="COMPLETED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_transactions")
