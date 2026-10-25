import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMessageBox, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
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
        self.setWindowTitle("Northstar Bank · ATM")
        self.setMinimumSize(780, 640)
        self.resize(940, 740)
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QMainWindow { background: #0b1420; }
            QWidget { font-family: "Arial"; color: #192b3c; }
            QFrame#machine { background: #152333; border: 1px solid #263b50; border-radius: 24px; }
            QLabel#brandMark { background: #24b89a; color: #08251f; border-radius: 13px; font-size: 22px; font-weight: 800; }
            QLabel#brandName { color: #f2f7fb; font-size: 17px; font-weight: 700; letter-spacing: 1px; }
            QLabel#brandSubtitle { color: #9fb1c2; font-size: 10px; letter-spacing: 2px; }
            QLabel#status { color: #92e5cd; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QFrame#screen { background: #f3f7fa; border: 1px solid #dce5eb; border-radius: 18px; }
            QLabel#screenTitle { color: #12283d; font-size: 22px; font-weight: 700; }
            QLabel#account { color: #64798b; font-size: 11px; font-weight: 700; }
            QFrame#balanceCard { background: #102d46; border-radius: 14px; }
            QLabel#balanceCaption { color: #a9c0d2; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QLabel#balanceValue { color: #ffffff; font-size: 32px; font-weight: 700; }
            QLabel#sectionTitle { color: #526a7c; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QPushButton#withdrawButton, QPushButton#depositButton, QPushButton#transferButton {
                background: #ffffff; border: 1px solid #d6e0e7; border-radius: 12px;
                color: #17324a; font-size: 13px; font-weight: 700; padding: 16px 10px;
                min-height: 62px;
            }
            QPushButton#withdrawButton:hover, QPushButton#depositButton:hover, QPushButton#transferButton:hover {
                background: #e8f5f2; border: 1px solid #24b89a;
            }
            QPushButton#withdrawButton:pressed, QPushButton#depositButton:pressed, QPushButton#transferButton:pressed {
                background: #d5eee8;
            }
            QTextEdit#history { background: #ffffff; border: 1px solid #dce5eb; border-radius: 10px; padding: 8px; color: #344c60; font-size: 12px; }
            QPushButton#logoutButton { background: transparent; border: 1px solid #52677a; border-radius: 9px; color: #d9e3eb; padding: 9px 18px; font-weight: 700; }
            QPushButton#logoutButton:hover { background: #263b50; }
            QLabel#footer { color: #91a4b5; font-size: 10px; }
        """)
        self.create_widgets()
        self.create_layouts()
        self.set_session_controls(False)

    def create_widgets(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.brand_mark = QLabel("N")
        self.brand_mark.setObjectName("brandMark")
        self.brand_mark.setAlignment(Qt.AlignCenter)
        self.brand_mark.setFixedSize(46, 46)

        self.brand_name = QLabel("NORTHSTAR BANK")
        self.brand_name.setObjectName("brandName")
        self.brand_subtitle = QLabel("SELF SERVICE BANKING")
        self.brand_subtitle.setObjectName("brandSubtitle")

        self.status_label = QLabel("●  INSERT CARD TO BEGIN")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.screen_title = QLabel("Welcome")
        self.screen_title.setObjectName("screenTitle")
        self.account_label = QLabel("ACCOUNT  ·  SIGN IN")
        self.account_label.setObjectName("account")
        self.account_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.label_balance = QLabel("$0.00")
        self.label_balance.setObjectName("balanceValue")
        self.label_balance.setFont(QFont("Arial", 32, QFont.Bold))

        self.button_withdraw = QPushButton("−    WITHDRAW CASH")
        self.button_withdraw.setObjectName("withdrawButton")
        self.button_withdraw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_withdraw.clicked.connect(self.withdraw_dialog)

        self.button_deposit = QPushButton("+    DEPOSIT FUNDS")
        self.button_deposit.setObjectName("depositButton")
        self.button_deposit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_deposit.clicked.connect(self.deposit_dialog)

        self.button_transfer = QPushButton("↗    TRANSFER")
        self.button_transfer.setObjectName("transferButton")
        self.button_transfer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_transfer.clicked.connect(self.transfer_dialog)

        self.button_logout = QPushButton("END SESSION")
        self.button_logout.setObjectName("logoutButton")
        self.button_logout.clicked.connect(self.logout)

        self.text_transaction_history = QTextEdit(self)
        self.text_transaction_history.setObjectName("history")
        self.text_transaction_history.setReadOnly(True)
        self.text_transaction_history.setMinimumHeight(112)

        self.footer_label = QLabel("Please take your cash and any personal belongings before leaving.")
        self.footer_label.setObjectName("footer")

    def create_layouts(self):
        root = QVBoxLayout(self.central_widget)
        root.setContentsMargins(24, 22, 24, 22)

        machine = QFrame()
        machine.setObjectName("machine")
        shell = QVBoxLayout(machine)
        shell.setContentsMargins(22, 20, 22, 20)
        shell.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(self.brand_mark)
        brand_copy = QVBoxLayout()
        brand_copy.setSpacing(3)
        brand_copy.addWidget(self.brand_name)
        brand_copy.addWidget(self.brand_subtitle)
        header.addLayout(brand_copy)
        header.addStretch(1)
        header.addWidget(self.status_label)
        shell.addLayout(header)

        screen = QFrame()
        screen.setObjectName("screen")
        screen_layout = QVBoxLayout(screen)
        screen_layout.setContentsMargins(22, 20, 22, 20)
        screen_layout.setSpacing(14)

        greeting = QHBoxLayout()
        greeting.addWidget(self.screen_title)
        greeting.addStretch(1)
        greeting.addWidget(self.account_label)
        screen_layout.addLayout(greeting)

        balance_card = QFrame()
        balance_card.setObjectName("balanceCard")
        balance_layout = QVBoxLayout(balance_card)
        balance_layout.setContentsMargins(18, 14, 18, 14)
        balance_layout.setSpacing(6)
        caption = QLabel("AVAILABLE BALANCE")
        caption.setObjectName("balanceCaption")
        balance_layout.addWidget(caption)
        balance_layout.addWidget(self.label_balance)
        screen_layout.addWidget(balance_card)

        action_heading = QLabel("SELECT A TRANSACTION")
        action_heading.setObjectName("sectionTitle")
        screen_layout.addWidget(action_heading)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.button_withdraw)
        actions.addWidget(self.button_deposit)
        actions.addWidget(self.button_transfer)
        screen_layout.addLayout(actions)

        history_heading = QLabel("RECENT ACCOUNT ACTIVITY")
        history_heading.setObjectName("sectionTitle")
        screen_layout.addWidget(history_heading)
        screen_layout.addWidget(self.text_transaction_history)

        shell.addWidget(screen, 1)

        footer = QHBoxLayout()
        footer.addWidget(self.footer_label)
        footer.addStretch(1)
        footer.addWidget(self.button_logout)
        shell.addLayout(footer)

        root.addWidget(machine)

    def authenticate_user(self):
        user_id, ok = QInputDialog.getText(self, "Cardholder Verification", "Enter your account ID:")
        if ok:
            pin, ok = QInputDialog.getText(self, "Cardholder Verification", "Enter your PIN:", QLineEdit.Password)
            if ok:
                if self.atm.authenticate_user(user_id, pin):
                    self.screen_title.setText("Good day")
                    self.account_label.setText(f"ACCOUNT  ·  {user_id.upper()}")
                    self.status_label.setText("●  SESSION ACTIVE")
                    self.set_session_controls(True)
                    self.update_balance_label()
                    self.show_transaction_history()
                    return True
                QMessageBox.warning(self, "Access not approved", "The account ID or PIN was not recognised.")
        return False

    def update_balance_label(self):
        self.label_balance.setText(f"${self.atm.show_balance():,.2f}")

    def show_transaction_history(self):
        self.text_transaction_history.clear()
        transactions = self.atm.get_transaction_history()
        if transactions:
            for transaction in transactions:
                self.text_transaction_history.append(transaction)
        else:
            self.text_transaction_history.append("No recent transactions.")

    def withdraw_dialog(self):
        amount, ok = QInputDialog.getDouble(self, "Cash withdrawal", "Enter amount to withdraw:", decimals=2)
        if ok:
            if self.atm.withdraw(amount):
                QMessageBox.information(self, "Withdrawal complete", f"${amount:,.2f} withdrawal approved.")
                self.update_balance_label()
                self.show_transaction_history()
            else:
                QMessageBox.warning(self, "Withdrawal declined", "Insufficient funds or no active session.")

    def deposit_dialog(self):
        amount, ok = QInputDialog.getDouble(self, "Cash deposit", "Enter amount to deposit:", decimals=2)
        if ok:
            if self.atm.deposit(amount):
                QMessageBox.information(self, "Deposit complete", f"${amount:,.2f} deposited.")
                self.update_balance_label()
                self.show_transaction_history()
            else:
                QMessageBox.warning(self, "Deposit unavailable", "Please sign in before making a deposit.")

    def transfer_dialog(self):
        recipient_id, ok = QInputDialog.getText(self, "Funds transfer", "Enter recipient account ID:")
        if ok:
            amount, ok = QInputDialog.getDouble(self, "Funds transfer", "Enter amount to transfer:", decimals=2)
            if ok:
                if self.atm.transfer(recipient_id, amount):
                    QMessageBox.information(self, "Transfer complete", f"${amount:,.2f} transferred to {recipient_id}.")
                    self.update_balance_label()
                    self.show_transaction_history()
                else:
                    QMessageBox.warning(self, "Transfer declined", "Please check the recipient, balance, and session.")

    def logout(self):
        self.atm.logout()
        self.label_balance.setText("$0.00")
        self.account_label.setText("ACCOUNT  ·  SIGN IN")
        self.screen_title.setText("Welcome")
        self.status_label.setText("●  INSERT CARD TO BEGIN")
        self.text_transaction_history.clear()
        self.set_session_controls(False)
        self.authenticate_user()

    def set_session_controls(self, enabled):
        self.button_withdraw.setEnabled(enabled)
        self.button_deposit.setEnabled(enabled)
        self.button_transfer.setEnabled(enabled)
        self.button_logout.setEnabled(enabled)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "End session", "Are you sure you want to close the ATM?",
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

