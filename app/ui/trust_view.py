from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox)
from PyQt6.QtCore import Qt
import json
import os

from app.core.document_models import MichaudFamilyTrust
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
        clauses_layout.addWidget(self.clauses_list_widget)

        clause_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add Clause")
        self.add_clause_button.clicked.connect(self.add_clause) # Placeholder for now
        self.edit_clause_button = QPushButton("Edit Clause")
        self.edit_clause_button.setEnabled(False) # Placeholder
        self.remove_clause_button = QPushButton("Remove Clause")
        self.remove_clause_button.setEnabled(False) # Placeholder

        clause_buttons_layout.addWidget(self.add_clause_button)
        clause_buttons_layout.addWidget(self.edit_clause_button)
        clause_buttons_layout.addWidget(self.remove_clause_button)
        clauses_layout.addLayout(clause_buttons_layout)
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
        for clause_dict in self.document.clauses: # In phase 1, clauses are dicts
            self.clauses_list_widget.addItem(f"ID: {clause_dict.get('id', 'N/A')} - {clause_dict.get('text', '')}")

    def new_document(self):
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.current_document_path = None
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Trust document initialized.")

    def add_clause(self):
        # For now, a very simple way to add clauses. Will be improved.
        # In a real scenario, a dialog would pop up to enter clause details.
        clause_text = f"New clause added at {len(self.document.clauses) + 1}" # Placeholder
        clause_id = f"TRUST-CLAUSE-{len(self.document.clauses) + 1:03d}"
        self.document.add_clause(clause_text, clause_id=clause_id, jurisdiction=self.document.jurisdiction)
        self.clauses_list_widget.addItem(f"ID: {clause_id} - {clause_text}")
        QMessageBox.information(self, "Clause Added", f"Clause '{clause_text}' added (placeholder).")

    def save_document(self):
        self._collect_data_from_ui() # Ensure document object is up-to-date

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
