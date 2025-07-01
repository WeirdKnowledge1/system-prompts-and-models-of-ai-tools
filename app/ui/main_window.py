import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QLabel, QStatusBar, QMenuBar, QMessageBox)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QUrl, QDir # For QDesktopServices and QDir path conversion
from PyQt6.QtGui import QDesktopServices # For opening URLs/local paths
import os

# Placeholder for view modules - will be created in subsequent steps
from .trust_view import TrustView
from .charter_view import CharterView
from .deposit_view import DepositView
from .settings_view import SettingsView
# from .ledger_view import LedgerView
from app.utils.constants import (DOC_TRUST, DOC_CHARTER, DOC_DEPOSIT,
                                 COLOR_EQUITY, COLOR_POSTAL, COLOR_NATURAL_LAW, COLOR_DEFAULT_BG)
from app.ui.trust_view import TrustView # Explicit imports for isinstance checks
from app.ui.charter_view import CharterView
from app.ui.deposit_view import DepositView


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

        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self._create_menu_bar()
        self._create_status_bar()
        self._ensure_data_directories_exist()
        self._apply_initial_styling() # Apply styling to the initially selected tab

    def _apply_initial_styling(self):
        """Applies styling to the current tab when the app starts."""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self._on_tab_changed(current_index)

    def _on_tab_changed(self, index: int):
        """Applies styling based on jurisdiction when a tab is changed."""
        widget = self.tab_widget.widget(index)

        # Default style for non-document tabs or when coloring is off
        default_stylesheet = f"QWidget {{ background-color: {COLOR_DEFAULT_BG}; color: black; }}"
        # Note: Applying stylesheet to QWidget itself. If views have complex children,
        # they might override this. More specific styling within views might be needed eventually.

        if not self.settings_view.get_setting("jurisdictional_colors_enabled"):
            if widget: # Apply default to all tabs if coloring is off
                widget.setStyleSheet(default_stylesheet)
            # Also reset tab bar colors if they were changed
            # for i in range(self.tab_widget.count()):
            #     self.tab_widget.tabBar().setTabTextColor(i, Qt.GlobalColor.black) # Example reset
            return

        bg_color = COLOR_DEFAULT_BG
        text_color = "black" # Default text color

        if isinstance(widget, TrustView):
            # Assuming TrustView's document.jurisdiction might change, re-evaluate
            # For now, hardcoding based on typical primary jurisdiction.
            # A more dynamic approach would be: jurisdiction = widget.document.jurisdiction
            # For simplicity now: Trust -> Equity
            bg_color = COLOR_EQUITY
            text_color = "white"
        elif isinstance(widget, CharterView):
            bg_color = COLOR_POSTAL
            text_color = "black" # Gold is light, black text is better
        elif isinstance(widget, DepositView):
            # Deposit can be primarily Lex Aequies
            bg_color = COLOR_EQUITY
            text_color = "white"
        # Add elif for Natural Law if a view primarily uses it.
        # elif isinstance(widget, SomeNaturalLawView):
        #     bg_color = COLOR_NATURAL_LAW
        #     text_color = "white"

        if widget: # Apply to the main widget of the tab
            stylesheet = f"QWidget {{ background-color: {bg_color}; color: {text_color}; }}"

            # More specific styling to avoid issues with child widgets like QLineEdit
            # This targets the view itself, and QLabels, QGroupBox directly.
            # QLineEdit, QTextEdit, QListWidget etc. will need their own specific styling
            # if we want their backgrounds to also change or ensure text readability.
            # For now, this is a broad approach.

            # Let's try a more targeted approach for better readability:
            # Style the view itself, and let child widgets inherit or be styled separately.
            # The problem is QWidget stylesheet applies to children unless they override.
            # For now, we'll keep it simple and refine if major readability issues persist across many controls.

            widget.setStyleSheet(stylesheet)

            # Example of how to make QLineEdit readable on dark backgrounds:
            # common_input_style = "QLineEdit, QTextEdit { background-color: white; color: black; }"
            # widget.setStyleSheet(f"QWidget {{ background-color: {bg_color}; color: {text_color}; }} {common_input_style}")

    def _open_codex_vault(self):
        """Opens the Codex Vault directory in the system's file explorer."""
        codex_path = os.path.abspath(CODEX_VAULT_DIR)
        if not os.path.exists(codex_path):
            # Ensure it exists if somehow it wasn't created, though _ensure_data_directories_exist should handle it
            os.makedirs(codex_path, exist_ok=True)
            QMessageBox.information(self, "Codex Vault Created",
                                   f"The Codex Vault directory has been created at:\n{codex_path}")

        # Convert path to a file URL suitable for QDesktopServices
        url = QUrl.fromLocalFile(QDir.toNativeSeparators(codex_path))
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "Open Codex Vault Error",
                                f"Could not open the Codex Vault directory:\n{codex_path}\n"
                                "Please check if you have a default file explorer set up.")

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

        file_menu.addSeparator() #---------------------------------------------

        view_vault_action = QAction("&View Codex Vault", self)
        view_vault_action.triggered.connect(self._open_codex_vault)
        file_menu.addAction(view_vault_action)

        file_menu.addSeparator() #---------------------------------------------

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
