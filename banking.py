import json
import os
from datetime import datetime
import hashlib


class BankAccount:
    def __init__(self, account_number, name, pin, balance=0):
        self.account_number = account_number
        self.name = name
        self.pin_hash = self.hash_pin(pin)
        self.balance = balance
        self.transactions = []

    @staticmethod
    def hash_pin(pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    def verify_pin(self, pin):
        return self.pin_hash == self.hash_pin(pin)

    def add_transaction(self, transaction_type, amount, details=""):
        transaction = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": transaction_type,
            "amount": amount,
            "balance_after": self.balance,
            "details": details
        }
        self.transactions.append(transaction)

    def deposit(self, amount):
        if amount <= 0:
            print("Amount must be greater than 0.")
            return False
        self.balance += amount
        self.add_transaction("DEPOSIT", amount, "Cash deposited")
        print(f"₹{amount:.2f} deposited successfully.")
        print(f"New balance: ₹{self.balance:.2f}")
        return True

    def withdraw(self, amount):
        if amount <= 0:
            print("Amount must be greater than 0.")
            return False
        if amount > self.balance:
            print("Insufficient balance.")
            return False
        self.balance -= amount
        self.add_transaction("WITHDRAW", amount, "Cash withdrawn")
        print(f"₹{amount:.2f} withdrawn successfully.")
        print(f"New balance: ₹{self.balance:.2f}")
        return True

    def show_transactions(self):
        if not self.transactions:
            print("\nNo transactions found.")
            return
        print("\n========== TRANSACTION HISTORY ==========")
        for t in self.transactions:
            print(
                f"{t['timestamp']} | {t['type']} | "
                f"₹{t['amount']:.2f} | "
                f"Balance: ₹{t['balance_after']:.2f} | {t['details']}"
            )


class Bank:
    def __init__(self):
        self.accounts = {}
        self.accounts_file = "accounts.json"
        self.log_file = "bank_activity.log"
        self.load_accounts()

    def log_activity(self, action, account_number=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(
                f"[{timestamp}] ACTION={action} ACCOUNT={account_number}\n"
            )

    def generate_account_number(self):
        if not self.accounts:
            return "100001"
        numbers = [int(n) for n in self.accounts]
        return str(max(numbers) + 1)

    def create_account(self):
        print("\n========== CREATE ACCOUNT ==========")
        name = input("Enter customer name: ").strip()

        while True:
            pin = input("Create 4-digit PIN: ")
            if len(pin) == 4 and pin.isdigit():
                break
            print("PIN must contain exactly 4 digits.")

        account_number = self.generate_account_number()
        self.accounts[account_number] = BankAccount(
            account_number, name, pin
        )
        self.save_accounts()
        self.log_activity("ACCOUNT_CREATED", account_number)

        print("\nAccount created successfully!")
        print(f"Customer: {name}")
        print(f"Account Number: {account_number}")

    def login(self):
        print("\n========== LOGIN ==========")
        account_number = input("Enter account number: ")
        pin = input("Enter PIN: ")

        if account_number not in self.accounts:
            print("Account not found.")
            return None

        account = self.accounts[account_number]
        if not account.verify_pin(pin):
            print("Incorrect PIN.")
            self.log_activity("FAILED_LOGIN", account_number)
            return None

        print(f"\nWelcome, {account.name}!")
        self.log_activity("LOGIN_SUCCESS", account_number)
        return account

    def transfer(self, sender):
        print("\n========== TRANSFER MONEY ==========")
        receiver_number = input("Enter receiver account number: ")

        if receiver_number not in self.accounts:
            print("Receiver account not found.")
            return

        if receiver_number == sender.account_number:
            print("You cannot transfer money to yourself.")
            return

        try:
            amount = float(input("Enter amount: ₹"))
        except ValueError:
            print("Please enter a valid amount.")
            return

        if amount <= 0:
            print("Amount must be greater than 0.")
            return
        if amount > sender.balance:
            print("Insufficient balance.")
            return

        receiver = self.accounts[receiver_number]
        sender.balance -= amount
        sender.add_transaction(
            "TRANSFER_OUT", amount,
            f"Transferred to {receiver.account_number}"
        )

        receiver.balance += amount
        receiver.add_transaction(
            "TRANSFER_IN", amount,
            f"Received from {sender.account_number}"
        )

        self.save_accounts()
        self.log_activity(
            f"TRANSFER ₹{amount:.2f} TO {receiver.account_number}",
            sender.account_number
        )

        print("\nTransfer successful!")
        print(f"Amount: ₹{amount:.2f}")
        print(f"To: {receiver.name}")
        print(f"Your balance: ₹{sender.balance:.2f}")

    def save_accounts(self):
        data = {}
        for number, account in self.accounts.items():
            data[number] = {
                "name": account.name,
                "pin_hash": account.pin_hash,
                "balance": account.balance,
                "transactions": account.transactions
            }

        with open(self.accounts_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load_accounts(self):
        if not os.path.exists(self.accounts_file):
            return

        try:
            with open(self.accounts_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            for number, details in data.items():
                account = BankAccount(number, details["name"], "0000")
                account.pin_hash = details["pin_hash"]
                account.balance = details["balance"]
                account.transactions = details["transactions"]
                self.accounts[number] = account
        except (json.JSONDecodeError, KeyError):
            print("Error loading account data.")


def customer_menu(bank, account):
    while True:
        print("\n====================================")
        print("          CUSTOMER DASHBOARD")
        print("====================================")
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transfer Money")
        print("5. Transaction History")
        print("6. Logout")
        print("====================================")

        choice = input("Enter choice: ")

        if choice == "1":
            print(f"\nCurrent Balance: ₹{account.balance:.2f}")

        elif choice == "2":
            try:
                amount = float(input("Enter deposit amount: ₹"))
                if account.deposit(amount):
                    bank.save_accounts()
                    bank.log_activity(
                        f"DEPOSIT ₹{amount:.2f}", account.account_number
                    )
            except ValueError:
                print("Please enter a valid amount.")

        elif choice == "3":
            try:
                amount = float(input("Enter withdrawal amount: ₹"))
                if account.withdraw(amount):
                    bank.save_accounts()
                    bank.log_activity(
                        f"WITHDRAW ₹{amount:.2f}", account.account_number
                    )
            except ValueError:
                print("Please enter a valid amount.")

        elif choice == "4":
            bank.transfer(account)

        elif choice == "5":
            account.show_transactions()

        elif choice == "6":
            bank.log_activity("LOGOUT", account.account_number)
            print("Logged out successfully.")
            break

        else:
            print("Invalid choice. Try again.")


def main():
    bank = Bank()

    while True:
        print("\n====================================")
        print("       SMART BANKING SIMULATOR")
        print("====================================")
        print("1. Create Account")
        print("2. Login")
        print("3. Exit")
        print("====================================")

        choice = input("Enter choice: ")

        if choice == "1":
            bank.create_account()
        elif choice == "2":
            account = bank.login()
            if account:
                customer_menu(bank, account)
        elif choice == "3":
            print("\nThank you for using Smart Banking Simulator!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
