import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap


def normalize_account_id(user_id):
    """Normalise an account identifier so lookups work consistently."""
    return str(user_id).strip().lower()


def is_valid_amount(amount):
    """Return True when an amount is a positive number."""
    try:
        return float(amount) > 0
    except (TypeError, ValueError):
        return False


def format_inr(amount):
    """Format a numeric amount using the Indian digit grouping convention."""
    whole, fraction = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        last_three = whole[-3:]
        leading = whole[:-3]
        groups = []
        while leading:
            groups.insert(0, leading[-2:])
            leading = leading[:-2]
        whole = ",".join(groups + [last_three])
    return f"₹{whole}.{fraction}"


class User:
    def __init__(self, user_id, pin, balance=0):
        self.user_id = normalize_account_id(user_id)
        self.pin = str(pin).strip()
        self.balance = float(balance)
        self.transactions = []

    def verify_pin(self, pin):
        return self.pin == str(pin).strip()

    def add_transaction(self, type, amount, recipient_id=None):
        transaction = f"{type} of {format_inr(amount)}"
        if recipient_id:
            transaction += f" to {recipient_id}"
        transaction += f". Balance: {format_inr(self.balance)}"
        self.transactions.append(transaction)

    def deposit(self, amount):
        if not is_valid_amount(amount):
            return False
        self.balance += float(amount)
        self.add_transaction("Deposit", amount)
        return True

    def withdraw(self, amount):
        if not is_valid_amount(amount):
            return False
        amount = float(amount)
        if amount > self.balance:
            return False
        self.balance -= amount
        self.add_transaction("Withdraw", amount)
        return True

    def transfer(self, amount, recipient):
        if not is_valid_amount(amount):
            return False
        amount = float(amount)
        if recipient is self or amount > self.balance:
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
        if self.current_user and is_valid_amount(amount):
            return self.current_user.deposit(amount)
        return False

    def withdraw(self, amount):
        if self.current_user and is_valid_amount(amount):
            return self.current_user.withdraw(amount)
        return False

    def transfer(self, recipient_id, amount):
        if self.current_user and is_valid_amount(amount):
            recipient = self.bank.get_user(recipient_id)
            if recipient and recipient is not self.current_user:
                return self.current_user.transfer(amount, recipient)
        return False

    def get_transaction_history(self):
        return self.current_user.get_transaction_history() if self.current_user else None


class Bank:
    def __init__(self):
        self.users = {}

    def add_user(self, user):
        self.users[normalize_account_id(user.user_id)] = user

    def get_user(self, user_id):
        return self.users.get(normalize_account_id(user_id))


