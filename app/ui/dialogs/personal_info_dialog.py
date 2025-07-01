from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QLineEdit, QPushButton, QFormLayout, QMessageBox,
                             QDialogButtonBox, QGroupBox, QApplication) # Added QApplication for __main__
from PyQt6.QtCore import Qt
import json
import os
import uuid

PROFILES_FILE_PATH = os.path.join("data", "personal_profiles.json")

class PersonalInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Personal Information Manager")
        self.setMinimumSize(700, 500)

        self.profiles = self._load_profiles()
        self.current_profile_id = None # To track which profile is being edited

        self._setup_ui()
        self._populate_profiles_list()

    def _load_profiles(self) -> list[dict]:
        if not os.path.exists(PROFILES_FILE_PATH):
            return []
        try:
            with open(PROFILES_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading profiles: {e}. Starting with an empty list.")
            return []

    def _save_profiles(self):
        try:
            os.makedirs(os.path.dirname(PROFILES_FILE_PATH), exist_ok=True)
            with open(PROFILES_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=4)
            # QMessageBox.information(self, "Profiles Saved", "Personal information profiles saved.")
        except IOError as e:
            QMessageBox.critical(self, "Save Error", f"Could not save profiles: {e}")

    def _setup_ui(self):
        main_layout = QHBoxLayout(self) # Main layout: list on left, form on right

        # --- Left Panel: Profiles List ---
        left_panel_layout = QVBoxLayout()
        self.profiles_list_widget = QListWidget()
        self.profiles_list_widget.itemSelectionChanged.connect(self._on_profile_selected)
        left_panel_layout.addWidget(QLabel("Profiles:"))
        left_panel_layout.addWidget(self.profiles_list_widget)

        profiles_action_layout = QHBoxLayout()
        self.add_profile_button = QPushButton("Add New Profile")
        self.add_profile_button.clicked.connect(self._add_new_profile)
        self.remove_profile_button = QPushButton("Remove Selected")
        self.remove_profile_button.clicked.connect(self._remove_selected_profile)
        self.remove_profile_button.setEnabled(False)
        profiles_action_layout.addWidget(self.add_profile_button)
        profiles_action_layout.addWidget(self.remove_profile_button)
        left_panel_layout.addLayout(profiles_action_layout)

        main_layout.addLayout(left_panel_layout, 1) # Stretch factor 1 for left panel

        # --- Right Panel: Profile Edit Form ---
        self.profile_form_group = QGroupBox("Profile Details")
        self.profile_form_group.setEnabled(False) # Disabled until a profile is selected or new is added
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Full Legal Name:", self.name_edit)
        self.title_role_edit = QLineEdit()
        form_layout.addRow("Title/Role:", self.title_role_edit)
        self.address_edit = QLineEdit() # Could be QTextEdit for multi-line
        form_layout.addRow("Address:", self.address_edit)
        self.province_state_edit = QLineEdit()
        form_layout.addRow("Province/State:", self.province_state_edit)
        self.country_edit = QLineEdit()
        form_layout.addRow("Country:", self.country_edit)
        self.email_edit = QLineEdit()
        form_layout.addRow("Email:", self.email_edit)
        self.phone_edit = QLineEdit()
        form_layout.addRow("Phone:", self.phone_edit)

        self.save_profile_changes_button = QPushButton("Save Changes to Selected Profile")
        self.save_profile_changes_button.clicked.connect(self._save_current_profile_details)
        form_layout.addRow(self.save_profile_changes_button)

        self.profile_form_group.setLayout(form_layout)
        main_layout.addWidget(self.profile_form_group, 2) # Stretch factor 2 for right panel

        # --- Dialog Buttons (Save All & Close, Close) ---
        # Replacing QDialogButtonBox for more explicit control here
        bottom_button_layout = QHBoxLayout()
        self.save_and_close_button = QPushButton("Save All & Close")
        self.save_and_close_button.clicked.connect(self.accept) # accept will trigger save
        self.close_button = QPushButton("Close Without Saving All") # Or just "Close" if saving is per-profile
        self.close_button.clicked.connect(self.reject)

        # For now, saving is done on "Save All & Close" or per profile save
        # Let's make "Save Changes to Selected Profile" the primary way to save an individual profile edit
        # And "Save All & Close" will do a final save of the whole list.

        dialog_buttons = QDialogButtonBox()
        dialog_buttons.addButton(self.save_and_close_button, QDialogButtonBox.ButtonRole.AcceptRole)
        dialog_buttons.addButton(self.close_button, QDialogButtonBox.ButtonRole.RejectRole)

        # Adding to a container widget that will be part of main_layout if needed, or directly
        # We need to add this button box to the main_layout, but it's QHBoxLayout.
        # So, let's embed main_layout (QHBox) into a QVBox that also holds the dialog buttons.

        overall_layout = QVBoxLayout()
        overall_layout.addLayout(main_layout) # The QHBoxLayout with list and form
        overall_layout.addWidget(dialog_buttons)
        self.setLayout(overall_layout)


    def _populate_profiles_list(self):
        self.profiles_list_widget.clear()
        for profile in self.profiles:
            # Use name for display, store ID in item data
            item = QListWidgetItem(profile.get("name", "Unnamed Profile"))
            item.setData(Qt.ItemDataRole.UserRole, profile.get("id")) # Store ID
            self.profiles_list_widget.addItem(item)

    def _clear_form(self):
        self.name_edit.clear()
        self.title_role_edit.clear()
        self.address_edit.clear()
        self.province_state_edit.clear()
        self.country_edit.clear()
        self.email_edit.clear()
        self.phone_edit.clear()
        self.current_profile_id = None
        self.profile_form_group.setEnabled(False)
        self.remove_profile_button.setEnabled(False)


    def _on_profile_selected(self):
        selected_items = self.profiles_list_widget.selectedItems()
        if not selected_items:
            self._clear_form()
            return

        item = selected_items[0]
        profile_id = item.data(Qt.ItemDataRole.UserRole)

        profile = next((p for p in self.profiles if p.get("id") == profile_id), None)

        if profile:
            self.current_profile_id = profile_id
            self.name_edit.setText(profile.get("name", ""))
            self.title_role_edit.setText(profile.get("title_role", ""))
            self.address_edit.setText(profile.get("address", ""))
            self.province_state_edit.setText(profile.get("province_state", ""))
            self.country_edit.setText(profile.get("country", ""))
            self.email_edit.setText(profile.get("email", ""))
            self.phone_edit.setText(profile.get("phone", ""))
            self.profile_form_group.setEnabled(True)
            self.remove_profile_button.setEnabled(True)
        else:
            self._clear_form() # Should not happen if ID is valid

    def _add_new_profile(self):
        self.profiles_list_widget.clearSelection() # Deselect any item
        self._clear_form() # Clear form for new entry
        self.profile_form_group.setEnabled(True)
        self.name_edit.setFocus()
        self.current_profile_id = str(uuid.uuid4()) # Assign a new ID for a potential new profile
        # This new profile is only added to self.profiles upon saving it via _save_current_profile_details

    def _save_current_profile_details(self):
        if not self.profile_form_group.isEnabled(): # No profile selected or new not initiated
            QMessageBox.information(self, "No Profile", "Please select a profile to edit or click 'Add New Profile'.")
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Profile Name cannot be empty.")
            return

        profile_data = {
            "id": self.current_profile_id or str(uuid.uuid4()), # Ensure ID exists
            "name": name,
            "title_role": self.title_role_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "province_state": self.province_state_edit.text().strip(),
            "country": self.country_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
        }

        # Check if it's an existing profile to update or a new one to add
        existing_profile_index = -1
        for i, p in enumerate(self.profiles):
            if p.get("id") == self.current_profile_id:
                existing_profile_index = i
                break

        if existing_profile_index != -1: # Update existing
            self.profiles[existing_profile_index] = profile_data
            # Update list widget item text if name changed
            list_item = self.profiles_list_widget.item(existing_profile_index) # This assumes order is maintained
            if list_item: list_item.setText(name) # This might not be robust if list isn't perfectly synced.
                                                # Better to repopulate or find item by ID.
                                                # For now, let's repopulate for simplicity after a save.
        else: # Add new profile
            self.profiles.append(profile_data)
            # Add to list widget (or repopulate)
            # item = QListWidgetItem(name)
            # item.setData(Qt.ItemDataRole.UserRole, profile_data["id"])
            # self.profiles_list_widget.addItem(item)
            # self.profiles_list_widget.setCurrentItem(item) # Select the new item

        self._populate_profiles_list() # Repopulate to ensure sync and correct selection
        # Reselect the saved item
        for i in range(self.profiles_list_widget.count()):
            item = self.profiles_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == profile_data["id"]:
                item.setSelected(True)
                self.profiles_list_widget.scrollToItem(item)
                break

        QMessageBox.information(self, "Profile Saved", f"Profile '{name}' saved.")
        # self._save_profiles() # Optionally save immediately to disk after each profile save

    def _remove_selected_profile(self):
        selected_items = self.profiles_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No profile selected to remove.")
            return

        item = selected_items[0]
        profile_id_to_remove = item.data(Qt.ItemDataRole.UserRole)
        profile_name = item.text()

        reply = QMessageBox.question(self, "Remove Profile",
                                     f"Are you sure you want to remove profile: {profile_name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.profiles = [p for p in self.profiles if p.get("id") != profile_id_to_remove]
            self._populate_profiles_list() # Refresh list
            self._clear_form() # Clear form as selection is gone
            QMessageBox.information(self, "Profile Removed", f"Profile '{profile_name}' removed.")
            # self._save_profiles() # Optionally save immediately

    def accept(self): # Override accept for QDialogButtonBox.AcceptRole
        self._save_current_profile_details() # Save any pending changes in the form
        self._save_profiles() # Save the entire list to disk
        super().accept()

    def reject(self): # Override reject for QDialogButtonBox.RejectRole
        # Optionally ask if user wants to save changes if any are pending before closing
        super().reject()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    dialog = PersonalInfoDialog()
    dialog.show()
    sys.exit(app.exec())
