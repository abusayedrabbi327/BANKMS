import os

USER_DATA_FILE = "user_data.txt"
BALANCE_FILE = "balance_data.txt"

def create_user(username, password):
    with open(USER_DATA_FILE, "a") as file:
        file.write(f"{username}:{password}\n")
    with open(BALANCE_FILE, "a") as file:
        file.write(f"{username}:0.0\n")

def authenticate_user(username, password):
    with open(USER_DATA_FILE, "r") as file:
        for line in file:
            stored_username, stored_password = line.strip().split(":")
            if username == stored_username and password == stored_password:
                return True
    return False

def get_balance(username):
    with open(BALANCE_FILE, "r") as file:
        for line in file:
            stored_username, balance = line.strip().split(":")
            if username == stored_username:
                return float(balance)
    return None

def update_balance(username, new_balance):
    with open(BALANCE_FILE, "r") as file:
        lines = file.readlines()
    with open(BALANCE_FILE, "w") as file:
        for line in lines:
            stored_username, _ = line.strip().split(":")
            if username == stored_username:
                file.write(f"{username}:{new_balance}\n")
            else:
                file.write(line)

def main():
    while True:
        print("1. Register")
        print("2. Sign In")
        print("3. Quit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            create_user(username, password)
            print("User registered successfully!")
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            if authenticate_user(username, password):
                print("Authentication successful!")
                while True:
                    print("1. Display Balance")
                    print("2. Transfer Funds")
                    print("3. Cash In")
                    print("4. Cash Out")
                    print("5. Sign Out")
                    account_choice = input("Enter your choice: ")
                    if account_choice == '1':
                        balance = get_balance(username)
                        if balance is not None:
                            print(f"Your account balance: {balance}")
                    elif account_choice == '2':
                        recipient = input("Enter recipient's username: ")
                        amount = float(input("Enter amount to transfer: "))
                        sender_balance = get_balance(username)
                        if sender_balance is not None and sender_balance >= amount:
                            recipient_balance = get_balance(recipient)
                            if recipient_balance is not None:
                                update_balance(username, sender_balance - amount)
                                update_balance(recipient, recipient_balance + amount)
                                print("Transfer successful!")
                            else:
                                print("Recipient not found.")
                        else:
                            print("Insufficient balance for transfer.")
                    elif account_choice == '3':
                        amount = float(input("Enter amount to cash in: "))
                        current_balance = get_balance(username)
                        if current_balance is not None:
                            update_balance(username, current_balance + amount)
                            print("Cash in successful!")
                    elif account_choice == '4':
                        amount = float(input("Enter amount to cash out: "))
                        current_balance = get_balance(username)
                        if current_balance is not None and current_balance >= amount:
                            update_balance(username, current_balance - amount)
                            print("Cash out successful!")
                        else:
                            print("Insufficient balance for cash out.")
                    elif account_choice == '5':
                        print("Signed out.")
                        break
                    else:
                        print("Invalid choice. Please select again.")
            else:
                print("Authentication failed.")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select again.")

if __name__ == "__main__":
    main()
