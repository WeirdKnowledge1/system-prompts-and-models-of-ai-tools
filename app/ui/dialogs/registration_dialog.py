from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QMessageBox, QLabel)
from PyQt6.QtCore import Qt

# To be imported once db and auth_utils are available in the project structure
# For now, direct import for this step's context.
import sys
import os
# This assumes registration_dialog.py is in app/ui/dialogs/
# Adjust path to reach app/core/
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

try:
    import database
    import auth_utils
except ImportError as e:
    print(f"CRITICAL: Could not import database or auth_utils for RegistrationDialog: {e}")
    # In a real app, this might prevent the dialog from even being created,
    # or the app might not start. For now, we proceed, but calls will fail.
    database = None
    auth_utils = None


class RegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New User")
        self.setMinimumWidth(350)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Choose a username")
        form_layout.addRow(QLabel("Username:"), self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        form_layout.addRow(QLabel("Password:"), self.password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm password")
        form_layout.addRow(QLabel("Confirm Password:"), self.confirm_password_edit)

        main_layout.addLayout(form_layout)

        self.status_label = QLabel("") # For error messages
        self.status_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.status_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.handle_registration)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def handle_registration(self):
        self.status_label.setText("") # Clear previous errors
        username = self.username_edit.text().strip()
        password = self.password_edit.text() # No strip, allow spaces if user wants
        confirm_password = self.confirm_password_edit.text()

        if not database or not auth_utils:
            QMessageBox.critical(self, "Error", "Core authentication modules are not available. Registration cannot proceed.")
            self.reject() # Close dialog as it's non-functional
            return

        if not username:
            self.status_label.setText("Username cannot be empty.")
            return
        if not password:
            self.status_label.setText("Password cannot be empty.")
            return
        if password != confirm_password:
            self.status_label.setText("Passwords do not match.")
            return

        # Basic password strength (example - can be much more complex)
        if len(password) < 8:
            self.status_label.setText("Password must be at least 8 characters long.")
            return

        # Check if username already exists
        existing_user = database.get_user_by_username(username)
        if existing_user:
            self.status_label.setText(f"Username '{username}' is already taken. Please choose another.")
            return

        # Proceed with registration
        try:
            salt = auth_utils.generate_salt_hex()
            hashed_password = auth_utils.hash_password(password, salt)

            user_id = database.add_user(username, hashed_password, salt)

            if user_id is not None:
                QMessageBox.information(self, "Registration Successful",
                                        f"User '{username}' registered successfully!")
                super().accept() # Call QDialog.accept() to close with Accepted result
            else:
                # This case might be redundant if add_user already catches IntegrityError for username
                self.status_label.setText("Registration failed: Could not save user to database (username might be taken).")
        except Exception as e:
            self.status_label.setText(f"An error occurred during registration: {e}")
            print(f"Registration error: {e}")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    # Ensure the database is initialized for standalone testing
    if database:
        print("Initializing database for RegistrationDialog test...")
        database.initialize_database()
    else:
        print("Skipping database initialization as module failed to load.")


    app = QApplication(sys.argv)
    dialog = RegistrationDialog()

    # For testing, you might want to see the dialog even if core modules fail to load initially
    # to test UI, but registration itself won't work.
    if not database or not auth_utils:
         QMessageBox.critical(None, "Module Load Error", "Database or Auth Utils not loaded. Registration will fail. This is for UI preview only.")

    if dialog.exec():
        print("Registration dialog accepted (user likely created).")
    else:
        print("Registration dialog cancelled.")

    # Clean up sys.path if modified for testing
    if module_path in sys.path and sys.path[0] == module_path:
        sys.path.pop(0)

    sys.exit(app.exec())
