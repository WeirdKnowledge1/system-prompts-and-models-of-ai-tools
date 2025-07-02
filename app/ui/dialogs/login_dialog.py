from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QMessageBox, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt

# Temporary sys.path modification for direct import of core modules
import sys
import os
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

# Sibling import for RegistrationDialog
dialogs_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if dialogs_path not in sys.path:
    sys.path.insert(0, dialogs_path)


try:
    import database
    import auth_utils
    from registration_dialog import RegistrationDialog
except ImportError as e:
    print(f"CRITICAL: Could not import modules for LoginDialog: {e}")
    database = None
    auth_utils = None
    RegistrationDialog = None # So the app can at least load the class structure

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Login - Michaud Postal Equity App")
        self.setMinimumWidth(350)

        self.logged_in_username = None # To store username on successful login
        self.logged_in_user_id = None # To store user ID on successful login

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        form_layout.addRow(QLabel("Username:"), self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        form_layout.addRow(QLabel("Password:"), self.password_edit)

        main_layout.addLayout(form_layout)

        self.status_label = QLabel("") # For error messages
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Buttons: Login, Cancel, and Register
        # QDialogButtonBox handles standard roles (AcceptRole, RejectRole)
        self.button_box = QDialogButtonBox()
        login_button = self.button_box.addButton("Login", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel) # Standard cancel

        # Separate Register button, not part of standard Ok/Cancel roles here
        self.register_button = QPushButton("Register New User")
        self.register_button.clicked.connect(self.show_registration_dialog)

        # Layout for buttons to have Register on one side
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.register_button)
        button_layout.addStretch() # Pushes Ok/Cancel to the right
        button_layout.addWidget(self.button_box)
        main_layout.addLayout(button_layout)

        self.button_box.accepted.connect(self.handle_login) # Connect "Login" button
        self.button_box.rejected.connect(self.reject)   # Connect "Cancel" button

        self.setLayout(main_layout)

    def handle_login(self):
        self.status_label.setText("") # Clear previous errors
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not database or not auth_utils:
            QMessageBox.critical(self, "Error", "Core authentication modules are not available. Login cannot proceed.")
            self.reject()
            return

        if not username:
            self.status_label.setText("Username cannot be empty.")
            return
        if not password:
            self.status_label.setText("Password cannot be empty.")
            return

        user_data = database.get_user_by_username(username)

        if user_data:
            stored_hash = user_data["password_hash"]
            salt = user_data["salt"]
            if auth_utils.verify_password(stored_hash, salt, password):
                self.logged_in_username = user_data["username"]
                self.logged_in_user_id = user_data["id"]
                QMessageBox.information(self, "Login Successful", f"Welcome, {self.logged_in_username}!")
                super().accept() # Close dialog with Accepted result
            else:
                self.status_label.setText("Invalid username or password.")
        else:
            self.status_label.setText("Invalid username or password.")

    def show_registration_dialog(self):
        if not RegistrationDialog:
            QMessageBox.critical(self, "Error", "Registration module not available.")
            return

        # Create and show the registration dialog
        # The LoginDialog will be hidden while RegistrationDialog is active because RegistrationDialog is modal.
        reg_dialog = RegistrationDialog(self) # Pass self as parent
        if reg_dialog.exec(): # exec() returns QDialog.Accepted or QDialog.Rejected
            # Optionally, you could pre-fill username if registration was successful
            # For now, user has to re-enter credentials to log in after registering.
            QMessageBox.information(self, "Registration Complete",
                                    "Registration successful. Please log in with your new credentials.")
            self.username_edit.setText("") # Clear username to prompt for re-entry
            self.password_edit.setText("") # Clear password
            self.username_edit.setFocus()
        # else: user cancelled registration

    def get_logged_in_user_details(self) -> tuple[str | None, int | None]:
        """Returns the username and user ID if login was successful, else (None, None)."""
        if self.result() == QDialog.DialogCode.Accepted:
            return self.logged_in_username, self.logged_in_user_id
        return None, None

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    # Ensure the database is initialized for standalone testing
    # And auth_utils is available
    temp_paths_to_remove = []
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
        temp_paths_to_remove.append(module_path)
    if dialogs_path not in sys.path:
        sys.path.insert(0, dialogs_path)
        temp_paths_to_remove.append(dialogs_path)

    try:
        import database
        database.initialize_database()
    except Exception as e:
        print(f"Could not initialize DB for LoginDialog test: {e}")


    app = QApplication(sys.argv)
    login_dialog = LoginDialog()

    if not database or not auth_utils or not RegistrationDialog:
         QMessageBox.critical(None, "Module Load Error", "Core modules not loaded. Dialog functionality limited. This is for UI preview only.")

    if login_dialog.exec():
        username, user_id = login_dialog.get_logged_in_user_details()
        print(f"Login successful for user: {username} (ID: {user_id})")
    else:
        print("Login dialog cancelled or failed.")

    # Clean up sys.path if modified for testing
    for path_to_remove in temp_paths_to_remove:
        if path_to_remove in sys.path:
            sys.path.remove(path_to_remove)

    sys.exit(app.exec())
