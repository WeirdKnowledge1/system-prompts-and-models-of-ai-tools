from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QTextEdit, QComboBox, QDialogButtonBox, QLabel)
from PyQt6.QtCore import Qt
from app.core.clause_model import Clause

class EditClauseDialog(QDialog):
    def __init__(self, clause: Clause = None, default_jurisdiction="Lex Aequies", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Clause" if clause else "Add New Clause")

        self.clause = clause if clause else Clause(text="", jurisdiction=default_jurisdiction)
        self.is_new_clause = clause is None

        self._setup_ui()
        if not self.is_new_clause:
            self._load_clause_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Clause ID (read-only, shown if editing)
        self.id_label = QLabel("Clause ID:")
        self.id_value_label = QLabel(self.clause.id if not self.is_new_clause else "(New Clause - ID will be auto-generated)")
        form_layout.addRow(self.id_label, self.id_value_label)

        # Clause Text
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter the full text of the clause...")
        form_layout.addRow(QLabel("Clause Text:"), self.text_edit)

        # Jurisdiction
        self.jurisdiction_combo = QComboBox()
        self.jurisdictions = ["Lex Aequies", "Lex Postalis", "Lex Naturalis", "Civil", "Ecclesiastical", "Unknown"] # Extended list
        self.jurisdiction_combo.addItems(self.jurisdictions)
        form_layout.addRow(QLabel("Jurisdiction:"), self.jurisdiction_combo)

        # Origin
        self.origin_edit = QLineEdit()
        self.origin_edit.setPlaceholderText("e.g., User Input, Template: Trust V1, Uploaded: contract.pdf")
        form_layout.addRow(QLabel("Origin:"), self.origin_edit)

        # Clause Purpose/Type (Human-centered enhancement)
        self.purpose_type_edit = QLineEdit()
        self.purpose_type_edit.setPlaceholderText("e.g., Ownership, Notice, Remedy, Appointment of Trustee")
        form_layout.addRow(QLabel("Purpose/Type (Optional):"), self.purpose_type_edit)

        main_layout.addLayout(form_layout)

        # Dialog Buttons (Save, Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setMinimumWidth(500) # Set a reasonable minimum width
        self.setMinimumHeight(400)


    def _load_clause_data(self):
        """Loads existing clause data into the dialog fields."""
        if self.clause:
            self.text_edit.setPlainText(self.clause.text)
            if self.clause.jurisdiction in self.jurisdictions:
                self.jurisdiction_combo.setCurrentText(self.clause.jurisdiction)
            else: # If jurisdiction is not in standard list, add it and select
                self.jurisdiction_combo.addItem(self.clause.jurisdiction)
                self.jurisdiction_combo.setCurrentText(self.clause.jurisdiction)
            self.origin_edit.setText(self.clause.origin)
            self.purpose_type_edit.setText(self.clause.metadata.get("purpose_type", ""))

    def _apply_changes_to_clause(self):
        """Applies changes from dialog fields back to the self.clause object."""
        self.clause.text = self.text_edit.toPlainText().strip()
        self.clause.jurisdiction = self.jurisdiction_combo.currentText()
        self.clause.origin = self.origin_edit.text().strip()

        purpose_type = self.purpose_type_edit.text().strip()
        if purpose_type:
            self.clause.metadata["purpose_type"] = purpose_type
        elif "purpose_type" in self.clause.metadata:
            del self.clause.metadata["purpose_type"] # Remove if blanked out

        if self.is_new_clause and not self.clause.id.startswith("CL-"): # Ensure new clauses get a default ID if not set
            self.clause.id = f"CL-{uuid.uuid4().hex[:8].upper()}" # Should be handled by Clause constructor, but as a fallback.
                                                                # Clause model already handles ID generation.

    def accept(self):
        """Called when Save is clicked."""
        if not self.text_edit.toPlainText().strip():
            from PyQt6.QtWidgets import QMessageBox # Local import to avoid circularity at module level if any
            QMessageBox.warning(self, "Input Error", "Clause text cannot be empty.")
            return # Don't close dialog

        self._apply_changes_to_clause()
        super().accept() # Close the dialog with QDialog.Accepted result

    def get_clause(self) -> Clause:
        """Returns the clause object (new or updated)."""
        return self.clause

if __name__ == '__main__':
    # Example Usage
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test adding a new clause
    print("Testing Add New Clause Dialog:")
    add_dialog = EditClauseDialog(default_jurisdiction="Lex Postalis")
    if add_dialog.exec():
        new_clause = add_dialog.get_clause()
        print("New Clause Added:")
        print(new_clause.to_dict())
    else:
        print("Add new clause cancelled.")

    print("\n" + "-"*30 + "\n")

    # Test editing an existing clause
    print("Testing Edit Existing Clause Dialog:")
    existing_clause_data = {
        "id": "CL-TRUST001",
        "text": "This is the original text of the trust's primary declaration.",
        "jurisdiction": "Lex Aequies",
        "origin": "Initial Draft v0.9",
        "metadata": {"purpose_type": "Declaration of Trust"}
    }
    existing_clause = Clause.from_dict(existing_clause_data)

    edit_dialog = EditClauseDialog(clause=existing_clause)
    if edit_dialog.exec():
        updated_clause = edit_dialog.get_clause()
        print("Clause Updated:")
        print(updated_clause.to_dict())
        assert updated_clause.id == "CL-TRUST001" # ID should not change on edit
    else:
        print("Edit existing clause cancelled.")

    sys.exit(app.exec())
