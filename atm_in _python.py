import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox, QInputDialog, QSizePolicy, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from functools import partial

class User:
    def __init__(self, user_id, pin, balance=0):
        self.user_id = user_id
        self.pin = pin
        self.balance = balance
        self.transactions = []

    def verify_pin(self, pin):
        return self.pin == pin

    def add_transaction(self, type, amount, recipient_id=None):
        transaction = f"{type} of ${amount:.2f}"
        if recipient_id:
            transaction += f" to {recipient_id}"
        transaction += f". Balance: ${self.balance:.2f}"
        self.transactions.append(transaction)

    def deposit(self, amount):
        self.balance += amount
        self.add_transaction("Deposit", amount)

    def withdraw(self, amount):
        if amount > self.balance:
            return False
        self.balance -= amount
        self.add_transaction("Withdraw", amount)
        return True

    def transfer(self, amount, recipient):
        if amount > self.balance:
            return False
        self.balance -= amount
        recipient.deposit(amount)
        self.add_transaction("Transfer", amount, recipient.user_id)
        return True

    def get_transaction_history(self):
        return self.transactions


class ATM:
    def __init__(self, bank):
        self.bank = bank
        self.current_user = None

    def authenticate_user(self, user_id, pin):
        user = self.bank.get_user(user_id)
        if user and user.verify_pin(pin):
            self.current_user = user
            return True
        return False

    def logout(self):
        self.current_user = None

    def show_balance(self):
        return self.current_user.balance if self.current_user else 0

    def deposit(self, amount):
        if self.current_user:
            self.current_user.deposit(amount)
            return True
        return False

    def withdraw(self, amount):
        if self.current_user:
            return self.current_user.withdraw(amount)
        return False

    def transfer(self, recipient_id, amount):
        if self.current_user:
            recipient = self.bank.get_user(recipient_id)
            if recipient:
                return self.current_user.transfer(amount, recipient)
        return False

    def get_transaction_history(self):
        return self.current_user.get_transaction_history() if self.current_user else None


class Bank:
    def __init__(self):
        self.users = {}

    def add_user(self, user):
        self.users[user.user_id] = user

    def get_user(self, user_id):
        return self.users.get(user_id)


class ATMApp(QMainWindow):
    def __init__(self, bank):
        super().__init__()
        self.atm = ATM(bank)
        self.setWindowTitle("ATM Application")
        self.setWindowIcon(QIcon('atm_icon.png'))  # Replace with your icon file
        self.setGeometry(100, 100, 600, 500)
        self.initUI()

    def initUI(self):
        self.create_widgets()
        self.create_layouts()

    def create_widgets(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.label_balance = QLabel("Balance: $0.00", self)
        self.label_balance.setFont(QFont('Arial', 14))

        self.button_withdraw = QPushButton("Withdraw", self)
        self.button_withdraw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button_withdraw.clicked.connect(self.withdraw_dialog)

        self.button_deposit = QPushButton("Deposit", self)
        self.button_deposit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button_deposit.clicked.connect(self.deposit_dialog)

        self.button_transfer = QPushButton("Transfer", self)
        self.button_transfer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button_transfer.clicked.connect(self.transfer_dialog)

        self.button_logout = QPushButton("Logout", self)
        self.button_logout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button_logout.clicked.connect(self.logout)

        self.text_transaction_history = QTextEdit(self)
        self.text_transaction_history.setReadOnly(True)

    def create_layouts(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.label_balance)
        vbox.addWidget(self.button_withdraw)
        vbox.addWidget(self.button_deposit)
        vbox.addWidget(self.button_transfer)
        vbox.addWidget(self.button_logout)
        vbox.addWidget(self.text_transaction_history)

        self.central_widget.setLayout(vbox)

    def authenticate_user(self):
        user_id, ok = QInputDialog.getText(self, "Login", "Enter User ID:")
        if ok:
            pin, ok = QInputDialog.getText(self, "Login", "Enter PIN:", QLineEdit.Password)
            if ok:
                if self.atm.authenticate_user(user_id, pin):
                    self.update_balance_label()
                    self.show_transaction_history()
                    return True
                else:
                    QMessageBox.warning(self, "Authentication Failed", "Invalid User ID or PIN")
        return False

    def update_balance_label(self):
        balance = self.atm.show_balance()
        self.label_balance.setText(f"Balance: ${balance:.2f}")

    def show_transaction_history(self):
        self.text_transaction_history.clear()
        transactions = self.atm.get_transaction_history()
        if transactions:
            for transaction in transactions:
                self.text_transaction_history.append(transaction)
        else:
            self.text_transaction_history.append("No transactions found.")

    def withdraw_dialog(self):
        amount, ok = QInputDialog.getDouble(self, "Withdraw", "Enter amount to withdraw:", decimals=2)
        if ok:
            if self.atm.withdraw(amount):
                QMessageBox.information(self, "Withdrawal", f"Withdrawal of ${amount:.2f} successful")
                self.update_balance_label()
                self.show_transaction_history()
            else:
                QMessageBox.warning(self, "Withdrawal Failed", "Insufficient funds")

    def deposit_dialog(self):
        amount, ok = QInputDialog.getDouble(self, "Deposit", "Enter amount to deposit:", decimals=2)
        if ok:
            self.atm.deposit(amount)
            QMessageBox.information(self, "Deposit", f"Deposit of ${amount:.2f} successful")
            self.update_balance_label()
            self.show_transaction_history()

    def transfer_dialog(self):
        recipient_id, ok = QInputDialog.getText(self, "Transfer", "Enter recipient User ID:")
        if ok:
            amount, ok = QInputDialog.getDouble(self, "Transfer", "Enter amount to transfer:", decimals=2)
            if ok:
                if self.atm.transfer(recipient_id, amount):
                    QMessageBox.information(self, "Transfer", f"Transfer of ${amount:.2f} to {recipient_id} successful")
                    self.update_balance_label()
                    self.show_transaction_history()
                else:
                    QMessageBox.warning(self, "Transfer Failed", "Transfer failed. Please check details.")

    def logout(self):
        self.atm.logout()
        self.label_balance.setText("Balance: $0.00")
        self.text_transaction_history.clear()
        self.authenticate_user()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit Application', 'Are you sure you want to exit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bank = Bank()
    bank.add_user(User("user1", "1234", 1000))
    bank.add_user(User("user2", "2345", 2000))
    atm_app = ATMApp(bank)
    atm_app.show()
    if not atm_app.authenticate_user():
        sys.exit()
    sys.exit(app.exec_())
