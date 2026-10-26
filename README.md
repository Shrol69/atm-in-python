# Northstar Smart ATM

A native PyQt desktop ATM simulator inspired by Indian self-service banking. The interface pairs a 3D ATM render with a bilingual English/Hindi kiosk, Indian rupee formatting, masked PIN entry, quick cash presets with a dispense sequence, deposits, transfers, PIN changes, and a mini statement.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python "atm_in _python.py"
```

## Demo accounts

- Account `user1` · PIN `1234` · balance `₹1,000`
- Account `user2` · PIN `2345` · balance `₹2,000`

Use **EN / हिन्दी** at the top to switch languages. Quick cash offers ₹500, ₹1,000, ₹2,000, and ₹5,000; available choices depend on the account balance. Custom cash withdrawals use ₹100 increments.

This is an in-memory learning simulation. Accounts and transactions reset when the app closes. It does not connect to a bank or handle real money.
