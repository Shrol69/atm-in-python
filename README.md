# Northstar Bank ATM

A desktop ATM simulator built with Python and PyQt5. The application supports demo account sign-in, balance viewing, cash deposits and withdrawals, transfers between accounts, transaction history, and session logout.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python "atm_in _python.py"
```

## Demo accounts

- Account ID: `user1` · PIN: `1234` · Starting balance: `$1,000`
- Account ID: `user2` · PIN: `2345` · Starting balance: `$2,000`

This is an in-memory learning demo. Account data and transactions reset when the program closes; do not use real account details or money.
