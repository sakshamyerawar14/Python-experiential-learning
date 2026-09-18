import json
import os
import hashlib
import secrets
from datetime import datetime

DATA_FILE = "bank_data.json"
LOG_FILE = "bank_activity.log"


def hash_pin(pin):
    salt = "smart-banking-salt-v1"
    return hashlib.sha256((salt + pin).encode()).hexdigest()


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"accounts": {}, "transactions": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {"accounts": {}, "transactions": []}


def save_data(data):
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temp_file, DATA_FILE)


def log_activity(action, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {action}: {details}\n")


def generate_account_number(accounts):
    while True:
        number = str(secrets.randbelow(9000000000) + 1000000000)
        if number not in accounts:
            return number


def generate_transaction_id():
    return "TXN" + datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(3).upper()


def add_transaction(data, account_number, transaction_type, amount, balance, description):
    transaction = {
        "transaction_id": generate_transaction_id(),
        "account_number": account_number,
        "type": transaction_type,
        "amount": round(amount, 2),
        "balance_after": round(balance, 2),
        "description": description,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["transactions"].append(transaction)
    return transaction


def valid_amount(amount):
    return amount > 0


def create_account(data):
    print("\n--- CREATE ACCOUNT ---")
    name = input("Customer name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    while True:
        pin = input("Create 4-digit PIN: ").strip()
        if pin.isdigit() and len(pin) == 4:
            break
        print("PIN must contain exactly 4 digits.")

    while True:
        try:
            initial_deposit = float(input("Initial deposit: ₹"))
            if initial_deposit >= 0:
                break
            print("Deposit cannot be negative.")
        except ValueError:
            print("Enter a valid amount.")

    account_number = generate_account_number(data["accounts"])
    data["accounts"][account_number] = {
        "name": name,
        "pin_hash": hash_pin(pin),
        "balance": round(initial_deposit, 2),
        "status": "ACTIVE",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if initial_deposit > 0:
        add_transaction(
            data,
            account_number,
            "DEPOSIT",
            initial_deposit,
            initial_deposit,
            "Initial deposit"
        )

    save_data(data)
    log_activity("ACCOUNT_CREATED", f"Account {account_number} created")
    print(f"\nAccount created successfully.")
    print(f"Account Number: {account_number}")
    print(f"Account Holder: {name}")
    print(f"Balance: ₹{initial_deposit:.2f}")


def authenticate(data):
    account_number = input("Account number: ").strip()
    account = data["accounts"].get(account_number)

    if not account:
        print("Account not found.")
        return None

    if account["status"] != "ACTIVE":
        print("Account is not active.")
        return None

    pin = input("PIN: ").strip()
    if hash_pin(pin) != account["pin_hash"]:
        log_activity("LOGIN_FAILED", f"Failed login for account {account_number}")
        print("Invalid PIN.")
        return None

    log_activity("LOGIN_SUCCESS", f"Account {account_number} logged in")
    return account_number


def deposit(data, account_number):
    try:
        amount = float(input("Deposit amount: ₹"))
    except ValueError:
        print("Enter a valid amount.")
        return

    if not valid_amount(amount):
        print("Amount must be greater than zero.")
        return

    account = data["accounts"][account_number]
    account["balance"] = round(account["balance"] + amount, 2)

    transaction = add_transaction(
        data,
        account_number,
        "DEPOSIT",
        amount,
        account["balance"],
        "Cash deposit"
    )

    save_data(data)
    log_activity(
        "DEPOSIT",
        f"Account {account_number}, Amount ₹{amount:.2f}, Transaction {transaction['transaction_id']}"
    )
    print(f"Deposit successful. New balance: ₹{account['balance']:.2f}")


def withdraw(data, account_number):
    try:
        amount = float(input("Withdrawal amount: ₹"))
    except ValueError:
        print("Enter a valid amount.")
        return

    if not valid_amount(amount):
        print("Amount must be greater than zero.")
        return

    account = data["accounts"][account_number]

    if amount > account["balance"]:
        print("Insufficient balance.")
        return

    account["balance"] = round(account["balance"] - amount, 2)

    transaction = add_transaction(
        data,
        account_number,
        "WITHDRAW",
        amount,
        account["balance"],
        "Cash withdrawal"
    )

    save_data(data)
    log_activity(
        "WITHDRAW",
        f"Account {account_number}, Amount ₹{amount:.2f}, Transaction {transaction['transaction_id']}"
    )
    print(f"Withdrawal successful. New balance: ₹{account['balance']:.2f}")


def transfer(data, sender_number):
    receiver_number = input("Receiver account number: ").strip()

    if receiver_number == sender_number:
        print("You cannot transfer money to the same account.")
        return

    receiver = data["accounts"].get(receiver_number)
    if not receiver:
        print("Receiver account not found.")
        return

    if receiver["status"] != "ACTIVE":
        print("Receiver account is not active.")
        return

    try:
        amount = float(input("Transfer amount: ₹"))
    except ValueError:
        print("Enter a valid amount.")
        return

    if not valid_amount(amount):
        print("Amount must be greater than zero.")
        return

    sender = data["accounts"][sender_number]

    if amount > sender["balance"]:
        print("Insufficient balance.")
        return

    sender["balance"] = round(sender["balance"] - amount, 2)
    receiver["balance"] = round(receiver["balance"] + amount, 2)

    transaction_id = generate_transaction_id()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sender_transaction = {
        "transaction_id": transaction_id,
        "account_number": sender_number,
        "type": "TRANSFER_OUT",
        "amount": round(amount, 2),
        "balance_after": sender["balance"],
        "description": f"Transfer to {receiver_number}",
        "timestamp": timestamp
    }

    receiver_transaction = {
        "transaction_id": transaction_id,
        "account_number": receiver_number,
        "type": "TRANSFER_IN",
        "amount": round(amount, 2),
        "balance_after": receiver["balance"],
        "description": f"Transfer from {sender_number}",
        "timestamp": timestamp
    }

    data["transactions"].extend([sender_transaction, receiver_transaction])
    save_data(data)

    log_activity(
        "TRANSFER",
        f"₹{amount:.2f} from {sender_number} to {receiver_number}, Transaction {transaction_id}"
    )

    print("Transfer successful.")
    print(f"Transaction ID: {transaction_id}")
    print(f"New balance: ₹{sender['balance']:.2f}")


def show_balance(data, account_number):
    account = data["accounts"][account_number]
    print(f"\nAccount Holder: {account['name']}")
    print(f"Account Number: {account_number}")
    print(f"Balance: ₹{account['balance']:.2f}")
    print(f"Status: {account['status']}")


def show_transactions(data, account_number):
    transactions = [
        transaction
        for transaction in data["transactions"]
        if transaction["account_number"] == account_number
    ]

    print("\n--- TRANSACTION HISTORY ---")

    if not transactions:
        print("No transactions found.")
        return

    for transaction in transactions:
        print(
            f"{transaction['timestamp']} | "
            f"{transaction['type']:<14} | "
            f"₹{transaction['amount']:.2f} | "
            f"Balance ₹{transaction['balance_after']:.2f} | "
            f"{transaction['transaction_id']} | "
            f"{transaction['description']}"
        )


def change_pin(data, account_number):
    while True:
        new_pin = input("New 4-digit PIN: ").strip()
        if new_pin.isdigit() and len(new_pin) == 4:
            break
        print("PIN must contain exactly 4 digits.")

    confirm_pin = input("Confirm new PIN: ").strip()

    if new_pin != confirm_pin:
        print("PIN confirmation does not match.")
        return

    data["accounts"][account_number]["pin_hash"] = hash_pin(new_pin)
    save_data(data)
    log_activity("PIN_CHANGED", f"PIN changed for account {account_number}")
    print("PIN changed successfully.")


def close_account(data, account_number):
    account = data["accounts"][account_number]

    if account["balance"] != 0:
        print("Account can only be closed when balance is ₹0.")
        return

    confirm = input("Type CLOSE to confirm: ").strip()

    if confirm != "CLOSE":
        print("Account closure cancelled.")
        return

    account["status"] = "CLOSED"
    save_data(data)
    log_activity("ACCOUNT_CLOSED", f"Account {account_number} closed")
    print("Account closed successfully.")


def customer_menu(data, account_number):
    while True:
        print("\n========== CUSTOMER MENU ==========")
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transfer Money")
        print("5. Transaction History")
        print("6. Change PIN")
        print("7. Close Account")
        print("8. Logout")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_balance(data, account_number)
        elif choice == "2":
            deposit(data, account_number)
        elif choice == "3":
            withdraw(data, account_number)
        elif choice == "4":
            transfer(data, account_number)
        elif choice == "5":
            show_transactions(data, account_number)
        elif choice == "6":
            change_pin(data, account_number)
        elif choice == "7":
            close_account(data, account_number)
            if data["accounts"][account_number]["status"] == "CLOSED":
                return
        elif choice == "8":
            log_activity("LOGOUT", f"Account {account_number} logged out")
            print("Logged out successfully.")
            return
        else:
            print("Invalid option.")


def main():
    data = load_data()

    while True:
        print("\n========================================")
        print("       SMART BANKING SIMULATOR")
        print("========================================")
        print("1. Create Account")
        print("2. Login")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            create_account(data)
        elif choice == "2":
            account_number = authenticate(data)
            if account_number:
                customer_menu(data, account_number)
        elif choice == "3":
            log_activity("SYSTEM_EXIT", "Banking simulator closed")
            print("Thank you for using Smart Banking Simulator.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
