# ⚡ BankMS Neo v2.0 - Next-Gen Banking Management System

A high-performance, full-stack Banking & Financial Ledger application built with **FastAPI**, **SQLAlchemy 2.0 (SQLite/PostgreSQL)**, **JWT Authentication & Bcrypt Password Hashing**, and a **Sleek Modern Fintech Dashboard UI**.

---

## 🌟 Key Features

- 🔐 **Secure Authentication**: Salted Bcrypt password hashing + stateless JWT Bearer token authentication.
- 💳 **Virtual Account & Card**: Generated 10-digit account numbers with dynamic card preview and instant copy.
- ⚡ **Atomic Financial Operations**: ACID-compliant transactions with rollback protection against overdrafts and race conditions.
- 💰 **Cash In / Cash Out**: Instant deposit and withdrawal operations with audit trails.
- 🚀 **Peer-to-Peer Transfers**: Send money between accounts using username or account number with live recipient verification.
- 📊 **Interactive Analytics**: Real-time cashflow chart (Inflow vs. Outflow) with Chart.js.
- 📑 **Transaction Ledger**: Filter by Deposit, Withdrawal, Transfer, full-text search, and **Export to CSV**.
- 📚 **Interactive Swagger API**: Auto-generated interactive OpenAPI docs at `/docs`.

---

## 🏗️ Architecture & Project Structure

```
BANKMS/
├── app/
│   ├── static/               # Frontend Single Page App
│   │   ├── css/style.css     # Modern Glassmorphic Fintech Design
│   │   ├── js/app.js         # Frontend Logic & Chart.js Integration
│   │   └── index.html        # Single Page Dashboard & Auth UI
│   ├── database.py           # SQLAlchemy Engine & Session
│   ├── models.py             # User & Transaction DB Models
│   ├── schemas.py            # Pydantic Schemas for Validation
│   ├── security.py           # Bcrypt & JWT Token Security
│   ├── crud.py               # Banking Logic & Ledger Operations
│   └── main.py               # FastAPI App & API Endpoints
├── migrate_legacy.py         # Migration script for legacy text files
├── test_bank.py              # Automated Integration & Unit Tests
├── run.py                    # Server Runner Entrypoint
├── requirements.txt          # Python Dependencies
└── bank.py                   # (Legacy CLI Version preserved)
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Migrate Legacy Flat Files
If you have existing `user_data.txt` and `balance_data.txt`:
```bash
python migrate_legacy.py
```

### 3. Run the Server
```bash
python run.py
```
Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Open in Browser
- **Web App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 👤 Default Demo Accounts

For instant testing out of the box:
- **Alice**: Username: `alice` | Password: `password123`
- **Bob**: Username: `bob` | Password: `password123`

---

## 🧪 Running Automated Tests
```bash
python test_bank.py
```
or with pytest:
```bash
pytest test_bank.py
```
