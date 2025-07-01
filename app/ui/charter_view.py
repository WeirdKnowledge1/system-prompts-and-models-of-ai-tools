from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox)
from PyQt6.QtCore import Qt
import json
import os

from app.core.document_models import MichaudFamilyPostalCharter
from app.utils.constants import CODEX_VAULT_DIR

class CharterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudFamilyPostalCharter(name="Untitled Michaud Family Postal Charter")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Document Info Group ---
        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()

        self.name_label = QLabel("Charter Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter the name of this Postal Charter document")
        self.name_input.textChanged.connect(lambda text: setattr(self.document, 'name', text))
        doc_info_layout.addWidget(self.name_label, 0, 0)
        doc_info_layout.addWidget(self.name_input, 0, 1)

        self.id_label = QLabel("Document ID:")
        self.id_display = QLabel(self.document.id) # Display only
        doc_info_layout.addWidget(self.id_label, 1, 0)
        doc_info_layout.addWidget(self.id_display, 1, 1)

        self.jurisdiction_label = QLabel("Jurisdiction:")
        self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        self.jurisdiction_input.textChanged.connect(lambda text: setattr(self.document, 'jurisdiction', text))
        doc_info_layout.addWidget(self.jurisdiction_label, 2, 0)
        doc_info_layout.addWidget(self.jurisdiction_input, 2, 1)

        doc_info_group.setLayout(doc_info_layout)
        main_layout.addWidget(doc_info_group)

        # --- Charter Details Group ---
        charter_details_group = QGroupBox("Postal Charter Specifics")
        charter_details_layout = QVBoxLayout()

        self.upu_format_label = QLabel("UPU Recognized Format Details:")
        self.upu_format_input = QTextEdit()
        charter_details_layout.addWidget(self.upu_format_label)
        charter_details_layout.addWidget(self.upu_format_input)

        self.global_tracking_label = QLabel("Global UPU Tracking Number Fields:")
        self.global_tracking_input = QTextEdit() # Was QLineEdit, QTextEdit for more space
        charter_details_layout.addWidget(self.global_tracking_label)
        charter_details_layout.addWidget(self.global_tracking_input)

        self.canada_post_label = QLabel("Canada Post Format Compliance Details:")
        self.canada_post_input = QTextEdit()
        charter_details_layout.addWidget(self.canada_post_label)
        charter_details_layout.addWidget(self.canada_post_input)

        self.usps_label = QLabel("USPS Format Compliance Details:")
        self.usps_input = QTextEdit()
        charter_details_layout.addWidget(self.usps_label)
        charter_details_layout.addWidget(self.usps_input)

        self.vienna_ref_label = QLabel("Vienna Convention Reference Details:")
        self.vienna_ref_input = QTextEdit()
        charter_details_layout.addWidget(self.vienna_ref_label)
        charter_details_layout.addWidget(self.vienna_ref_input)

        self.postal_treaty_label = QLabel("Postal Treaty Law Reference Details:")
        self.postal_treaty_input = QTextEdit()
        charter_details_layout.addWidget(self.postal_treaty_label)
        charter_details_layout.addWidget(self.postal_treaty_input)

        # Family Trust Reference (Placeholder for now - could be a file picker or ID input)
        self.family_trust_ref_label = QLabel("Family Trust Reference (ID/Path):")
        self.family_trust_ref_input = QLineEdit()
        self.family_trust_ref_input.setPlaceholderText("Enter ID or path to the related Family Trust document")
        charter_details_layout.addWidget(self.family_trust_ref_label)
        charter_details_layout.addWidget(self.family_trust_ref_input)

        charter_details_group.setLayout(charter_details_layout)
        main_layout.addWidget(charter_details_group)

        # --- Clauses Group ---
        clauses_group = QGroupBox("Clauses")
        clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget()
        self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)

        # --- Selected Clause Details Panel ---
        self.selected_clause_details_group = QGroupBox("Selected Clause Details")
        selected_clause_layout = QGridLayout()

        self.sel_clause_id_label = QLabel("ID:")
        self.sel_clause_id_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_id_label, 0, 0)
        selected_clause_layout.addWidget(self.sel_clause_id_value, 0, 1)

        self.sel_clause_jurisdiction_label = QLabel("Jurisdiction:")
        self.sel_clause_jurisdiction_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_jurisdiction_label, 1, 0)
        selected_clause_layout.addWidget(self.sel_clause_jurisdiction_value, 1, 1)

        self.sel_clause_origin_label = QLabel("Origin:")
        self.sel_clause_origin_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_origin_label, 2, 0)
        selected_clause_layout.addWidget(self.sel_clause_origin_value, 2, 1)

        self.sel_clause_text_label = QLabel("Text:")
        self.sel_clause_text_value = QTextEdit()
        self.sel_clause_text_value.setReadOnly(True)
        selected_clause_layout.addWidget(self.sel_clause_text_label, 3, 0, 1, 2)
        selected_clause_layout.addWidget(self.sel_clause_text_value, 4, 0, 1, 2)

        self.edit_selected_clause_button = QPushButton("Edit Selected Clause")
        self.edit_selected_clause_button.setEnabled(False)
        self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)
        selected_clause_layout.addWidget(self.edit_selected_clause_button, 5, 0, 1, 2)

        self.selected_clause_details_group.setLayout(selected_clause_layout)
        self.selected_clause_details_group.setVisible(False)
        clauses_layout.addWidget(self.selected_clause_details_group)

        # --- Clause Action Buttons ---
        clause_action_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add New Clause")
        self.add_clause_button.clicked.connect(self.add_clause)
        self.remove_clause_button = QPushButton("Remove Selected Clause")
        self.remove_clause_button.setEnabled(False)
        self.remove_clause_button.clicked.connect(self.remove_selected_clause)

        clause_action_buttons_layout.addWidget(self.add_clause_button)
        clause_action_buttons_layout.addWidget(self.remove_clause_button)
        clauses_layout.addLayout(clause_action_buttons_layout)

        clauses_group.setLayout(clauses_layout)
        main_layout.addWidget(clauses_group)

        # --- File Operations ---
        file_ops_layout = QHBoxLayout()
        self.new_button = QPushButton("New Charter Document")
        self.new_button.clicked.connect(self.new_document)
        self.save_button = QPushButton("Save Charter")
        self.save_button.clicked.connect(self.save_document)
        self.load_button = QPushButton("Load Charter")
        self.load_button.clicked.connect(self.load_document)

        file_ops_layout.addWidget(self.new_button)
        file_ops_layout.addWidget(self.save_button)
        file_ops_layout.addWidget(self.load_button)
        main_layout.addLayout(file_ops_layout)

        main_layout.addStretch()
        self.load_document_data_into_ui()

    def _collect_data_from_ui(self):
        self.document.name = self.name_input.text()
        self.document.jurisdiction = self.jurisdiction_input.text()
        self.document.upu_recognized_format_details = self.upu_format_input.toPlainText()
        self.document.global_upu_tracking_number_fields = self.global_tracking_input.toPlainText()
        self.document.canada_post_format_compliance_details = self.canada_post_input.toPlainText()
        self.document.usps_format_compliance_details = self.usps_input.toPlainText()
        self.document.vienna_convention_reference_details = self.vienna_ref_input.toPlainText()
        self.document.postal_treaty_law_reference_details = self.postal_treaty_input.toPlainText()
        self.document.family_trust_ref = self.family_trust_ref_input.text()

    def load_document_data_into_ui(self):
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.upu_format_input.setPlainText(self.document.upu_recognized_format_details)
        self.global_tracking_input.setPlainText(self.document.global_upu_tracking_number_fields)
        self.canada_post_input.setPlainText(self.document.canada_post_format_compliance_details)
        self.usps_input.setPlainText(self.document.usps_format_compliance_details)
        self.vienna_ref_input.setPlainText(self.document.vienna_convention_reference_details)
        self.postal_treaty_input.setPlainText(self.document.postal_treaty_law_reference_details)
        self.family_trust_ref_input.setText(self.document.family_trust_ref or "")

        self.clauses_list_widget.clear()
        for clause_obj in self.document.clauses: # Now Clause objects
            self.clauses_list_widget.addItem(str(clause_obj)) # Use Clause.__str__

    def new_document(self):
        self.document = MichaudFamilyPostalCharter(name="Untitled Michaud Family Postal Charter")
        self.current_document_path = None
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Postal Charter document initialized.")

    def add_clause(self):
        clause_text = f"New sample clause for Charter {len(self.document.clauses) + 1}"
        new_clause = self.document.add_clause(
            clause_text=clause_text,
            jurisdiction=self.document.jurisdiction, # Default to doc's jurisdiction
            origin="User Input via Basic Add"
        )
        self.clauses_list_widget.addItem(str(new_clause))
        QMessageBox.information(self, "Clause Added", f"Clause '{new_clause.id}' added.")

    def display_selected_clause_details(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            current_row = self.clauses_list_widget.currentRow()
            if 0 <= current_row < len(self.document.clauses):
                clause_obj = self.document.clauses[current_row]
                self.sel_clause_id_value.setText(clause_obj.id)
                self.sel_clause_jurisdiction_value.setText(clause_obj.jurisdiction)
                self.sel_clause_origin_value.setText(clause_obj.origin)
                self.sel_clause_text_value.setPlainText(clause_obj.text)
                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True)
                self.remove_clause_button.setEnabled(True)
            else:
                self.selected_clause_details_group.setVisible(False)
                self.edit_selected_clause_button.setEnabled(False)
                self.remove_clause_button.setEnabled(False)
        else:
            self.selected_clause_details_group.setVisible(False)
            self.edit_selected_clause_button.setEnabled(False)
            self.remove_clause_button.setEnabled(False)

    def edit_selected_clause(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row >= 0:
            clause_obj = self.document.clauses[current_row]
            QMessageBox.information(self, "Edit Clause", f"Editing clause: {clause_obj.id} (Placeholder).")
            # Actual edit dialog and logic to be implemented later
        else:
            QMessageBox.warning(self, "Edit Clause", "No clause selected.")

    def remove_selected_clause(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row >= 0:
            clause_obj = self.document.clauses[current_row]
            reply = QMessageBox.question(self, "Remove Clause",
                                         f"Are you sure you want to remove clause: {clause_obj.id}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.document.clauses.pop(current_row)
                self.clauses_list_widget.takeItem(current_row)
                self.display_selected_clause_details() # Clear/update details panel
                QMessageBox.information(self, "Clause Removed", f"Clause {clause_obj.id} removed.")
        else:
            QMessageBox.warning(self, "Remove Clause", "No clause selected.")

    def save_document(self):
        self._collect_data_from_ui() # Ensure document object is up-to-date with UI text fields

        if not self._validate_document_basic():
            return

        if not self.current_document_path:
            charter_dir = os.path.join(CODEX_VAULT_DIR, "charters")
            safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
            safe_filename = safe_filename.replace(' ', '_') + ".mpea_charter"

            filePath, _ = QFileDialog.getSaveFileName(
                self,
                "Save Postal Charter Document",
                os.path.join(charter_dir, safe_filename),
                "Michaud Postal Equity App Charter Files (*.mpea_charter);;All Files (*)"
            )
            if not filePath:
                return
            self.current_document_path = filePath

        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)
            QMessageBox.information(self, "Save Successful", f"Postal Charter document saved to\n{self.current_document_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save document: {e}")
            self.current_document_path = None

    def load_document(self):
        charter_dir = os.path.join(CODEX_VAULT_DIR, "charters")
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Postal Charter Document",
            charter_dir,
            "Michaud Postal Equity App Charter Files (*.mpea_charter);;All Files (*)"
        )
        if not filePath:
            return

        try:
            with open(filePath, 'r') as f:
                doc_data = json.load(f)
            self.document = MichaudFamilyPostalCharter.from_dict(doc_data)
            self.current_document_path = filePath
            self.load_document_data_into_ui()
            QMessageBox.information(self, "Load Successful", f"Postal Charter document loaded from\n{filePath}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load document: {e}")

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    charter_view = CharterView()
    charter_view.setWindowTitle("Test Michaud Family Postal Charter View")
    charter_view.setGeometry(100,100, 800, 700)
    charter_view.show()
    sys.exit(app.exec())

    def _validate_document_basic(self) -> bool:
        """Performs basic validation on the document before saving."""
        self._collect_data_from_ui() # Ensure self.document is up-to-date

        errors = []
        if not self.document.name.strip():
            errors.append("Charter Name cannot be empty.")
        # Example of another required field for Charters, can be adjusted
        if not self.document.upu_recognized_format_details.strip():
            errors.append("UPU Recognized Format Details cannot be empty.")

        # Add more checks as needed for other critical fields.

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return False
        return True
