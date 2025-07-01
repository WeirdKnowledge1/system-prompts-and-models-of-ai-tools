from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QTextEdit, QComboBox, QDialogButtonBox, QLabel, QMessageBox,
                             QDateTimeEdit) # Make sure QDateTimeEdit is imported
from PyQt6.QtCore import Qt, QDateTime # Make sure QDateTime is imported

class AddLedgerEntryDialog(QDialog):
    def __init__(self, entry_data_to_edit: dict = None, default_jurisdiction="Lex Aequies", parent=None):
        super().__init__(parent)

        self.entry_data_to_edit = entry_data_to_edit
        self.is_editing = self.entry_data_to_edit is not None

        if self.is_editing:
            self.setWindowTitle("Edit Ledger Entry")
        else:
            self.setWindowTitle("Add New Ledger Entry")

        self.output_entry_data = {}
        self.default_jurisdiction = default_jurisdiction

        self._setup_ui() # Calls the full UI setup
        if self.is_editing:
            self._load_entry_data_for_editing()
        else: # For new entries, set default timestamp and status
            self.timestamp_edit.setDateTime(QDateTime.currentDateTime())
            self.status_combo.setCurrentText("Active")
            self.jurisdiction_combo.setCurrentText(self.default_jurisdiction)


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        if self.is_editing and self.entry_data_to_edit.get("entry_id"):
            self.id_display_label = QLabel(self.entry_data_to_edit["entry_id"])
            form_layout.addRow(QLabel("Entry ID:"), self.id_display_label)

        self.title_edit = QLineEdit()
        form_layout.addRow(QLabel("Title:"), self.title_edit)

        self.entry_type_combo = QComboBox()
        self.entry_types = ["Transaction", "Notice Sent", "Notice Received", "Filing", "Clause Reference", "Amendment", "Trustee Action", "System Event", "User Note", "Other"]
        self.entry_type_combo.addItems(self.entry_types)
        form_layout.addRow(QLabel("Entry Type:"), self.entry_type_combo)

        self.jurisdiction_combo = QComboBox()
        self.jurisdictions = ["Lex Aequies", "Lex Postalis", "Lex Naturalis", "Civil", "Ecclesiastical", "N/A"]
        self.jurisdiction_combo.addItems(self.jurisdictions)
        form_layout.addRow(QLabel("Jurisdiction Tag:"), self.jurisdiction_combo)

        self.notes_edit = QTextEdit()
        form_layout.addRow(QLabel("Notes:"), self.notes_edit)

        self.clause_ids_edit = QLineEdit()
        self.clause_ids_edit.setPlaceholderText("Optional: e.g., CL-123, CL-456")
        form_layout.addRow(QLabel("Associated Clause IDs (CSV):"), self.clause_ids_edit)

        self.status_combo = QComboBox()
        self.statuses = ["Active", "Archived", "Under Review", "Completed"]
        self.status_combo.addItems(self.statuses)
        form_layout.addRow(QLabel("Status:"), self.status_combo)

        # New fields for Step 2 of Phase 6
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated, e.g., Land Use, Notice Served")
        form_layout.addRow(QLabel("Category Tags (CSV):"), self.tags_edit)

        self.timestamp_edit = QDateTimeEdit()
        self.timestamp_edit.setCalendarPopup(True)
        self.timestamp_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        form_layout.addRow(QLabel("Timestamp:"), self.timestamp_edit)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Save Entry" if self.is_editing else "Add Entry")
        self.button_box.accepted.connect(self.accept_entry)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setMinimumWidth(450)
        self.setMinimumHeight(400) # Increased height for new fields

    def _load_entry_data_for_editing(self):
        if self.entry_data_to_edit:
            self.title_edit.setText(self.entry_data_to_edit.get("title", ""))

            current_type = self.entry_data_to_edit.get("entry_type", self.entry_types[0])
            if current_type in self.entry_types: self.entry_type_combo.setCurrentText(current_type)
            else: self.entry_type_combo.addItem(current_type); self.entry_type_combo.setCurrentText(current_type)

            current_juris = self.entry_data_to_edit.get("jurisdiction_tag", self.default_jurisdiction)
            if current_juris in self.jurisdictions: self.jurisdiction_combo.setCurrentText(current_juris)
            else: self.jurisdiction_combo.addItem(current_juris); self.jurisdiction_combo.setCurrentText(current_juris)

            self.notes_edit.setPlainText(self.entry_data_to_edit.get("notes", ""))
            self.clause_ids_edit.setText(", ".join(self.entry_data_to_edit.get("associated_clause_ids", [])))

            current_status = self.entry_data_to_edit.get("status", self.statuses[0])
            if current_status in self.statuses: self.status_combo.setCurrentText(current_status)
            else: self.status_combo.addItem(current_status); self.status_combo.setCurrentText(current_status)

            self.tags_edit.setText(", ".join(self.entry_data_to_edit.get("category_tags", [])))

            timestamp_str = self.entry_data_to_edit.get("timestamp", QDateTime.currentDateTime().toString(Qt.DateFormat.ISODateWithMs))
            try:
                # Ensure timestamp_str is in a format QDateTime can parse, or it's already a QDateTime
                dt_object = QDateTime.fromString(timestamp_str, Qt.DateFormat.ISODateWithMs)
                if not dt_object.isValid(): # Try another common format if first fails
                    dt_object = QDateTime.fromString(timestamp_str, "yyyy-MM-dd HH:mm:ss")
                if not dt_object.isValid(): # Fallback
                     dt_object = QDateTime.fromString(timestamp_str.split('.')[0], Qt.DateFormat.ISODate) # Try without ms

                self.timestamp_edit.setDateTime(dt_object if dt_object.isValid() else QDateTime.currentDateTime())

            except Exception: # Broad exception for parsing issues
                 self.timestamp_edit.setDateTime(QDateTime.currentDateTime())


    def accept_entry(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return

        self.output_entry_data = {
            "title": title,
            "entry_type": self.entry_type_combo.currentText(),
            "jurisdiction_tag": self.jurisdiction_combo.currentText(),
            "notes": self.notes_edit.toPlainText().strip(),
            "associated_clause_ids": [cid.strip() for cid in self.clause_ids_edit.text().split(',') if cid.strip()],
            "status": self.status_combo.currentText(),
            "category_tags": [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()],
            "timestamp": self.timestamp_edit.dateTime().toString(Qt.DateFormat.ISODateWithMs) # Store as ISO string
        }

        if self.is_editing:
            self.output_entry_data["entry_id"] = self.entry_data_to_edit.get("entry_id")
            # Timestamp is now user-editable, so we use the value from timestamp_edit
            # If we wanted to preserve original creation timestamp and have a last_modified, that'd be different.
        super().accept()

    def get_entry_data(self) -> dict:
        return self.output_entry_data

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    # from app.core.ledger_models import LedgerEntry # For testing edit mode

    app = QApplication(sys.argv)

    print("Testing Add New Ledger Entry Dialog:")
    add_dialog = AddLedgerEntryDialog(default_jurisdiction="Lex Postalis")
    if add_dialog.exec():
        print("New Entry Data:", add_dialog.get_entry_data())
    else:
        print("Add new entry cancelled.")

    print("\n" + "-"*30 + "\n")

    # For testing edit, we'd need a LedgerEntry instance or a dict matching its structure
    # from app.core.ledger_models import LedgerEntry # Ensure this can be imported for test
    # For now, let's create a sample dict for editing
    sample_entry_for_edit = {
        "entry_id": "LENT-EDITTEST",
        "timestamp": QDateTime.currentDateTime().addDays(-1).toString(Qt.DateFormat.ISODateWithMs),
        "title": "Original Test Entry for Edit",
        "entry_type": "Filing",
        "jurisdiction_tag": "Lex Aequies",
        "notes": "This is an original note to be edited.",
        "associated_clause_ids": ["CL-A1", "CL-B2"],
        "status": "Active",
        "category_tags": ["Urgent", "Review"]
    }

    print("Testing Edit Existing Ledger Entry Dialog:")
    edit_dialog = AddLedgerEntryDialog(entry_data_to_edit=sample_entry_for_edit)
    if edit_dialog.exec():
        updated_data = edit_dialog.get_entry_data()
        print("Updated Entry Data:", updated_data)
        assert updated_data["entry_id"] == sample_entry_for_edit["entry_id"]
    else:
        print("Edit existing entry cancelled.")

    sys.exit(app.exec())
