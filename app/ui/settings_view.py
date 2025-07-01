from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QCheckBox,
                             QGroupBox, QScrollArea, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
import json
import os

# Define a settings file path
SETTINGS_FILE_PATH = os.path.join("data", "app_settings.json")

class SettingsView(QWidget):
    def __init__(self, main_window=None, parent=None): # Added main_window
        super().__init__(parent)
        self.main_window = main_window # Store reference
        self.settings = self._load_settings()
        self._setup_ui()

    def _default_settings(self):
        """Provides default values for all settings."""
        return {
            "voice_input_enabled": False,
            "zip_module_loader_enabled": False,
            "legal_embossed_seal_enabled": False,
            "qr_proof_chain_embeds_enabled": False,
            "offline_mode_autonomous_ai_enabled": False,
            "natural_law_final_jurisdiction_enabled": False,
            "enforce_clauseconformer_all_docs": True,
            "jurisdictional_colors_enabled": True,
            "permit_live_clause_editing": False,
            "show_jurisdiction_headers": True,
            "zip_rewrite_ai_logic_enabled": False,
            "auto_validate_codex_memory": True,
            "allow_clause_conversion": True,
            "local_archive_source_uploads": True,
            "auto_save_enabled": True,
            "auto_save_interval_minutes": 5,
            "daily_assistant_enabled": True        # New for Daily Assistant
            # Add other settings from the full list in Part II.A.1 with defaults
        }

    def _load_settings(self):
        """Loads settings from a JSON file, or returns defaults if file not found/invalid."""
        defaults = self._default_settings()
        if not os.path.exists(SETTINGS_FILE_PATH):
            return defaults
        try:
            with open(SETTINGS_FILE_PATH, 'r') as f:
                loaded_settings = json.load(f)
            # Ensure all keys from defaults are present, add if missing
            for key, value in defaults.items():
                if key not in loaded_settings:
                    loaded_settings[key] = value
            return loaded_settings
        except json.JSONDecodeError:
            return defaults # Return defaults if JSON is corrupted
        except Exception:
            return defaults


    def _save_settings(self):
        """Saves current settings to a JSON file."""
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE_PATH), exist_ok=True)
            with open(SETTINGS_FILE_PATH, 'w') as f:
                json.dump(self.settings, f, indent=4)
            QMessageBox.information(self, "Settings Saved", "Application settings have been saved.")
            if self.main_window and hasattr(self.main_window, 'settings_updated'):
                self.main_window.settings_updated() # Notify main window
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Settings", f"Could not save settings: {e}")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Scroll Area for many settings
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)

        settings_layout = QVBoxLayout(scroll_content_widget)

        # --- Interface Customization Group ---
        interface_group = QGroupBox("Interface Customization")
        interface_layout = QGridLayout()

        # Jurisdictional Visual Feedback (Color Scheme Toggle) - Part IV.B (Moved here)
        self.jurisdictional_colors_checkbox = QCheckBox("Enable Jurisdictional Visual Feedback (Colors)")
        self.jurisdictional_colors_checkbox.setToolTip("Changes UI colors based on document jurisdiction (Equity, Postal, Natural Law).")
        self.jurisdictional_colors_checkbox.setChecked(self.settings.get("jurisdictional_colors_enabled", True))
        self.jurisdictional_colors_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"jurisdictional_colors_enabled": state == Qt.CheckState.Checked.value})
        )
        interface_layout.addWidget(self.jurisdictional_colors_checkbox, 0, 0)
        interface_layout.addWidget(QLabel("Applies color schemes to document views based on their governing law."), 0, 1)

        # Show/Hide Document Jurisdiction Headers (Moved here)
        self.show_jurisdiction_headers_checkbox = QCheckBox("Show Document Jurisdiction Headers")
        self.show_jurisdiction_headers_checkbox.setToolTip("Toggles the visibility of jurisdiction headers within document views.")
        self.show_jurisdiction_headers_checkbox.setChecked(self.settings.get("show_jurisdiction_headers", True))
        self.show_jurisdiction_headers_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"show_jurisdiction_headers": state == Qt.CheckState.Checked.value})
        )
        interface_layout.addWidget(self.show_jurisdiction_headers_checkbox, 1, 0)
        interface_layout.addWidget(QLabel("Controls visibility of jurisdictional headers in documents."), 1, 1)

        interface_group.setLayout(interface_layout)
        settings_layout.addWidget(interface_group)

        # --- AI & Automation Features Group ---
        ai_automation_group = QGroupBox("AI & Automation Features")
        ai_automation_layout = QGridLayout()

        # Enable/Disable Voice Input
        self.voice_input_checkbox = QCheckBox("Enable Voice Input")
        self.voice_input_checkbox.setToolTip("Enables or disables voice command input for the application.")
        self.voice_input_checkbox.setChecked(self.settings.get("voice_input_enabled", False))
        self.voice_input_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"voice_input_enabled": state == Qt.CheckState.Checked.value})
        )
        ai_automation_layout.addWidget(self.voice_input_checkbox, 0, 0)
        ai_automation_layout.addWidget(QLabel("Allows interaction with the app using voice commands. (Placeholder)"), 0, 1)

        # Enable/Disable ZIP Module Loader
        self.zip_loader_checkbox = QCheckBox("Enable ZIP Module Loader")
        self.zip_loader_checkbox.setToolTip("Allows loading of new logic modules via .zip files.")
        self.zip_loader_checkbox.setChecked(self.settings.get("zip_module_loader_enabled", False))
        self.zip_loader_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"zip_module_loader_enabled": state == Qt.CheckState.Checked.value})
        )
        ai_automation_layout.addWidget(self.zip_loader_checkbox, 1, 0)
        ai_automation_layout.addWidget(QLabel("Permits upgrading AI logic and features via ZIP uploads. (Placeholder)"), 1, 1)

        # Enable ZIP Upload to Rewrite AI Logic (Auto-Upgrade) - New
        self.zip_rewrite_ai_checkbox = QCheckBox("Enable ZIP Upload to Rewrite AI Logic (Auto-Upgrade)")
        self.zip_rewrite_ai_checkbox.setToolTip("Allows ZIP uploads to directly modify core AI operational logic.")
        self.zip_rewrite_ai_checkbox.setChecked(self.settings.get("zip_rewrite_ai_logic_enabled", False))
        self.zip_rewrite_ai_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"zip_rewrite_ai_logic_enabled": state == Qt.CheckState.Checked.value})
        )
        ai_automation_layout.addWidget(self.zip_rewrite_ai_checkbox, 2, 0)
        ai_automation_layout.addWidget(QLabel("Grants ZIP modules permission for AI self-optimization. (Placeholder)"), 2, 1)

        # Enable Daily Assistant Mode - New
        self.daily_assistant_checkbox = QCheckBox("Enable Daily Assistant Mode")
        self.daily_assistant_checkbox.setToolTip("Enables the AI to provide daily reminders and suggestions.")
        self.daily_assistant_checkbox.setChecked(self.settings.get("daily_assistant_enabled", True)) # Default ON
        self.daily_assistant_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"daily_assistant_enabled": state == Qt.CheckState.Checked.value})
        )
        ai_automation_layout.addWidget(self.daily_assistant_checkbox, 3, 0)
        ai_automation_layout.addWidget(QLabel("AI provides daily reminders and suggestions. (Placeholder functionality)"), 3, 1)

        # Enable Offline Mode / Autonomous AI
        self.offline_mode_checkbox = QCheckBox("Enable Offline Mode / Autonomous AI")
        self.offline_mode_checkbox.setToolTip("Allows the AI to operate fully offline with all features.")
        self.offline_mode_checkbox.setChecked(self.settings.get("offline_mode_autonomous_ai_enabled", False))
        self.offline_mode_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"offline_mode_autonomous_ai_enabled": state == Qt.CheckState.Checked.value})
        )
        ai_automation_layout.addWidget(self.offline_mode_checkbox, 3, 0)
        ai_automation_layout.addWidget(QLabel("Enables full AI functionality without internet access. (Placeholder)"), 3, 1)

        ai_automation_group.setLayout(ai_automation_layout)
        settings_layout.addWidget(ai_automation_group)

        # --- Document & Clause Behavior Group ---
        doc_clause_group = QGroupBox("Document & Clause Behavior")
        doc_clause_layout = QGridLayout()

        # Enable Legal Embossed Seal (QR-authenticated)
        self.embossed_seal_checkbox = QCheckBox("Enable Legal Embossed Seal (QR-authenticated)")
        self.embossed_seal_checkbox.setToolTip("Marks documents for physical embossing with a QR-authenticated seal.")
        self.embossed_seal_checkbox.setChecked(self.settings.get("legal_embossed_seal_enabled", False))
        self.embossed_seal_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"legal_embossed_seal_enabled": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.embossed_seal_checkbox, 0, 0)
        doc_clause_layout.addWidget(QLabel("Outputs documents with markings for a QR-authenticated legal seal. (Placeholder)"), 0, 1)

        # Enable QR Proof Chain Embeds
        self.qr_proof_checkbox = QCheckBox("Enable QR Proof Chain Embeds")
        self.qr_proof_checkbox.setToolTip("Embeds QR-coded chains of source proof and timestamps into documents.")
        self.qr_proof_checkbox.setChecked(self.settings.get("qr_proof_chain_embeds_enabled", False))
        self.qr_proof_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"qr_proof_chain_embeds_enabled": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.qr_proof_checkbox, 1, 0)
        doc_clause_layout.addWidget(QLabel("Embeds traceable QR codes linking to source proofs within documents."), 1, 1)

        # Enable Natural Law Enforcement as Final Jurisdiction
        self.natural_law_final_checkbox = QCheckBox("Enable Natural Law Enforcement as Final Jurisdiction")
        self.natural_law_final_checkbox.setToolTip("Prioritizes Natural Law principles in conflict resolution and final document authority.")
        self.natural_law_final_checkbox.setChecked(self.settings.get("natural_law_final_jurisdiction_enabled", False))
        self.natural_law_final_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"natural_law_final_jurisdiction_enabled": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.natural_law_final_checkbox, 2, 0)
        doc_clause_layout.addWidget(QLabel("Ensures Natural Law is the ultimate authority in document logic. (Placeholder)"), 2, 1)

        # Enforce ClauseConformer Across All Document Types
        self.enforce_conformer_checkbox = QCheckBox("Enforce ClauseConformer Across All Document Types")
        self.enforce_conformer_checkbox.setToolTip("Automatically runs ClauseConformer checks during document operations.")
        self.enforce_conformer_checkbox.setChecked(self.settings.get("enforce_clauseconformer_all_docs", True))
        self.enforce_conformer_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"enforce_clauseconformer_all_docs": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.enforce_conformer_checkbox, 3, 0)
        doc_clause_layout.addWidget(QLabel("Activates automatic conformance checks by ClauseConformer agent."), 3, 1)

        # Permit Live Clause Editing from Document Viewer
        self.live_clause_editing_checkbox = QCheckBox("Permit Live Clause Editing from Document Viewer")
        self.live_clause_editing_checkbox.setToolTip("Allows direct editing of clause text within the main document view, rather than only via dialog.")
        self.live_clause_editing_checkbox.setChecked(self.settings.get("permit_live_clause_editing", False))
        self.live_clause_editing_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"permit_live_clause_editing": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.live_clause_editing_checkbox, 4, 0)
        doc_clause_layout.addWidget(QLabel("Enables in-place editing of clauses in the list. (Placeholder)"), 4, 1)

        # Auto-Validate All Output Against Codex Memory - New
        self.auto_validate_codex_checkbox = QCheckBox("Auto-Validate All Output Against Codex Memory")
        self.auto_validate_codex_checkbox.setToolTip("Performs validation against stored Codex data before finalizing output.")
        self.auto_validate_codex_checkbox.setChecked(self.settings.get("auto_validate_codex_memory", True))
        self.auto_validate_codex_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"auto_validate_codex_memory": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.auto_validate_codex_checkbox, 5, 0)
        doc_clause_layout.addWidget(QLabel("Ensures output consistency with Codex memory. (Placeholder)"), 5, 1)

        # Allow Clause Conversion from Ecclesiastical → Lex Triad - New
        self.allow_clause_conversion_checkbox = QCheckBox("Allow Clause Conversion (Ecclesiastical → Lex Triad)")
        self.allow_clause_conversion_checkbox.setToolTip("Enables AI tools to convert clauses from ecclesiastical or statutory forms.")
        self.allow_clause_conversion_checkbox.setChecked(self.settings.get("allow_clause_conversion", True))
        self.allow_clause_conversion_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"allow_clause_conversion": state == Qt.CheckState.Checked.value})
        )
        doc_clause_layout.addWidget(self.allow_clause_conversion_checkbox, 6, 0)
        doc_clause_layout.addWidget(QLabel("Permits AI-assisted conversion of clauses to Lex Triad. (Placeholder)"), 6, 1)

        doc_clause_group.setLayout(doc_clause_layout)
        settings_layout.addWidget(doc_clause_group)

        # --- Codex Vault & Data Management Group ---
        codex_vault_group = QGroupBox("Codex Vault & Data Management")
        codex_vault_layout = QGridLayout()

        # Enable Local Archive of Source Uploads (Codex Vault) - New
        self.local_archive_uploads_checkbox = QCheckBox("Enable Local Archive of Source Uploads (Codex Vault)")
        self.local_archive_uploads_checkbox.setToolTip("Saves copies of all user-uploaded source documents within the Codex Vault.")
        self.local_archive_uploads_checkbox.setChecked(self.settings.get("local_archive_source_uploads", True))
        self.local_archive_uploads_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"local_archive_source_uploads": state == Qt.CheckState.Checked.value})
        )
        codex_vault_layout.addWidget(self.local_archive_uploads_checkbox, 0, 0)
        codex_vault_layout.addWidget(QLabel("Keeps a local copy of all uploaded source files."), 0, 1)

        # Auto-Save settings
        self.enable_auto_save_checkbox = QCheckBox("Enable Auto-Save")
        self.enable_auto_save_checkbox.setToolTip("Automatically saves the active document at regular intervals.")
        self.enable_auto_save_checkbox.setChecked(self.settings.get("auto_save_enabled", True))
        self.enable_auto_save_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"auto_save_enabled": state == Qt.CheckState.Checked.value})
        )
        codex_vault_layout.addWidget(self.enable_auto_save_checkbox, 1, 0)

        self.auto_save_interval_label = QLabel("Auto-Save Interval (minutes):")
        codex_vault_layout.addWidget(self.auto_save_interval_label, 2, 0)
        self.auto_save_interval_spinbox = QSpinBox()
        self.auto_save_interval_spinbox.setMinimum(1)
        self.auto_save_interval_spinbox.setMaximum(60) # Max 1 hour interval
        self.auto_save_interval_spinbox.setValue(self.settings.get("auto_save_interval_minutes", 5))
        self.auto_save_interval_spinbox.valueChanged.connect(
            lambda value: self.settings.update({"auto_save_interval_minutes": value})
        )
        codex_vault_layout.addWidget(self.auto_save_interval_spinbox, 2, 1)


        codex_vault_group.setLayout(codex_vault_layout)
        settings_layout.addWidget(codex_vault_group)

        settings_layout.addStretch()
        main_layout.addWidget(scroll_area)

        # --- Save Button ---
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self._save_settings)
        main_layout.addWidget(self.save_settings_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_setting(self, key: str):
        """Public method to get a specific setting's value."""
        return self.settings.get(key)

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    settings_view = SettingsView()
    settings_view.setWindowTitle("Test Settings View")
    settings_view.setGeometry(100,100, 700, 500)
    settings_view.show()
    sys.exit(app.exec())
