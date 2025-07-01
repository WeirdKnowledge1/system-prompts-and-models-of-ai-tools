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
        for clause_dict in self.document.clauses:
            self.clauses_list_widget.addItem(f"ID: {clause_dict.get('id', 'N/A')} - {clause_dict.get('text', '')}")

    def new_document(self):
        self.document = MichaudFamilyPostalCharter(name="Untitled Michaud Family Postal Charter")
        self.current_document_path = None
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Postal Charter document initialized.")

    def add_clause(self):
        clause_text = f"New charter clause {len(self.document.clauses) + 1}"
        clause_id = f"CHARTER-CLAUSE-{len(self.document.clauses) + 1:03d}"
        self.document.add_clause(clause_text, clause_id=clause_id, jurisdiction=self.document.jurisdiction)
        self.clauses_list_widget.addItem(f"ID: {clause_id} - {clause_text}")
        QMessageBox.information(self, "Clause Added", f"Clause '{clause_text}' added (placeholder).")

    def save_document(self):
        self._collect_data_from_ui()
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
