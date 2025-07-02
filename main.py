import sys
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.dialogs.login_dialog import LoginDialog # Import LoginDialog
from app.core.database import initialize_database # Import database initializer

# Adjust sys.path if core and ui.dialogs are not directly importable from project root
# This is often needed if main.py is at the root and imports from subdirectories.
# However, if using `python -m main_module.main` from outside, or if project is structured
# as a package, this might not be strictly necessary. For now, assume direct imports work.
# If not, add:
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


def main():
    app = QApplication(sys.argv)

    # Initialize the database (creates DB and tables if they don't exist)
    try:
        initialize_database()
    except Exception as e:
        # Use QMessageBox for critical startup errors if QApplication is already running
        # For now, print and potentially exit if DB init is absolutely critical before any UI.
        print(f"CRITICAL: Failed to initialize database: {e}")
        # Depending on severity, you might exit here:
        # from PyQt6.QtWidgets import QMessageBox
        # QMessageBox.critical(None, "Database Error", f"Failed to initialize database: {e}\nApplication will exit.")
        # sys.exit(1)
        # For now, we'll let it proceed to login dialog, which might also fail if DB is broken.
        pass


    # Show Login Dialog
    login_dialog = LoginDialog()
    if login_dialog.exec(): # exec() returns QDialog.Accepted or QDialog.Rejected
        logged_in_username, logged_in_user_id = login_dialog.get_logged_in_user_details()

        if logged_in_username and logged_in_user_id is not None:
            main_win = MainWindow(current_username=logged_in_username, current_user_id=logged_in_user_id)
            main_win.show()
            sys.exit(app.exec())
        else:
            # This case should ideally not be reached if dialog.accept() means successful login
            print("Login was accepted, but no user details returned. Exiting.")
            sys.exit(1)
    else:
        # User cancelled the login dialog (or registration)
        print("Login cancelled or failed. Exiting application.")
        sys.exit(0)

if __name__ == '__main__':
    main()
