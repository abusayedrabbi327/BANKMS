import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

# Auth Schemas
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=4, max_length=100, description="Account password")
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    account_number: str
    balance: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

# Transaction Schemas
class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit (must be greater than 0)")
    note: Optional[str] = Field(None, max_length=200)

class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw (must be greater than 0)")
    note: Optional[str] = Field(None, max_length=200)

class TransferRequest(BaseModel):
    recipient: str = Field(..., description="Recipient username or 10-digit account number")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    note: Optional[str] = Field(None, max_length=200)

class TransactionResponse(BaseModel):
    id: int
    reference_id: str
    transaction_type: str
    amount: float
    sender_id: Optional[int] = None
    sender_username: Optional[str] = None
    receiver_id: Optional[int] = None
    receiver_username: Optional[str] = None
    note: Optional[str] = None
    status: str
    created_at: datetime.datetime
    balance_after: Optional[float] = None

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    user: UserProfile
    balance: float
    total_inflow: float
    total_outflow: float
    transaction_count: int
    recent_transactions: List[TransactionResponse]
