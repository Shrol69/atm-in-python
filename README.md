# ATM Console Application

This is a simple console-based ATM application implemented in Python. The application allows users to perform basic banking operations such as viewing transaction history, withdrawing funds, depositing funds, and transferring funds to other users. The application includes user authentication through user ID and PIN.

## Features

- User authentication with user ID and PIN
- View transaction history
- Withdraw funds
- Deposit funds
- Transfer funds to other users
- Logout and exit the application

## Class Design

### User

Manages user details, including their balance and transaction history.

### ATM

Handles user authentication and manages ATM functionalities such as showing balance, deposit, withdraw, transfer, and transaction history.

### Bank

Manages multiple users and provides a method to retrieve user details.

### ATMApp

Handles the user interface and interaction, providing a menu for different ATM operations.

## How to Run

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/atm-console-app.git
    cd atm-console-app
    ```

2. Run the application:
    ```bash
    python atm_app.py
    ```

## Example Usage

```python
if __name__ == "__main__":
    # Create a bank and add some users
    bank = Bank()
    bank.add_user(User("user1", "1234", 1000))
    bank.add_user(User("user2", "2345", 2000))

    # Create and run the ATM application
    atm_app = ATMApp(bank)
    atm_app.run()
