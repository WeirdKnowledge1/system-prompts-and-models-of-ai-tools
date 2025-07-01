from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QCheckBox,
                             QGroupBox, QScrollArea, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
import json
import os

# Define a settings file path
SETTINGS_FILE_PATH = os.path.join("data", "app_settings.json")

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = self._load_settings()
        self._setup_ui()

    def _default_settings(self):
        """Provides default values for all settings."""
        return {
            "voice_input_enabled": False,
            "zip_module_loader_enabled": False,
            "legal_embossed_seal_enabled": False,
            "qr_proof_chain_embeds_enabled": False,
            "offline_mode_autonomous_ai_enabled": False, # From full list
            "natural_law_final_jurisdiction_enabled": False, # From full list
            "enforce_clauseconformer_all_docs": True, # From full list
            "jurisdictional_colors_enabled": True, # Part IV.B
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

        # --- Primary Command Toggles Group (Part II.A.1) ---
        primary_toggles_group = QGroupBox("System Preferences - Primary Command Toggles")
        primary_toggles_grid = QGridLayout()

        # 1. Enable/Disable Voice Input
        self.voice_input_checkbox = QCheckBox("Enable Voice Input")
        self.voice_input_checkbox.setToolTip("Enables or disables voice command input for the application.")
        self.voice_input_checkbox.setChecked(self.settings.get("voice_input_enabled", False))
        self.voice_input_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"voice_input_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.voice_input_checkbox, 0, 0)
        primary_toggles_grid.addWidget(QLabel("Allows interaction with the app using voice commands. (Placeholder)"), 0, 1)

        # 2. Enable/Disable ZIP Module Loader
        self.zip_loader_checkbox = QCheckBox("Enable ZIP Module Loader")
        self.zip_loader_checkbox.setToolTip("Allows loading of new logic modules via .zip files.")
        self.zip_loader_checkbox.setChecked(self.settings.get("zip_module_loader_enabled", False))
        self.zip_loader_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"zip_module_loader_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.zip_loader_checkbox, 1, 0)
        primary_toggles_grid.addWidget(QLabel("Permits upgrading AI logic and features via ZIP uploads. (Placeholder)"), 1, 1)

        # 3. Enable Legal Embossed Seal (QR-authenticated)
        self.embossed_seal_checkbox = QCheckBox("Enable Legal Embossed Seal (QR-authenticated)")
        self.embossed_seal_checkbox.setToolTip("Marks documents for physical embossing with a QR-authenticated seal.")
        self.embossed_seal_checkbox.setChecked(self.settings.get("legal_embossed_seal_enabled", False))
        self.embossed_seal_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"legal_embossed_seal_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.embossed_seal_checkbox, 2, 0)
        primary_toggles_grid.addWidget(QLabel("Outputs documents with markings for a QR-authenticated legal seal. (Placeholder)"), 2, 1)

        # 4. Enable QR Proof Chain Embeds
        self.qr_proof_checkbox = QCheckBox("Enable QR Proof Chain Embeds")
        self.qr_proof_checkbox.setToolTip("Embeds QR-coded chains of source proof and timestamps into documents.")
        self.qr_proof_checkbox.setChecked(self.settings.get("qr_proof_chain_embeds_enabled", False))
        self.qr_proof_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"qr_proof_chain_embeds_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.qr_proof_checkbox, 3, 0)
        primary_toggles_grid.addWidget(QLabel("Embeds traceable QR codes linking to source proofs within documents. (Placeholder)"), 3, 1)

        # Add more checkboxes here as per the full list in Part II.A.1 for future phases
        # Example for one more from the full list:
        self.offline_mode_checkbox = QCheckBox("Enable Offline Mode / Autonomous AI")
        self.offline_mode_checkbox.setToolTip("Allows the AI to operate fully offline with all features.")
        self.offline_mode_checkbox.setChecked(self.settings.get("offline_mode_autonomous_ai_enabled", False))
        self.offline_mode_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"offline_mode_autonomous_ai_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.offline_mode_checkbox, 4, 0)
        primary_toggles_grid.addWidget(QLabel("Enables full AI functionality without internet access. (Placeholder)"), 4, 1)

        # Jurisdictional Visual Feedback (Color Scheme Toggle) - Part IV.B
        self.jurisdictional_colors_checkbox = QCheckBox("Enable Jurisdictional Visual Feedback (Colors)")
        self.jurisdictional_colors_checkbox.setToolTip("Changes UI colors based on document jurisdiction (Equity, Postal, Natural Law).")
        self.jurisdictional_colors_checkbox.setChecked(self.settings.get("jurisdictional_colors_enabled", True)) # Default to True
        self.jurisdictional_colors_checkbox.stateChanged.connect(
            lambda state: self.settings.update({"jurisdictional_colors_enabled": state == Qt.CheckState.Checked.value})
        )
        primary_toggles_grid.addWidget(self.jurisdictional_colors_checkbox, 5, 0)
        primary_toggles_grid.addWidget(QLabel("Applies color schemes to document views based on their governing law."), 5, 1)

        primary_toggles_group.setLayout(primary_toggles_grid)
        settings_layout.addWidget(primary_toggles_group)

        settings_layout.addStretch() # Push settings to the top
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