class ATMApp(QMainWindow):
    def __init__(self, bank):
        super().__init__()
        self.atm = ATM(bank)
        self.setWindowTitle("Northstar Bank · ATM")
        self.setMinimumSize(1180, 760)
        self.resize(1460, 900)
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
            QFrame#loginPanel { background: #ffffff; border: 1px solid #dce5eb; border-radius: 14px; }
            QLabel#loginHeading { color: #12283d; font-size: 20px; font-weight: 700; }
            QLabel#loginPrompt { color: #64798b; font-size: 12px; }
            QLabel#demoHint { color: #718595; font-size: 11px; font-weight: 700; }
            QLineEdit { background: #f9fbfc; border: 1px solid #cad6df; border-radius: 8px; color: #13283a; padding: 11px 12px; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #24b89a; }
            QPushButton#loginButton { background: #16866e; border: 0; border-radius: 9px; color: white; font-size: 13px; font-weight: 700; padding: 12px; }
            QPushButton#loginButton:hover { background: #11745f; }
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

        self.brand_name = QLabel("NORTHSTAR BANK · INDIA")
        self.brand_name.setObjectName("brandName")
        self.brand_subtitle = QLabel("ATM  •  CASH  •  TRANSFERS")
        self.brand_subtitle.setObjectName("brandSubtitle")

        self.status_label = QLabel("●  CARD READY  ·  SECURE SESSION")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.screen_title = QLabel("Namaste")
        self.screen_title.setObjectName("screenTitle")
        self.account_label = QLabel("INDIA  ·  CUSTOMER LOGIN")
        self.account_label.setObjectName("account")
        self.account_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.label_balance = QLabel("₹0.00")
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

        self.login_panel = QFrame()
        self.login_panel.setObjectName("loginPanel")
        login_layout = QVBoxLayout(self.login_panel)
        login_layout.setContentsMargins(18, 14, 18, 14)
        login_layout.setSpacing(9)
        self.login_heading = QLabel("Welcome to Northstar Bank")
        self.login_heading.setObjectName("loginHeading")
        self.login_prompt = QLabel("Enter your account number and 4-digit PIN to begin.")
        self.login_prompt.setObjectName("loginPrompt")
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("Account number  (demo: user1 or user2)")
        self.account_input.setClearButtonEnabled(True)
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("4-digit ATM PIN")
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(4)
        self.pin_input.returnPressed.connect(self.authenticate_user)
        self.login_button = QPushButton("INSERT CARD  ·  CONTINUE")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.authenticate_user)
        self.demo_hint = QLabel("DEMO  ·  user1 / 1234     user2 / 2345")
        self.demo_hint.setObjectName("demoHint")
        login_layout.addWidget(self.login_heading)
        login_layout.addWidget(self.login_prompt)
        login_layout.addWidget(self.account_input)
        login_layout.addWidget(self.pin_input)
        login_layout.addWidget(self.login_button)
        login_layout.addWidget(self.demo_hint)

        self.machine_visual = QLabel()
        self.machine_visual.setObjectName("machineVisual")
        self.machine_visual.setAlignment(Qt.AlignCenter)
        self.machine_visual.setMinimumWidth(390)
        self.machine_visual.setPixmap(
            QPixmap(str(Path(__file__).parent / "assets" / "india-atm-machine.png")).scaled(
                610, 790, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

        self.button_logout = QPushButton("END SESSION")
        self.button_logout.setObjectName("logoutButton")
        self.button_logout.clicked.connect(self.logout)

        self.text_transaction_history = QTextEdit(self)
        self.text_transaction_history.setObjectName("history")
        self.text_transaction_history.setReadOnly(True)
        self.text_transaction_history.setMinimumHeight(112)

        self.footer_label = QLabel("Please take your card, cash and receipt before leaving.")
        self.footer_label.setObjectName("footer")

    def create_layouts(self):
        root = QHBoxLayout(self.central_widget)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(20)

        machine_art = QVBoxLayout()
        machine_art.setSpacing(8)
        art_caption = QLabel("SELF-SERVICE BANKING")
        art_caption.setStyleSheet("color:#9fb1c2;font-size:10px;font-weight:700;letter-spacing:2px;padding-left:8px;")
        machine_art.addWidget(art_caption)
        machine_art.addWidget(self.machine_visual, 1)
        art_footer = QLabel("NORTHSTAR  ·  INDIA")
        art_footer.setStyleSheet("color:#9fb1c2;font-size:10px;font-weight:700;letter-spacing:2px;padding-left:8px;")
        machine_art.addWidget(art_footer)
        root.addLayout(machine_art, 5)

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
        screen_layout.addWidget(self.login_panel)

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

        self.actions_panel = QWidget()
        self.actions_panel.setStyleSheet("background:transparent;")
        actions = QHBoxLayout(self.actions_panel)
        actions.setSpacing(10)
        actions.addWidget(self.button_withdraw)
        actions.addWidget(self.button_deposit)
        actions.addWidget(self.button_transfer)
        screen_layout.addWidget(self.actions_panel)

        history_heading = QLabel("RECENT ACCOUNT ACTIVITY")
        history_heading.setObjectName("sectionTitle")
        screen_layout.addWidget(history_heading)
        screen_layout.addWidget(self.text_transaction_history)

        self.balance_card = balance_card
        self.action_heading = action_heading
        self.history_heading = history_heading

        shell.addWidget(screen, 1)

        footer = QHBoxLayout()
        footer.addWidget(self.footer_label)
        footer.addStretch(1)
        footer.addWidget(self.button_logout)
        shell.addLayout(footer)

        root.addWidget(machine, 7)

    def authenticate_user(self):
        user_id = self.account_input.text().strip()
        pin = self.pin_input.text()
        if self.atm.authenticate_user(user_id, pin):
            self.screen_title.setText("Namaste")
            self.account_label.setText(f"ACCOUNT  ·  {user_id.upper()}")
            self.status_label.setText("●  SESSION ACTIVE")
            self.set_session_controls(True)
            self.pin_input.clear()
            self.update_balance_label()
            self.show_transaction_history()
            return True
        QMessageBox.warning(self, "Card verification failed", "The account number or PIN was not recognised.")
        return False

    def update_balance_label(self):
        self.label_balance.setText(format_inr(self.atm.show_balance()))

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
            if not is_valid_amount(amount):
                QMessageBox.warning(self, "Withdrawal declined", "Please enter a positive amount.")
                return
            if self.atm.withdraw(amount):
                QMessageBox.information(self, "Withdrawal complete", f"{format_inr(amount)} withdrawal approved.")
                self.update_balance_label()
                self.show_transaction_history()
            else:
                QMessageBox.warning(self, "Withdrawal declined", "Insufficient funds or no active session.")

    def deposit_dialog(self):
        amount, ok = QInputDialog.getDouble(self, "Cash deposit", "Enter amount to deposit:", decimals=2)
        if ok:
            if not is_valid_amount(amount):
                QMessageBox.warning(self, "Deposit unavailable", "Please enter a positive amount.")
                return
            if self.atm.deposit(amount):
                QMessageBox.information(self, "Deposit complete", f"{format_inr(amount)} deposited.")
                self.update_balance_label()
                self.show_transaction_history()
            else:
                QMessageBox.warning(self, "Deposit unavailable", "Please sign in before making a deposit.")

    def transfer_dialog(self):
        recipient_id, ok = QInputDialog.getText(self, "Funds transfer", "Enter recipient account ID:")
        if ok:
            recipient_id = recipient_id.strip()
            if not recipient_id:
                QMessageBox.warning(self, "Transfer declined", "Please provide a valid recipient account number.")
                return
            amount, ok = QInputDialog.getDouble(self, "Funds transfer", "Enter amount to transfer:", decimals=2)
            if ok:
                if not is_valid_amount(amount):
                    QMessageBox.warning(self, "Transfer declined", "Please enter a positive amount.")
                    return
                if self.atm.transfer(recipient_id, amount):
                    QMessageBox.information(self, "Transfer complete", f"{format_inr(amount)} transferred to {recipient_id}.")
                    self.update_balance_label()
                    self.show_transaction_history()
                else:
                    QMessageBox.warning(self, "Transfer declined", "Please check the recipient, balance, and session.")

    def logout(self):
        self.atm.logout()
        self.label_balance.setText("₹0.00")
        self.account_label.setText("INDIA  ·  CUSTOMER LOGIN")
        self.screen_title.setText("Namaste")
        self.status_label.setText("●  CARD READY  ·  SECURE SESSION")
        self.account_input.clear()
        self.pin_input.clear()
        self.text_transaction_history.clear()
        self.set_session_controls(False)

    def set_session_controls(self, enabled):
        self.button_withdraw.setEnabled(enabled)
        self.button_deposit.setEnabled(enabled)
        self.button_transfer.setEnabled(enabled)
        self.button_logout.setEnabled(enabled)
        self.login_panel.setVisible(not enabled)
        self.balance_card.setVisible(enabled)
        self.action_heading.setVisible(enabled)
        self.actions_panel.setVisible(enabled)
        self.history_heading.setVisible(enabled)
        self.text_transaction_history.setVisible(enabled)

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
    sys.exit(app.exec_())

