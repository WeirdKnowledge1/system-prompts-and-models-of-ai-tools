import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QLabel, QStatusBar, QMenuBar, QMessageBox)
from PyQt6.QtGui import QAction, QIcon
import os

# Placeholder for view modules - will be created in subsequent steps
from .trust_view import TrustView
from .charter_view import CharterView
from .deposit_view import DepositView
from .settings_view import SettingsView
# from .ledger_view import LedgerView
from app.utils.constants import DOC_TRUST, DOC_CHARTER, DOC_DEPOSIT, COLOR_EQUITY, COLOR_POSTAL

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Michaud Postal Equity App - MPEA")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create actual views
        self.trust_view = TrustView(self)
        self.charter_view = CharterView(self)
        self.deposit_view = DepositView(self)
        self.settings_view = SettingsView(self)
        # self.ledger_view = LedgerView(self) # Placeholder

        # Add tabs with actual views
        self.tab_widget.addTab(self.trust_view, DOC_TRUST)
        self.tab_widget.addTab(self.charter_view, DOC_CHARTER)
        self.tab_widget.addTab(self.deposit_view, DOC_DEPOSIT)
        self.tab_widget.addTab(self.settings_view, "System Preferences")

        # Placeholder tabs for other views
        self.ledger_tab_placeholder = QWidget()
        self.ledger_tab_placeholder.setLayout(QVBoxLayout())
        self.ledger_tab_placeholder.layout().addWidget(QLabel("Content for Ledgers will be here."))
        self.tab_widget.addTab(self.ledger_tab_placeholder, "Ledgers")

        # Apply initial styling (e.g., background color for Trust tab)
        # This will be expanded in Phase 2 for dynamic jurisdictional colors
        self.trust_view.setStyleSheet(f"background-color: {COLOR_EQUITY}; color: white;") # Example
        # Find the actual QWidget container for the tab to style its background directly if needed
        # For more fine-grained control, styling should be applied to specific widgets within TrustView.
        # For now, applying to the whole TrustView widget.

        self._create_menu_bar()
        self._create_status_bar()
        self._ensure_data_directories_exist()

    def _create_menu_bar(self):
        self.menu_bar = self.menuBar()
        # File Menu
        file_menu = self.menu_bar.addMenu("&File")

        new_action = QAction("&New", self)
        # new_action.triggered.connect(self.new_file) # Placeholder
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        # open_action.triggered.connect(self.open_file) # Placeholder
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        # save_action.triggered.connect(self.save_file) # Placeholder
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu (Placeholder)
        edit_menu = self.menu_bar.addMenu("&Edit")
        undo_action = QAction("&Undo", self)
        # undo_action.triggered.connect(self.undo_action_triggered) # Placeholder
        edit_menu.addAction(undo_action)

        # View Menu (Placeholder)
        view_menu = self.menu_bar.addMenu("&View")

        # Tools Menu (Placeholder)
        tools_menu = self.menu_bar.addMenu("&Tools")

        # Help Menu
        help_menu = self.menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")

    def show_about_dialog(self):
        QMessageBox.about(self, "About Michaud Postal Equity App",
                          "Michaud Postal Equity App (MPEA)\n"
                          "Version 0.1 (Alpha)\n"
                          "Built with PyQt6")

    def _ensure_data_directories_exist(self):
        base_data_dir = "data"
        sub_dirs = ["trusts", "charters", "deposits", "backups", "codex_vault_sources", "zip_modules"]
        if not os.path.exists(base_data_dir):
            os.makedirs(base_data_dir)
        for sub_dir in sub_dirs:
            path = os.path.join(base_data_dir, sub_dir)
            if not os.path.exists(path):
                os.makedirs(path)

        # For Codex Vault (Part III.A) - User uploaded files
        codex_vault_uploads_path = os.path.join(base_data_dir, "codex_vault_sources", "uploads")
        if not os.path.exists(codex_vault_uploads_path):
            os.makedirs(codex_vault_uploads_path)


if __name__ == '__main__':
    # This is for testing the main window directly.
    # The main entry point will be main.py
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
