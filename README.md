# Northstar Bank ATM Demo

A small desktop ATM simulation built with Python and PyQt5. It provides demo sign-in, balance display, deposits, withdrawals, transfers, and a recent activity list.

## Requirements

- Python 3.9 or later
- macOS, Windows, or Linux with a desktop session available

## Run on macOS or Linux

From this project folder, create and activate a virtual environment, install the GUI dependency, and start the app:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python "atm_in _python.py"
```

## Run on Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python "atm_in _python.py"
```

The app opens a sign-in prompt when it starts. Use either demo account:

| Account ID | PIN | Starting balance |
| --- | --- | ---: |
| `user1` | `1234` | $1,000.00 |
| `user2` | `2345` | $2,000.00 |

This is a learning demo. Account data is kept in memory and resets when the app closes; the demo PINs are stored in the source code. Do not use it for real banking or real financial information.
