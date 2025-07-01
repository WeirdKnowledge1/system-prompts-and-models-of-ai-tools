import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QLabel, QStatusBar, QMenuBar, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QUrl, QDir # For QDesktopServices and QDir path conversion
from PyQt6.QtGui import QDesktopServices # For opening URLs/local paths
import os
import shutil # For file copying
import datetime # For timestamping in manifest

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

        if widget:
            # Determine the object name of the view for specific targeting
            # Ensure views have self.setObjectName("ViewName") in their __init__
            # For now, we assume they might not, so we use a general QWidget for the base.
            # view_object_name = widget.objectName() if widget.objectName() else "QWidget"
            # Using widget.metaObject().className() might be more reliable if objectName isn't set.

            # Base style for the tab widget itself (the view container)
            # This makes the direct background of the view the jurisdictional color.
            base_view_style = f"QWidget {{ background-color: {bg_color}; }}"

            # General text color for QLabels directly on the view background
            # Also make their own backgrounds transparent so the view background shows.
            label_style = f"QLabel {{ color: {text_color}; background-color: transparent; }}"

            # Styles for input fields to ensure readability
            input_fields_style = """
                QLineEdit, QTextEdit, QComboBox, QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #888888; /* Slightly darker border for inputs */
                    padding: 3px;
                }
                QComboBox { /* Ensure combobox also has padding */
                    padding: 3px;
                }
                QComboBox::drop-down {
                    border-left: 1px solid #888888;
                    /* image: url(path/to/your/dropdown-arrow.png); Optional custom arrow */
                }
                QListWidget::item:selected {
                    background-color: #0078d7; /* Standard selection blue */
                    color: white;
                }
            """
            # Styles for buttons
            button_style = f"""
                QPushButton {{
                    color: {"white" if bg_color == COLOR_EQUITY else "black"}; /* Text color based on background */
                    background-color: {"#5050A0" if bg_color == COLOR_EQUITY else "#D0D0D0"}; /* Button color adapting to theme */
                    border: 1px solid {"#7070C0" if bg_color == COLOR_EQUITY else "#A0A0A0"};
                    padding: 5px 10px;
                    min-height: 20px; /* Ensure buttons are not too small */
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {"#6060B0" if bg_color == COLOR_EQUITY else "#E0E0E0"};
                }}
                QPushButton:pressed {{
                    background-color: {"#404090" if bg_color == COLOR_EQUITY else "#C0C0C0"};
                }}
                QPushButton:disabled {{
                    color: #707070;
                    background-color: #B0B0B0;
                    border-color: #909090;
                }}
            """

            # Styles for GroupBoxes
            groupbox_style = f"""
                QGroupBox {{
                    color: {text_color}; /* Title text color */
                    background-color: transparent;
                    border: 1px solid {text_color if text_color == 'white' else '#AAAAAA'}; /* Brighter border for dark themes */
                    border-radius: 4px;
                    margin-top: 12px; /* make space for the title */
                    padding: 10px 5px 5px 5px; /* top, right, bottom, left */
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center; /* position at the top center */
                    padding: 0 5px;
                    background-color: {bg_color}; /* Match groupbox title background to tab background */
                    color: {text_color};
                    border-radius: 3px; /* Optional: rounded corners for title background */
                }}
            """

            # Combine stylesheets
            # The widget itself (the view) gets the base background.
            # Then specific child widget types are styled.
            combined_stylesheet = "\n".join([
                base_view_style, # Applied to the main QWidget of the tab
                label_style,
                input_fields_style,
                button_style,
                groupbox_style
            ])

            widget.setStyleSheet(combined_stylesheet)

            # Show/Hide Jurisdiction Header Label based on settings
            # This applies to document views that have this label
            if isinstance(widget, (TrustView, CharterView, DepositView)):
                show_headers = self.settings_view.get_setting("show_jurisdiction_headers")
                if hasattr(widget, 'jurisdiction_header_label'): # Check if the view has the label
                    widget.jurisdiction_header_label.setVisible(show_headers)
                # If the view itself is the one with the jurisdiction_header_label, then:
                # widget.jurisdiction_header_label.setVisible(show_headers)

        elif widget: # For non-document tabs or if coloring is off and widget is not None
             widget.setStyleSheet(default_stylesheet) # Apply default style
             # Also hide jurisdiction header if it's a non-doc tab that might have had it visible from a previous doc tab
             if hasattr(widget, 'jurisdiction_header_label'):
                 widget.jurisdiction_header_label.setVisible(False)


    def _upload_files_to_vault(self):
        """Allows user to select files and copies them to the Codex Vault uploads directory."""
        upload_dir = os.path.join(CODEX_VAULT_DIR, "codex_vault_sources", "uploads")
        # Ensure directory exists (it should due to _ensure_data_directories_exist)
        # os.makedirs(upload_dir, exist_ok=True)

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Document(s) to Upload to Codex Vault",
            QDir.homePath(), # Start in user's home directory
            "Documents (*.pdf *.docx *.txt);;All Files (*)"
        )

        if not file_paths:
            return # User cancelled

        success_files = []
        error_files = []

        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(upload_dir, file_name)

                if os.path.exists(destination_path):
                    reply = QMessageBox.question(
                        self, "File Exists",
                        f"The file '{file_name}' already exists in the Codex Vault uploads.\nOverwrite it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Cancel:
                        QMessageBox.information(self, "Upload Cancelled", "File upload operation cancelled by user.")
                        return # Cancel entire operation
                    elif reply == QMessageBox.StandardButton.No:
                        error_files.append(f"{file_name} (skipped, not overwritten)")
                        continue # Skip this file
                    # If Yes, proceed to overwrite

                shutil.copy2(file_path, destination_path) # copy2 preserves metadata
                success_files.append(file_name)
            except Exception as e:
                error_files.append(f"{os.path.basename(file_path)} (Error: {e})")

        message = []
        if success_files:
            message.append(f"Successfully uploaded:\n- " + "\n- ".join(success_files))
        if error_files:
            message.append(f"Errors/Skipped:\n- " + "\n- ".join(error_files))

        if not message:
             final_message = "No files were selected or processed."
        else:
            final_message = "\n\n".join(message)

        QMessageBox.information(self, "Codex Vault Upload Report", final_message.strip())

        self._update_vault_manifest(success_files, upload_dir)

    def _update_vault_manifest(self, successfully_uploaded_filenames: list, upload_dir: str):
        """
        Creates or updates a manifest.json file in the codex_vault_sources directory
        with details of uploaded files and basic parsing for .txt files.
        """
        manifest_path = os.path.join(CODEX_VAULT_DIR, "codex_vault_sources", "manifest.json")
        manifest_data = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse existing manifest {manifest_path}. Starting fresh.")
                manifest_data = {"files": {}} # Ensure "files" key exists

        if "files" not in manifest_data: # Ensure the 'files' key exists
            manifest_data["files"] = {}

        for filename in successfully_uploaded_filenames:
            file_path_in_vault = os.path.join(upload_dir, filename)
            file_entry = {
                "path": file_path_in_vault,
                "upload_date": datetime.datetime.now().isoformat(),
                "parsed_status": "not_attempted",
                "extracted_segments_count": 0,
                "extracted_segments": [] # Placeholder for actual segments later
            }

            if filename.lower().endswith(".txt"):
                try:
                    with open(file_path_in_vault, 'r', encoding='utf-8') as f_txt:
                        content = f_txt.read()
                    # Basic parsing: split by double newlines
                    segments = [seg.strip() for seg in content.split("\n\n") if seg.strip()]
                    file_entry["parsed_status"] = "basic_text_extraction"
                    file_entry["extracted_segments_count"] = len(segments)
                    # Storing full segments might make manifest large. For now, just count.
                    # file_entry["extracted_segments"] = segments
                    print(f"TXT file '{filename}': Found {len(segments)} potential segments.")
                except Exception as e:
                    print(f"Error parsing TXT file '{filename}': {e}")
                    file_entry["parsed_status"] = f"error_parsing_txt: {e}"

            elif filename.lower().endswith((".pdf", ".docx")):
                file_entry["parsed_status"] = "parsing_not_implemented"
                print(f"File '{filename}': Parsing for this file type not yet implemented.")

            manifest_data["files"][filename] = file_entry # Use filename as key

        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=4)
            print(f"Codex Vault manifest updated: {manifest_path}")
        except Exception as e:
            print(f"Error writing Codex Vault manifest: {e}")


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

        upload_to_vault_action = QAction("&Upload Document(s) to Codex Vault...", self)
        upload_to_vault_action.triggered.connect(self._upload_files_to_vault)
        file_menu.addAction(upload_to_vault_action)

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
