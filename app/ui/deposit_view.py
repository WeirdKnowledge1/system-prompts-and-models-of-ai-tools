from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox, QListWidgetItem)
from PyQt6.QtCore import Qt
import json
import os

from app.core.document_models import MichaudSpecialDepositDocument
from app.utils.constants import CODEX_VAULT_DIR

class DepositView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudSpecialDepositDocument(name="Untitled Michaud Special Deposit")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Document Info Group ---
        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()

        self.name_label = QLabel("Deposit Document Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter the name of this Special Deposit document")
        self.name_input.textChanged.connect(lambda text: setattr(self.document, 'name', text))
        doc_info_layout.addWidget(self.name_label, 0, 0)
        doc_info_layout.addWidget(self.name_input, 0, 1)

        self.id_label = QLabel("Document ID:")
        self.id_display = QLabel(self.document.id)
        doc_info_layout.addWidget(self.id_label, 1, 0)
        doc_info_layout.addWidget(self.id_display, 1, 1)

        self.jurisdiction_label = QLabel("Jurisdiction:")
        self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        self.jurisdiction_input.textChanged.connect(lambda text: setattr(self.document, 'jurisdiction', text))
        doc_info_layout.addWidget(self.jurisdiction_label, 2, 0)
        doc_info_layout.addWidget(self.jurisdiction_input, 2, 1)

        doc_info_group.setLayout(doc_info_layout)
        main_layout.addWidget(doc_info_group)

        # --- Filed Documents Group ---
        filed_docs_group = QGroupBox("Filed Documents (e.g., BC, CLB)")
        filed_docs_layout = QVBoxLayout()
        self.filed_docs_list_widget = QListWidget()
        # Allow adding/removing simple text entries for filed documents for now
        filed_docs_buttons_layout = QHBoxLayout()
        self.add_filed_doc_input = QLineEdit()
        self.add_filed_doc_input.setPlaceholderText("Enter document name/ID (e.g., Birth Certificate SC123)")
        self.add_filed_doc_button = QPushButton("Add Filed Document")
        self.add_filed_doc_button.clicked.connect(self.add_filed_document_item)
        self.remove_filed_doc_button = QPushButton("Remove Selected Filed Document")
        self.remove_filed_doc_button.clicked.connect(self.remove_filed_document_item)

        filed_docs_buttons_layout.addWidget(self.add_filed_doc_input)
        filed_docs_buttons_layout.addWidget(self.add_filed_doc_button)
        filed_docs_layout.addWidget(self.filed_docs_list_widget)
        filed_docs_layout.addLayout(filed_docs_buttons_layout)
        filed_docs_layout.addWidget(self.remove_filed_doc_button)
        filed_docs_group.setLayout(filed_docs_layout)
        main_layout.addWidget(filed_docs_group)

        # --- Deposit Specifics Group ---
        deposit_specifics_group = QGroupBox("Deposit Specifics")
        deposit_specifics_layout = QVBoxLayout()

        self.source_validation_label = QLabel("Source Validation Details:")
        self.source_validation_input = QTextEdit()
        deposit_specifics_layout.addWidget(self.source_validation_label)
        deposit_specifics_layout.addWidget(self.source_validation_input)

        self.beneficiary_alignment_label = QLabel("Trust Beneficiary Alignment Notes:")
        self.beneficiary_alignment_input = QTextEdit()
        deposit_specifics_layout.addWidget(self.beneficiary_alignment_label)
        deposit_specifics_layout.addWidget(self.beneficiary_alignment_input)

        # Placeholder for signature sections
        self.agent_signature_label = QLabel("Postal Equity Agent Signature Placeholder:")
        self.agent_signature_input = QLineEdit()
        self.agent_signature_input.setPlaceholderText("e.g., Signed by Agent X on YYYY-MM-DD")
        deposit_specifics_layout.addWidget(self.agent_signature_label)
        deposit_specifics_layout.addWidget(self.agent_signature_input)

        self.notary_signature_label = QLabel("Notary Signature Placeholder:")
        self.notary_signature_input = QLineEdit()
        self.notary_signature_input.setPlaceholderText("e.g., Notarized by Notary Z on YYYY-MM-DD")
        deposit_specifics_layout.addWidget(self.notary_signature_label)
        deposit_specifics_layout.addWidget(self.notary_signature_input)

        # References
        self.family_trust_ref_label = QLabel("Family Trust Reference (ID/Path):")
        self.family_trust_ref_input = QLineEdit()
        deposit_specifics_layout.addWidget(self.family_trust_ref_label)
        deposit_specifics_layout.addWidget(self.family_trust_ref_input)

        self.postal_charter_ref_label = QLabel("Postal Charter Reference (ID/Path):")
        self.postal_charter_ref_input = QLineEdit()
        deposit_specifics_layout.addWidget(self.postal_charter_ref_label)
        deposit_specifics_layout.addWidget(self.postal_charter_ref_input)

        # Citations
        self.foreign_trustee_act_label = QLabel("Foreign Trustee Act Citation:")
        self.foreign_trustee_act_input = QLineEdit()
        deposit_specifics_layout.addWidget(self.foreign_trustee_act_label)
        deposit_specifics_layout.addWidget(self.foreign_trustee_act_input)

        self.subrogate_practice_act_label = QLabel("Subrogate Practice Act Citation:")
        self.subrogate_practice_act_input = QLineEdit()
        deposit_specifics_layout.addWidget(self.subrogate_practice_act_label)
        deposit_specifics_layout.addWidget(self.subrogate_practice_act_input)

        self.manitoba_statutes_label = QLabel("Manitoba Statutes (Special Deposit) Citation:")
        self.manitoba_statutes_input = QLineEdit()
        deposit_specifics_layout.addWidget(self.manitoba_statutes_label)
        deposit_specifics_layout.addWidget(self.manitoba_statutes_input)

        deposit_specifics_group.setLayout(deposit_specifics_layout)
        main_layout.addWidget(deposit_specifics_group)

        # --- Clauses Group ---
        clauses_group = QGroupBox("Clauses")
        clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget()
        clauses_layout.addWidget(self.clauses_list_widget)

        clause_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add Clause")
        self.add_clause_button.clicked.connect(self.add_clause)
        self.edit_clause_button = QPushButton("Edit Clause")
        self.edit_clause_button.setEnabled(False)
        self.remove_clause_button = QPushButton("Remove Clause")
        self.remove_clause_button.setEnabled(False)

        clause_buttons_layout.addWidget(self.add_clause_button)
        clause_buttons_layout.addWidget(self.edit_clause_button)
        clause_buttons_layout.addWidget(self.remove_clause_button)
        clauses_layout.addLayout(clause_buttons_layout)
        clauses_group.setLayout(clauses_layout)
        main_layout.addWidget(clauses_group)

        # --- File Operations ---
        file_ops_layout = QHBoxLayout()
        self.new_button = QPushButton("New Deposit Document")
        self.new_button.clicked.connect(self.new_document)
        self.save_button = QPushButton("Save Deposit")
        self.save_button.clicked.connect(self.save_document)
        self.load_button = QPushButton("Load Deposit")
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
        # Filed documents are managed by add/remove methods directly on self.document.filed_documents
        self.document.source_validation_details = self.source_validation_input.toPlainText()
        self.document.trust_beneficiary_alignment_notes = self.beneficiary_alignment_input.toPlainText()
        self.document.postal_equity_agent_signature_placeholder = self.agent_signature_input.text()
        self.document.notary_signature_placeholder = self.notary_signature_input.text()
        self.document.family_trust_ref = self.family_trust_ref_input.text()
        self.document.postal_charter_ref = self.postal_charter_ref_input.text()
        self.document.foreign_trustee_act_citation = self.foreign_trustee_act_input.text()
        self.document.subrogate_practice_act_citation = self.subrogate_practice_act_input.text()
        self.document.manitoba_statutes_special_deposit_citation = self.manitoba_statutes_input.text()

    def load_document_data_into_ui(self):
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)

        self.filed_docs_list_widget.clear()
        for item_dict in self.document.filed_documents: # Expecting list of dicts like {"doc_name": "...", "details": "..."}
             # For simplicity in Phase 1, just show the 'doc_name' or a combined string.
            display_text = item_dict.get("doc_name", "Unnamed Document")
            if item_dict.get("details"):
                display_text += f" ({item_dict.get('details')})"
            self.filed_docs_list_widget.addItem(display_text)

        self.source_validation_input.setPlainText(self.document.source_validation_details)
        self.beneficiary_alignment_input.setPlainText(self.document.trust_beneficiary_alignment_notes)
        self.agent_signature_input.setText(self.document.postal_equity_agent_signature_placeholder)
        self.notary_signature_input.setText(self.document.notary_signature_placeholder)
        self.family_trust_ref_input.setText(self.document.family_trust_ref or "")
        self.postal_charter_ref_input.setText(self.document.postal_charter_ref or "")
        self.foreign_trustee_act_input.setText(self.document.foreign_trustee_act_citation)
        self.subrogate_practice_act_input.setText(self.document.subrogate_practice_act_citation)
        self.manitoba_statutes_input.setText(self.document.manitoba_statutes_special_deposit_citation)

        self.clauses_list_widget.clear()
        for clause_dict in self.document.clauses:
            self.clauses_list_widget.addItem(f"ID: {clause_dict.get('id', 'N/A')} - {clause_dict.get('text', '')}")

    def add_filed_document_item(self):
        doc_text = self.add_filed_doc_input.text().strip()
        if doc_text:
            # For now, store as simple dict. Could be more structured later.
            self.document.filed_documents.append({"doc_name": doc_text, "details": ""})
            self.filed_docs_list_widget.addItem(doc_text)
            self.add_filed_doc_input.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter text for the filed document.")

    def remove_filed_document_item(self):
        current_row = self.filed_docs_list_widget.currentRow()
        if current_row >= 0:
            item = self.filed_docs_list_widget.takeItem(current_row)
            # Also remove from the self.document.filed_documents list
            # This requires matching based on the text, which is brittle.
            # A more robust way would be to store objects or unique IDs.
            # For Phase 1, we'll find by text.
            item_text = item.text()
            self.document.filed_documents = [
                fd for fd in self.document.filed_documents if fd.get("doc_name") != item_text and
                (fd.get("doc_name") + (f" ({fd.get('details')})" if fd.get("details") else "")) != item_text
            ]
            del item
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a filed document to remove.")


    def new_document(self):
        self.document = MichaudSpecialDepositDocument(name="Untitled Michaud Special Deposit")
        self.current_document_path = None
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Special Deposit document initialized.")

    def add_clause(self):
        clause_text = f"New deposit clause {len(self.document.clauses) + 1}"
        clause_id = f"DEPOSIT-CLAUSE-{len(self.document.clauses) + 1:03d}"
        self.document.add_clause(clause_text, clause_id=clause_id, jurisdiction=self.document.jurisdiction)
        self.clauses_list_widget.addItem(f"ID: {clause_id} - {clause_text}")
        QMessageBox.information(self, "Clause Added", f"Clause '{clause_text}' added (placeholder).")

    def save_document(self):
        self._collect_data_from_ui()
        if not self.current_document_path:
            deposit_dir = os.path.join(CODEX_VAULT_DIR, "deposits")
            safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
            safe_filename = safe_filename.replace(' ', '_') + ".mpea_deposit"

            filePath, _ = QFileDialog.getSaveFileName(
                self,
                "Save Special Deposit Document",
                os.path.join(deposit_dir, safe_filename),
                "Michaud Postal Equity App Deposit Files (*.mpea_deposit);;All Files (*)"
            )
            if not filePath:
                return
            self.current_document_path = filePath

        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)
            QMessageBox.information(self, "Save Successful", f"Special Deposit document saved to\n{self.current_document_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save document: {e}")
            self.current_document_path = None

    def load_document(self):
        deposit_dir = os.path.join(CODEX_VAULT_DIR, "deposits")
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Special Deposit Document",
            deposit_dir,
            "Michaud Postal Equity App Deposit Files (*.mpea_deposit);;All Files (*)"
        )
        if not filePath:
            return

        try:
            with open(filePath, 'r') as f:
                doc_data = json.load(f)
            self.document = MichaudSpecialDepositDocument.from_dict(doc_data)
            self.current_document_path = filePath
            self.load_document_data_into_ui()
            QMessageBox.information(self, "Load Successful", f"Special Deposit document loaded from\n{filePath}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load document: {e}")


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    deposit_view = DepositView()
    deposit_view.setWindowTitle("Test Michaud Special Deposit View")
    deposit_view.setGeometry(100,100, 800, 800)
    deposit_view.show()
    sys.exit(app.exec())
