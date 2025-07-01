from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox)
from PyQt6.QtCore import Qt
import json
import os
import datetime # Import datetime

from app.core.document_models import MichaudFamilyTrust
from app.core.clause_model import Clause
from app.ui.dialogs.edit_clause_dialog import EditClauseDialog
from app.core.agents import ClauseConformer # Import ClauseConformer
from app.utils.constants import CODEX_VAULT_DIR

class TrustView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust") # Default empty document
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Document Info Group ---
        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()

        self.name_label = QLabel("Trust Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter the name of this Trust document")
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

        # --- Parties Group ---
        parties_group = QGroupBox("Parties")
        parties_layout = QGridLayout()

        self.settlors_label = QLabel("Settlors (comma-separated):")
        self.settlors_input = QLineEdit()
        self.settlors_input.setPlaceholderText("e.g., Rene Michaud, Louise Michaud")
        parties_layout.addWidget(self.settlors_label, 0, 0)
        parties_layout.addWidget(self.settlors_input, 0, 1)

        self.trustees_label = QLabel("Trustees (comma-separated):")
        self.trustees_input = QLineEdit()
        self.trustees_input.setPlaceholderText("e.g., Rene Michaud Jr.")
        parties_layout.addWidget(self.trustees_label, 1, 0)
        parties_layout.addWidget(self.trustees_input, 1, 1)

        self.beneficiaries_label = QLabel("Beneficiaries (comma-separated):")
        self.beneficiaries_input = QLineEdit()
        self.beneficiaries_input.setPlaceholderText("e.g., Michaud Family Lineage")
        parties_layout.addWidget(self.beneficiaries_label, 2, 0)
        parties_layout.addWidget(self.beneficiaries_input, 2, 1)

        parties_group.setLayout(parties_layout)
        main_layout.addWidget(parties_group)

        # --- Details Group ---
        details_group = QGroupBox("Specific Details")
        details_layout = QVBoxLayout()

        self.land_rights_label = QLabel("Land Rights Details:")
        self.land_rights_input = QTextEdit()
        self.land_rights_input.setPlaceholderText("Describe land rights details...")
        details_layout.addWidget(self.land_rights_label)
        details_layout.addWidget(self.land_rights_input)

        self.name_control_label = QLabel("Name Control Details:")
        self.name_control_input = QTextEdit()
        self.name_control_input.setPlaceholderText("Describe name control details...")
        details_layout.addWidget(self.name_control_label)
        details_layout.addWidget(self.name_control_input)

        self.mortgage_recon_label = QLabel("Equitable Mortgage Reconciliation Details:")
        self.mortgage_recon_input = QTextEdit()
        self.mortgage_recon_input.setPlaceholderText("Describe equitable mortgage reconciliation details...")
        details_layout.addWidget(self.mortgage_recon_label)
        details_layout.addWidget(self.mortgage_recon_input)

        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)

        # --- Clauses Group ---
        clauses_group = QGroupBox("Clauses")
        clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget()
        self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)

        # --- Selected Clause Details Panel (Part IV.B) ---
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
        selected_clause_layout.addWidget(self.sel_clause_text_label, 3, 0)
        selected_clause_layout.addWidget(self.sel_clause_text_value, 4, 0, 1, 2) # Span 2 columns for text area

        self.sel_clause_purpose_label = QLabel("Purpose/Type:")
        self.sel_clause_purpose_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_purpose_label, 5, 0)
        selected_clause_layout.addWidget(self.sel_clause_purpose_value, 5, 1)

        self.sel_clause_created_label = QLabel("Created:")
        self.sel_clause_created_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_created_label, 6, 0)
        selected_clause_layout.addWidget(self.sel_clause_created_value, 6, 1)

        self.sel_clause_modified_label = QLabel("Modified:")
        self.sel_clause_modified_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_modified_label, 7, 0)
        selected_clause_layout.addWidget(self.sel_clause_modified_value, 7, 1)

        self.sel_clause_version_label = QLabel("Version:")
        self.sel_clause_version_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_version_label, 8, 0)
        selected_clause_layout.addWidget(self.sel_clause_version_value, 8, 1)

        buttons_sel_clause_layout = QHBoxLayout()
        self.edit_selected_clause_button = QPushButton("Edit Selected Clause")
        self.edit_selected_clause_button.setEnabled(False)
        self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)

        self.view_audit_button = QPushButton("View Audit Trail")
        self.view_audit_button.setEnabled(False) # Placeholder
        self.view_audit_button.setToolTip("Functionality to be implemented in a future phase.")
        # self.view_audit_button.clicked.connect(self.view_clause_audit_trail) # Placeholder

        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button)
        buttons_sel_clause_layout.addWidget(self.view_audit_button)
        selected_clause_layout.addLayout(buttons_sel_clause_layout, 9, 0, 1, 2) # Add button layout

        self.selected_clause_details_group.setLayout(selected_clause_layout)
        self.selected_clause_details_group.setVisible(False)
        clauses_layout.addWidget(self.selected_clause_details_group)

        # --- Clause Action Buttons ---
        clause_action_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add New Clause")
        self.add_clause_button.clicked.connect(self.add_clause)

        self.remove_clause_button = QPushButton("Remove Selected Clause")
        self.remove_clause_button.setEnabled(False) # Initially disabled
        self.remove_clause_button.clicked.connect(self.remove_selected_clause)

        self.move_clause_up_button = QPushButton("Move Up")
        self.move_clause_up_button.setEnabled(False)
        self.move_clause_up_button.clicked.connect(self.move_clause_up)

        self.move_clause_down_button = QPushButton("Move Down")
        self.move_clause_down_button.setEnabled(False)
        self.move_clause_down_button.clicked.connect(self.move_clause_down)

        clause_action_buttons_layout.addWidget(self.add_clause_button)
        clause_action_buttons_layout.addWidget(self.remove_clause_button)
        clause_action_buttons_layout.addWidget(self.move_clause_up_button)
        clause_action_buttons_layout.addWidget(self.move_clause_down_button)
        clauses_layout.addLayout(clause_action_buttons_layout)

        clauses_group.setLayout(clauses_layout)
        main_layout.addWidget(clauses_group)

        # --- File Operations ---
        file_ops_layout = QHBoxLayout()
        self.new_button = QPushButton("New Trust Document")
        self.new_button.clicked.connect(self.new_document)
        self.save_button = QPushButton("Save Trust")
        self.save_button.clicked.connect(self.save_document)
        self.load_button = QPushButton("Load Trust")
        self.load_button.clicked.connect(self.load_document)

        file_ops_layout.addWidget(self.new_button)
        file_ops_layout.addWidget(self.save_button)
        file_ops_layout.addWidget(self.load_button)
        main_layout.addLayout(file_ops_layout)

        # --- Conformance Check Button ---
        self.conformance_check_button = QPushButton("Run Basic Conformance Check")
        self.conformance_check_button.clicked.connect(self.run_basic_conformance_check)
        main_layout.addWidget(self.conformance_check_button, alignment=Qt.AlignmentFlag.AlignLeft) # Align to left or center

        main_layout.addStretch() # Add stretch to push content to the top

        self.load_document_data_into_ui() # Load initial default document

    def _collect_data_from_ui(self):
        """Collects data from UI fields and updates the self.document object."""
        self.document.name = self.name_input.text()
        self.document.jurisdiction = self.jurisdiction_input.text()
        self.document.settlors = [s.strip() for s in self.settlors_input.text().split(',') if s.strip()]
        self.document.trustees = [t.strip() for t in self.trustees_input.text().split(',') if t.strip()]
        self.document.beneficiaries = [b.strip() for b in self.beneficiaries_input.text().split(',') if b.strip()]
        self.document.land_rights_details = self.land_rights_input.toPlainText()
        self.document.name_control_details = self.name_control_input.toPlainText()
        self.document.equitable_mortgage_reconciliation_details = self.mortgage_recon_input.toPlainText()
        # Clauses are managed separately by add_clause/remove_clause for now

    def load_document_data_into_ui(self):
        """Populates UI fields from the self.document object."""
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.settlors_input.setText(", ".join(self.document.settlors))
        self.trustees_input.setText(", ".join(self.document.trustees))
        self.beneficiaries_input.setText(", ".join(self.document.beneficiaries))
        self.land_rights_input.setPlainText(self.document.land_rights_details)
        self.name_control_input.setPlainText(self.document.name_control_details)
        self.mortgage_recon_input.setPlainText(self.document.equitable_mortgage_reconciliation_details)

        self.clauses_list_widget.clear()
        for clause_obj in self.document.clauses: # Now these are Clause objects
            self.clauses_list_widget.addItem(str(clause_obj)) # Use Clause.__str__ for display

    def new_document(self):
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.current_document_path = None
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Trust document initialized.")

    def add_clause(self):
        # For now, a very simple way to add clauses. Will be improved with a dialog.
        # For Phase 2, Step 8, we just ensure Clause objects are created.
        # A dialog for text, jurisdiction, origin will be added later.
        clause_text = f"New sample clause for Trust {len(self.document.clauses) + 1}"
        # clause_id will be auto-generated by Clause model if not provided
        new_clause = self.document.add_clause(
            clause_text=clause_text,
            jurisdiction=self.document.jurisdiction, # Default to doc's jurisdiction
            origin="User Input via Basic Add"
        )
        # self.clauses_list_widget.addItem(str(new_clause)) # Dialog handles UI update after success
        # QMessageBox.information(self, "Clause Added", f"Clause '{new_clause.id}' added.")
        dialog = EditClauseDialog(default_jurisdiction=self.document.jurisdiction, parent=self)
        if dialog.exec():
            new_clause = dialog.get_clause()
            self.document.clauses.append(new_clause) # Add to model
            self.clauses_list_widget.addItem(str(new_clause)) # Add to UI list
            self.clauses_list_widget.setCurrentRow(self.clauses_list_widget.count() - 1) # Select the new item
            QMessageBox.information(self, "Clause Added", f"Clause '{new_clause.id}' successfully added.")
            # Potentially update document's last_modified_date and version here or in document model

    def display_selected_clause_details(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            # Assuming the list widget items directly correspond to clauses in self.document.clauses
            # This relies on the order being consistent.
            # A more robust way would be to store the clause ID or object in the QListWidgetItem's data.
            current_row = self.clauses_list_widget.currentRow()
            if 0 <= current_row < len(self.document.clauses):
                clause_obj = self.document.clauses[current_row]

                self.sel_clause_id_value.setText(clause_obj.id)
                self.sel_clause_jurisdiction_value.setText(clause_obj.jurisdiction)
                self.sel_clause_origin_value.setText(clause_obj.origin)
                self.sel_clause_text_value.setPlainText(clause_obj.text)
                self.sel_clause_purpose_value.setText(clause_obj.metadata.get("purpose_type", "N/A"))

                # Format dates for display (optional, could also show ISO string)
                try:
                    created_date = datetime.datetime.fromisoformat(clause_obj.creation_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    created_date = clause_obj.creation_date # Show as is if not parsable
                self.sel_clause_created_value.setText(created_date)

                try:
                    modified_date = datetime.datetime.fromisoformat(clause_obj.last_modified_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    modified_date = clause_obj.last_modified_date
                self.sel_clause_modified_value.setText(modified_date)

                self.sel_clause_version_value.setText(str(clause_obj.version))

                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True)
                self.remove_clause_button.setEnabled(True)
                self.move_clause_up_button.setEnabled(current_row > 0)
                self.move_clause_down_button.setEnabled(current_row < self.clauses_list_widget.count() - 1)
            else:
                # Should not happen if selection is valid and lists are in sync
                self.selected_clause_details_group.setVisible(False)
                self.edit_selected_clause_button.setEnabled(False)
                self.remove_clause_button.setEnabled(False)
                self.move_clause_up_button.setEnabled(False)
                self.move_clause_down_button.setEnabled(False)
        else:
            self.selected_clause_details_group.setVisible(False)
            self.edit_selected_clause_button.setEnabled(False)
            self.remove_clause_button.setEnabled(False)
            self.move_clause_up_button.setEnabled(False)
            self.move_clause_down_button.setEnabled(False)

    def edit_selected_clause(self):
        # Placeholder for editing functionality
        # In a real implementation, this would open a dialog pre-filled with clause details
        # For now, just show a message.
        current_row = self.clauses_list_widget.currentRow()
        if current_row >= 0:
            clause_to_edit = self.document.clauses[current_row]

            dialog = EditClauseDialog(clause=clause_to_edit, parent=self)
            if dialog.exec():
                updated_clause = dialog.get_clause()
                self.document.clauses[current_row] = updated_clause # Update in model
                self.clauses_list_widget.item(current_row).setText(str(updated_clause)) # Update in UI list
                self.display_selected_clause_details() # Refresh details panel
                QMessageBox.information(self, "Clause Updated", f"Clause '{updated_clause.id}' successfully updated.")
                # Potentially update document's last_modified_date and version
            # else: User cancelled
        else:
            QMessageBox.warning(self, "Edit Clause", "No clause selected to edit.")

    def remove_selected_clause(self):
        # Placeholder for removing functionality
        current_row = self.clauses_list_widget.currentRow()
        if current_row >= 0:
            clause_obj = self.document.clauses[current_row]
            reply = QMessageBox.question(self, "Remove Clause",
                                         f"Are you sure you want to remove clause: {clause_obj.id}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.document.clauses.pop(current_row)
                self.clauses_list_widget.takeItem(current_row) # Remove from UI list
                self.display_selected_clause_details() # Clear/update details panel
                QMessageBox.information(self, "Clause Removed", f"Clause {clause_obj.id} removed.")
        else:
            QMessageBox.warning(self, "Remove Clause", "No clause selected to remove.")


    def save_document(self):
        self._collect_data_from_ui() # Ensure document object is up-to-date with UI text fields

        if not self._validate_document_basic():
            return

        if not self.current_document_path:
            trust_dir = os.path.join(CODEX_VAULT_DIR, "trusts")
            # Sanitize document name for use as filename
            safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
            safe_filename = safe_filename.replace(' ', '_') + ".mpea_trust" # Custom extension

            filePath, _ = QFileDialog.getSaveFileName(
                self,
                "Save Trust Document",
                os.path.join(trust_dir, safe_filename),
                "Michaud Postal Equity App Trust Files (*.mpea_trust);;All Files (*)"
            )
            if not filePath:
                return
            self.current_document_path = filePath

        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)
            QMessageBox.information(self, "Save Successful", f"Trust document saved to\n{self.current_document_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save document: {e}")
            self.current_document_path = None # Reset path if save failed

    def load_document(self):
        trust_dir = os.path.join(CODEX_VAULT_DIR, "trusts")
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Trust Document",
            trust_dir,
            "Michaud Postal Equity App Trust Files (*.mpea_trust);;All Files (*)"
        )
        if not filePath:
            return

        try:
            with open(filePath, 'r') as f:
                doc_data = json.load(f)

            # Use the from_dict method of the specific class
            self.document = MichaudFamilyTrust.from_dict(doc_data)
            self.current_document_path = filePath
            self.load_document_data_into_ui()
            QMessageBox.information(self, "Load Successful", f"Trust document loaded from\n{filePath}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load document: {e}")
            # Optionally, revert to a new blank document or keep current state
            # self.new_document()

    def _validate_document_basic(self) -> bool:
        """Performs basic validation on the document before saving."""
        self._collect_data_from_ui() # Ensure self.document is up-to-date

        errors = []
        if not self.document.name.strip():
            errors.append("Trust Name cannot be empty.")
        if not self.document.settlors:
            errors.append("Settlors must be specified.")
        if not self.document.trustees:
            errors.append("Trustees must be specified.")
        if not self.document.beneficiaries:
            errors.append("Beneficiaries must be specified.")

        # Add more checks as needed for other critical fields.
        # For example, check if jurisdiction is set, etc.

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return False
        return True


if __name__ == '__main__':
    # This is for testing the TrustView widget directly.
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    trust_view = TrustView()
    trust_view.setWindowTitle("Test Michaud Family Trust View")
    trust_view.setGeometry(100,100, 800, 600)
    trust_view.show()
    sys.exit(app.exec())

    def run_basic_conformance_check(self):
        """Runs the basic conformance check using ClauseConformer agent."""
        self._collect_data_from_ui() # Ensure document is up-to-date

        conformer = ClauseConformer() # In a real app, context might be passed
        issues = conformer.check_document_for_basic_issues(self.document)

        if issues:
            report_message = "Basic Conformance Check Found Issues:\n\n" + "\n".join(f"- {issue}" for issue in issues)
            QMessageBox.warning(self, "Conformance Issues", report_message)
        else:
            QMessageBox.information(self, "Conformance Check", "No basic conformance issues found.")

    def move_clause_up(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row > 0: # Can move up if not the first item
            # Swap in the model
            clause_to_move = self.document.clauses.pop(current_row)
            self.document.clauses.insert(current_row - 1, clause_to_move)

            # Update UI list (remove and re-insert)
            # No need to change item text, just its position
            item = self.clauses_list_widget.takeItem(current_row)
            self.clauses_list_widget.insertItem(current_row - 1, item)
            self.clauses_list_widget.setCurrentRow(current_row - 1) # Keep selection on moved item
            # itemSelectionChanged will call display_selected_clause_details and update button states

    def move_clause_down(self):
        current_row = self.clauses_list_widget.currentRow()
        # Check if current_row is valid and not the last item
        if 0 <= current_row < self.clauses_list_widget.count() - 1:
            # Swap in the model
            clause_to_move = self.document.clauses.pop(current_row)
            self.document.clauses.insert(current_row + 1, clause_to_move)

            # Update UI list
            item = self.clauses_list_widget.takeItem(current_row)
            self.clauses_list_widget.insertItem(current_row + 1, item)
            self.clauses_list_widget.setCurrentRow(current_row + 1)
            # itemSelectionChanged will call display_selected_clause_details
