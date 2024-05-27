import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QListWidget, QListWidgetItem, QMessageBox, QComboBox, QInputDialog, QHBoxLayout, QDateEdit)
from PyQt5.QtCore import QDate
from firebase_config import db, auth
from qt_material import apply_stylesheet

class ExpenseTrackerApp(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle('Expense Tracker')
        self.setGeometry(100, 100, 480, 600)

        self.expense_list = QListWidget()
        self.expense_list.itemClicked.connect(self.load_selected_expense)

        self.expense_label = QLabel('Title:')
        self.expense_input = QLineEdit()

        self.amount_label = QLabel('Amount:')
        self.amount_input = QLineEdit()

        self.date_label = QLabel('Date:')
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.category_label = QLabel('Category:')
        self.category_dropdown = QComboBox()
        self.filter_category_dropdown = QComboBox()
        self.filter_category_dropdown.addItem("All Categories")
        self.filter_category_dropdown.currentIndexChanged.connect(self.filter_expenses)

        self.load_categories()

        self.add_category_button = QPushButton('Add Category')
        self.add_category_button.clicked.connect(self.add_category)

        self.add_button = QPushButton('Add Expense')
        self.add_button.clicked.connect(self.add_expense)

        self.edit_button = QPushButton('Edit Expense')
        self.edit_button.clicked.connect(self.edit_expense)
        self.edit_button.setEnabled(False)

        self.delete_button = QPushButton('Delete Expense')
        self.delete_button.clicked.connect(self.delete_expense)
        self.delete_button.setEnabled(False)

        self.total_label = QLabel('Total Expenses: $0.00')

        form_layout = QVBoxLayout()
        form_layout.addWidget(self.expense_label)
        form_layout.addWidget(self.expense_input)
        form_layout.addWidget(self.amount_label)
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(self.date_label)
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(self.category_label)
        form_layout.addWidget(self.category_dropdown)
        form_layout.addWidget(self.add_category_button)
        form_layout.addWidget(self.add_button)
        form_layout.addWidget(self.edit_button)
        form_layout.addWidget(self.delete_button)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        filter_layout.addWidget(self.filter_category_dropdown)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.expense_list)
        layout.addWidget(self.total_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.selected_expense_id = None
        self.load_expenses()

    def load_categories(self):
        self.category_dropdown.clear()
        categories = db.child(f"users/{self.user_id}/categories").get()
        if categories.each():
            for category in categories.each():
                self.category_dropdown.addItem(category.val())
                self.filter_category_dropdown.addItem(category.val())
        else:
            self.category_dropdown.addItem("Miscellaneous")

    def add_category(self):
        category, ok = QInputDialog.getText(self, 'Add Category', 'Category Name:')
        if ok and category:
            db.child(f"users/{self.user_id}/categories").push(category)
            self.load_categories()

    def load_expenses(self):
        self.expense_list.clear()
        self.selected_expense_id = None
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        expenses = db.child(f"users/{self.user_id}/expenses").get()
        total_expense = 0.0
        if expenses.each():
            for expense in expenses.each():
                item = expense.val()
                print(item)
                list_item = QListWidgetItem(f"{item['expense']}: ${item['amount']} [{item['category']}] on {item['date']}")
                list_item.setData(32, expense.key())
                self.expense_list.addItem(list_item)
                total_expense += float(item['amount'])
        else:
            self.expense_list.addItem("No expenses found.")
        self.total_label.setText(f'Total Expenses: ${total_expense:.2f}')

    def update_expense_list(self, expenses):
        self.expense_list.clear()
        self.selected_expense_id = None
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        total_expense = 0.0
        if expenses.each():
            for expense in expenses.each():
                item = expense.val()
                if self.filter_category_dropdown.currentIndex() > 0 and self.filter_category_dropdown.currentText() != item['category']:
                    continue
                list_item = QListWidgetItem(f"{item['expense']}: ${item['amount']} [{item['category']}] on {item['date']}")
                list_item.setData(32, expense.key())
                self.expense_list.addItem(list_item)
                total_expense += float(item['amount'])
        if self.expense_list.count() == 0:
            self.expense_list.addItem("No expenses found.")
        self.total_label.setText(f'Total Expenses: ${total_expense:.2f}')

    def filter_expenses(self):
        expenses = db.child(f"users/{self.user_id}/expenses").order_by_child("amount").get()
        self.update_expense_list(expenses)

    def add_expense(self):
        expense = self.expense_input.text()
        amount = self.amount_input.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        category = self.category_dropdown.currentText()
        if expense and amount and category:
            try:
                amount = float(amount)
                db.child(f"users/{self.user_id}/expenses").push({"expense": expense, "amount": amount, "date": date, "category": category})
                self.expense_input.clear()
                self.amount_input.clear()
                self.load_expenses()
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Amount must be a number.')
        else:
            QMessageBox.warning(self, 'Input Error', 'All fields are required.')

    def load_selected_expense(self, item):
        if item.text() == "No expenses found.":
            return
        expense_text = item.text()
        expense_id = item.data(32)
        if expense_id:
            self.selected_expense_id = expense_id
            parts = expense_text.split(': $')
            print(parts)
            expense = parts[0]
            amount, date = parts[1].split(' on ')
            amount, category = amount.split('[')
            category = category.replace(']', '')
            self.expense_input.setText(expense)
            self.amount_input.setText(amount)
            self.date_input.setDate(QDate.fromString(date, "yyyy-MM-dd"))
            self.category_dropdown.setCurrentText(category)
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            QMessageBox.warning(self, 'Format Error', 'The selected item has an unexpected format.')

    def edit_expense(self):
        if self.selected_expense_id:
            expense = self.expense_input.text()
            amount = self.amount_input.text()
            date = self.date_input.date().toString("yyyy-MM-dd")
            category = self.category_dropdown.currentText()
            if expense and amount:
                try:
                    amount = float(amount)
                    db.child(f"users/{self.user_id}/expenses").child(self.selected_expense_id).update({"expense": expense, "amount": amount, "date": date, "category": category})
                    self.load_expenses()
                except ValueError:
                    QMessageBox.warning(self, 'Invalid Input', 'Amount must be a number.')
            else:
                QMessageBox.warning(self, 'Input Error', 'All fields are required.')
                
    def delete_expense(self):
        if self.selected_expense_id:
            db.child(f"users/{self.user_id}/expenses").child(self.selected_expense_id).remove()
            self.expense_input.clear()
            self.amount_input.clear()
            self.load_expenses()

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Login')
        self.setGeometry(100, 100, 480, 200)

        self.app_name_label = QLabel('Paisa', self)

        self.email_label = QLabel('Email:', self)
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText('Enter email')

        self.password_label = QLabel('Password:', self)
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Password')
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.login)

        self.signup_button = QPushButton('Sign Up', self)
        self.signup_button.clicked.connect(self.signup)

        layout = QVBoxLayout()
        layout.addWidget(self.app_name_label)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            QMessageBox.information(self, 'Login Successful', f'Welcome {email}!')
            user_id = user['localId']
            self.redirect_to_main_app(user_id)
        except Exception as e:
            QMessageBox.warning(self, 'Login Failed', str(e))

    def signup(self):
        email = self.email_input.text()
        password = self.password_input.text()

        try:
            auth.create_user_with_email_and_password(email, password)
            QMessageBox.information(self, 'Sign Up Successful', f'Account created for {email}!')
            self.redirect_to_main_app()
        except Exception as e:
            QMessageBox.warning(self, 'Sign Up Failed', str(e))
            
    def redirect_to_main_app(self, user_id):
        self.main_app_window = ExpenseTrackerApp(user_id)
        self.main_app_window.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
