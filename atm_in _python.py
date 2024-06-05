class User:
    def __init__(self, user_id, pin, balance=0):
        self.user_id = user_id
        self.pin = pin
        self.balance = balance
        self.transactions = []

    def verify_pin(self, pin):
        return self.pin == pin

    def add_transaction(self, type, amount, recipient_id=None):
        transaction = f"{type} of {amount}"
        if recipient_id:
            transaction += f" to {recipient_id}"
        transaction += f". Balance: {self.balance}"
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
        return self.current_user.balance if self.current_user else None

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


class ATMApp:
    def __init__(self, bank):
        self.atm = ATM(bank)

    def run(self):
        while True:
            print("Welcome to the ATM")
            user_id = input("Enter your user ID: ")
            pin = input("Enter your PIN: ")
            if self.atm.authenticate_user(user_id, pin):
                print("Authentication successful")
                while True:
                    print("\nATM Menu:")
                    print("1. Transaction History")
                    print("2. Withdraw")
                    print("3. Deposit")
                    print("4. Transfer")
                    print("5. Quit")
                    choice = input("Choose an option: ")
                    if choice == '1':
                        self.show_transaction_history()
                    elif choice == '2':
                        self.withdraw()
                    elif choice == '3':
                        self.deposit()
                    elif choice == '4':
                        self.transfer()
                    elif choice == '5':
                        self.quit()
                        break
                    else:
                        print("Invalid choice. Please try again.")
            else:
                print("Authentication failed. Please try again.")

    def show_transaction_history(self):
        transactions = self.atm.get_transaction_history()
        if transactions:
            print("Transaction History:")
            for transaction in transactions:
                print(transaction)
        else:
            print("No transactions found.")

    def withdraw(self):
        amount = float(input("Enter amount to withdraw: "))
        if self.atm.withdraw(amount):
            print("Withdrawal successful.")
        else:
            print("Insufficient funds.")

    def deposit(self):
        amount = float(input("Enter amount to deposit: "))
        if self.atm.deposit(amount):
            print("Deposit successful.")

    def transfer(self):
        recipient_id = input("Enter recipient user ID: ")
        amount = float(input("Enter amount to transfer: "))
        if self.atm.transfer(recipient_id, amount):
            print("Transfer successful.")
        else:
            print("Transfer failed. Please check the details and try again.")

    def quit(self):
        self.atm.logout()
        print("Logged out. Thank you for using the ATM.")
        exit()


# Example U
if __name__ == "__main__":
    bank = Bank()
    bank.add_user(User("user1", "1234", 1000))
    bank.add_user(User("user2", "2345", 2000))
    atm_app = ATMApp(bank)
    atm_app.run()
