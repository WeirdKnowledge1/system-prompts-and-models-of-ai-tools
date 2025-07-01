import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QLabel, QStatusBar, QMenuBar, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QUrl, QDir, QTimer # For QDesktopServices, QDir path conversion, and QTimer
from PyQt6.QtGui import QDesktopServices # For opening URLs/local paths
import os
import shutil # For file copying
import datetime # For timestamping in manifest

# Placeholder for view modules - will be created in subsequent steps
from .trust_view import TrustView
from .charter_view import CharterView
from .deposit_view import DepositView
from .settings_view import SettingsView
from .dashboard_view import DashboardView
from app.ui.dialogs.personal_info_dialog import PersonalInfoDialog
from .ledger_view import LedgerView
from app.core.daily_assistant_agent import DailyAssistantAgent # Import DailyAssistantAgent
from app.utils.constants import (DOC_TRUST, DOC_CHARTER, DOC_DEPOSIT,
                                 COLOR_EQUITY, COLOR_POSTAL, COLOR_NATURAL_LAW, COLOR_DEFAULT_BG)
from app.ui.trust_view import TrustView
from app.ui.charter_view import CharterView
from app.ui.deposit_view import DepositView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Michaud Postal Equity App - MPEA")
        self.setGeometry(100, 100, 1200, 800)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create actual views
        self.dashboard_view = DashboardView(self) # Create dashboard first
        self.trust_view = TrustView(self)
        self.charter_view = CharterView(self)
        self.deposit_view = DepositView(self)
        self.settings_view = SettingsView(main_window=self)
        self.ledger_view = LedgerView(self) # Create LedgerView instance

        # Add tabs, dashboard first
        self.tab_widget.addTab(self.dashboard_view, "Master AI Dashboard")
        self.tab_widget.addTab(self.trust_view, DOC_TRUST)
        self.tab_widget.addTab(self.charter_view, DOC_CHARTER)
        self.tab_widget.addTab(self.deposit_view, DOC_DEPOSIT)
        self.tab_widget.addTab(self.ledger_view, "Document Ledgers") # Add actual LedgerView
        self.tab_widget.addTab(self.settings_view, "System Preferences")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        # Connect document view signals to update dashboard (conceptual for now)
        # Example: self.trust_view.document_loaded_signal.connect(self.update_dashboard_current_doc)

        self._create_menu_bar()
        self._create_status_bar()
        self._ensure_data_directories_exist()
        self._apply_initial_styling()
        self._setup_auto_save_timer()
        self._run_daily_assistant_on_startup()


    def _run_daily_assistant_on_startup(self):
        if hasattr(self, 'settings_view') and self.settings_view.get_setting("daily_assistant_enabled"):
            if hasattr(self, 'dashboard_view'):
                try:
                    assistant = DailyAssistantAgent(app_context=self) # Pass main_window as context
                    reminders = assistant.get_daily_reminders()
                    if reminders:
                        for reminder in reminders:
                            self.dashboard_view.add_notification(f"Daily Assistant: {reminder}")
                        # Optionally, show a summary QMessageBox as well for more prominence on startup
                        # QMessageBox.information(self, "Daily Assistant Reminders",
                        #                         "The Daily Assistant has some reminders for you (check Dashboard notifications).")
                    else:
                        self.dashboard_view.add_notification("Daily Assistant: No specific reminders today.")
                except Exception as e:
                    print(f"Error running Daily Assistant on startup: {e}")
                    if hasattr(self, 'dashboard_view'):
                        self.dashboard_view.add_notification(f"Error initializing Daily Assistant: {e}")


    def _setup_auto_save_timer(self):
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self._update_auto_save_timer_interval() # Start it if enabled

    def _update_auto_save_timer_interval(self):
        if hasattr(self, 'settings_view') and self.settings_view.get_setting("auto_save_enabled"):
            interval_minutes = self.settings_view.get_setting("auto_save_interval_minutes")
            self.auto_save_timer.start(interval_minutes * 60 * 1000) # Convert minutes to milliseconds
            print(f"Auto-save timer started with interval: {interval_minutes} minutes.")
        else:
            self.auto_save_timer.stop()
            print("Auto-save timer stopped.")

    def _perform_auto_save(self):
        active_view = self._get_active_document_view()
        if active_view and hasattr(active_view, 'is_modified') and active_view.is_modified:
            if active_view.current_document_path: # Only auto-save if it has a path
                print(f"Auto-saving document: {active_view.document.name}")
                # Call save_document with silent=True
                # The view's save_document method needs to accept a silent parameter
                # and not show popups if silent is True.
                if hasattr(active_view, 'save_document'):
                    active_view.save_document(silent=True) # This clears is_modified
            else: # No current_document_path, but document is modified (it's a new document)
                try:
                    autosave_dir = os.path.join(CODEX_VAULT_DIR, "autosaves")
                    os.makedirs(autosave_dir, exist_ok=True)

                    doc_type_name = active_view.document.doc_type.replace(" ", "_")
                    # Use a portion of the document's current in-memory ID for the autosave filename
                    doc_id_part = active_view.document.id.split('-')[0] # first part of UUID
                    filename = f"{doc_type_name}_{doc_id_part}_autosave_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                    autosave_path = os.path.join(autosave_dir, filename)

                    # We need a way to save document content without altering its state (is_modified, current_path)
                    # or creating a new ID, just dumping its current content.
                    # The existing save_document/save_document_as are not suitable directly for this type of autosave.
                    # Let's add a simple content dump for autosaving new files.
                    with open(autosave_path, 'w') as f:
                        json.dump(active_view.document.to_dict(), f, indent=4)

                    self.status_bar.showMessage(f"New '{active_view.document.doc_type}' auto-saved to recovery area.", 5000)
                    print(f"Auto-saved new document '{active_view.document.name}' to {autosave_path}")
                    # DO NOT clear active_view.is_modified here, as the main document is still "new and unsaved"
                except Exception as e:
                    print(f"Error auto-saving new document {active_view.document.name}: {e}")
        else:
            # print("Auto-save: No active, modified document to save.") # Reduced verbosity
            pass


    def _apply_initial_styling(self):
        """Applies styling to the current tab when the app starts."""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self._on_tab_changed(current_index)

    def settings_updated(self):
        """Called when settings are saved in SettingsView."""
        self._update_auto_save_timer_interval()
        # Also re-apply styling in case jurisdictional color setting changed
        self._apply_initial_styling() # This calls _on_tab_changed for current tab

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
            if isinstance(widget, (TrustView, CharterView, DepositView)):
                if hasattr(widget, 'jurisdiction_header_label'): # Check if the view has the label
                    # Ensure settings_view is initialized before accessing get_setting
                    if hasattr(self, 'settings_view') and self.settings_view:
                         show_headers = self.settings_view.get_setting("show_jurisdiction_headers")
                         widget.jurisdiction_header_label.setVisible(show_headers)
                    else: # Fallback if settings_view isn't ready (should not happen in normal flow)
                        widget.jurisdiction_header_label.setVisible(True)

        elif widget: # For non-document tabs or if coloring is off and widget is not None
             widget.setStyleSheet(default_stylesheet)
             if hasattr(widget, 'jurisdiction_header_label'):
                 widget.jurisdiction_header_label.setVisible(False)

        # Update LedgerView with the current document if applicable
        active_doc_view = self._get_active_document_view() # Get current doc view
        if active_doc_view and hasattr(active_doc_view, 'document'):
            self.ledger_view.set_document(active_doc_view.document)
             # Update dashboard's current document display
            if hasattr(self, 'dashboard_view'):
                self.dashboard_view.update_current_document(
                    active_doc_view.document.name,
                    active_doc_view.document.jurisdiction
                )
        elif not isinstance(widget, (TrustView, CharterView, DepositView)): # if not a doc view
            self.ledger_view.set_document(None) # Clear ledger if not a doc tab
            if hasattr(self, 'dashboard_view'):
                 self.dashboard_view.update_current_document(None, None)


    def _get_active_document_view(self) -> QWidget | None:
        """Helper to get the currently active document view if it's one of our known types."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, (TrustView, CharterView, DepositView)):
            return current_widget
        return None

    def _trigger_save_active_document(self):
        active_view = self._get_active_document_view()
        if active_view and hasattr(active_view, 'save_document'):
            active_view.save_document()
        else:
            self.status_bar.showMessage("No active document to save or save not supported for this tab.", 3000)

    def _trigger_save_as_active_document(self):
        active_view = self._get_active_document_view()
        if active_view and hasattr(active_view, 'save_document_as'):
            active_view.save_document_as()
        else:
            self.status_bar.showMessage("No active document for 'Save As' or operation not supported.", 3000)

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
        save_action.triggered.connect(self._trigger_save_active_document)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.triggered.connect(self._trigger_save_as_active_document)
        file_menu.addAction(save_as_action)

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

        # Tools Menu
        tools_menu = self.menu_bar.addMenu("&Tools")
        manage_personal_info_action = QAction("Manage &Personal Info...", self)
        manage_personal_info_action.triggered.connect(self._open_personal_info_manager)
        tools_menu.addAction(manage_personal_info_action)

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
        sub_dirs = ["trusts", "charters", "deposits", "backups",
                    "codex_vault_sources", "zip_modules", "autosaves"] # Added "autosaves"
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
