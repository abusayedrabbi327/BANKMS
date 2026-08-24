"""
Migration utility: Imports legacy flat-file users and balances from user_data.txt and balance_data.txt into the SQLite database.
"""
import os
import sys
from app.database import SessionLocal, Base, engine
from app.models import User, Transaction
from app.security import get_password_hash

def migrate():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    user_file = "user_data.txt"
    balance_file = "balance_data.txt"
    
    if not os.path.exists(user_file):
        print(f"[*] No {user_file} found. Skipping legacy migration.")
        db.close()
        return

    # Read balances
    balances = {}
    if os.path.exists(balance_file):
        with open(balance_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                parts = line.split(":", 1)
                try:
                    balances[parts[0]] = float(parts[1])
                except ValueError:
                    balances[parts[0]] = 0.0

    # Read users
    migrated_count = 0
    with open(user_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            username, password = line.split(":", 1)
            
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                print(f"[!] User '{username}' already exists in database. Skipping.")
                continue

            balance = balances.get(username, 0.0)
            new_user = User(
                username=username,
                email=f"{username}@example.com",
                full_name=username.capitalize(),
                hashed_password=get_password_hash(password),
                balance=balance
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            if balance > 0:
                txn = Transaction(
                    sender_id=None,
                    receiver_id=new_user.id,
                    transaction_type="DEPOSIT",
                    amount=balance,
                    receiver_balance_after=balance,
                    note="Legacy Account Balance Migration"
                )
                db.add(txn)
                db.commit()
            
            migrated_count += 1
            print(f"[+] Migrated user: {username} with balance ${balance:,.2f}")

    db.close()
    print(f"[OK] Migration finished. Total imported: {migrated_count}")

if __name__ == "__main__":
    migrate()
