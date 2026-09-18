# Smart Banking Simulator

A Python-based banking simulation system with account creation, PIN authentication, deposits, withdrawals, fund transfers, transaction history, account management, persistent data storage, and activity logging.

## Features

- Create bank accounts
- Generate unique account numbers
- 4-digit PIN authentication
- PIN hashing
- Deposit money
- Withdraw money
- Transfer money between accounts
- Balance validation
- Transaction IDs
- Complete transaction history
- Change PIN
- Close account when balance is zero
- Persistent JSON database
- Secure activity log
- Login and logout logging
- Input validation

## Run

```bash
python banking_simulator.py
```

The application automatically creates:

- `bank_data.json` for account and transaction data
- `bank_activity.log` for banking activity logs

## Project Structure

```text
smart_banking_simulator/
├── banking_simulator.py
├── README.md
├── bank_data.json
└── bank_activity.log
```

`bank_data.json` and `bank_activity.log` are generated automatically after the first run.
