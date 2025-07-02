from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox, QListWidgetItem, QInputDialog, QApplication) # Added QInputDialog, QApplication
from PyQt6.QtCore import Qt
import json
import os
import datetime
import uuid

from app.core.document_models import MichaudSpecialDepositDocument
from app.core.clause_model import Clause
from app.ui.dialogs.edit_clause_dialog import EditClauseDialog
from app.ui.dialogs.qr_display_dialog import QRDisplayDialog
from app.core.agents import ClauseConformer, VeritasProof, DocumentTracker
from app.core.document_utils import generate_display_clause_numbers
from app.utils.constants import CODEX_VAULT_DIR

class DepositView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudSpecialDepositDocument(name="Untitled Special Deposit Document")
        self.is_modified = False
        self.last_conformance_issues = None # To store issues for GitHub reporting
        self._setup_ui()
        self._connect_modification_signals()

    def _connect_modification_signals(self):
        self.name_input.textChanged.connect(self._mark_as_modified)
        self.jurisdiction_input.textChanged.connect(self._mark_as_modified)
        # Specific fields for SpecialDepositDocument
        self.filed_docs_input.textChanged.connect(self._mark_as_modified) # Assuming QTextEdit for simplicity
        self.source_validation_input.textChanged.connect(self._mark_as_modified)
        self.trust_beneficiary_notes_input.textChanged.connect(self._mark_as_modified)
        self.agent_signature_input.textChanged.connect(self._mark_as_modified)
        self.notary_signature_input.textChanged.connect(self._mark_as_modified)
        self.foreign_trustee_act_input.textChanged.connect(self._mark_as_modified)
        self.subrogate_practice_act_input.textChanged.connect(self._mark_as_modified)
        self.manitoba_statutes_input.textChanged.connect(self._mark_as_modified)
        # Linking fields
        self.family_trust_ref_input.textChanged.connect(self._mark_as_modified)
        self.postal_charter_ref_input.textChanged.connect(self._mark_as_modified)
        self.upu_tracking_number_input.textChanged.connect(self._mark_as_modified)


    def _mark_as_modified(self, text=None):
        self.is_modified = True

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.jurisdiction_header_label = QLabel("Jurisdiction: N/A") # Updated by _update_document_jurisdiction
        self.jurisdiction_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.jurisdiction_header_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px; background-color: #E8E8E8; border-bottom: 1px solid #C0C0C0;")
        main_layout.addWidget(self.jurisdiction_header_label)

        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()
        doc_info_layout.addWidget(QLabel("Deposit Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(lambda text: setattr(self.document, 'name', text))
        doc_info_layout.addWidget(self.name_input, 0, 1)
        doc_info_layout.addWidget(QLabel("Document ID:"), 1, 0)
        self.id_display = QLabel(self.document.id)
        doc_info_layout.addWidget(self.id_display, 1, 1)
        doc_info_layout.addWidget(QLabel("Jurisdiction:"), 2, 0)
        self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        self.jurisdiction_input.textChanged.connect(self._update_document_jurisdiction)
        doc_info_layout.addWidget(self.jurisdiction_input, 2, 1)
        doc_info_group.setLayout(doc_info_layout)
        main_layout.addWidget(doc_info_group)

        deposit_details_group = QGroupBox("Special Deposit Specifics")
        deposit_details_layout = QVBoxLayout()

        deposit_details_layout.addWidget(QLabel("Filed Documents (e.g., 'Name: ID', one per line):"))
        self.filed_docs_input = QTextEdit() # Simple text for now, could be a list/table later
        deposit_details_layout.addWidget(self.filed_docs_input)

        deposit_details_layout.addWidget(QLabel("Source Validation Details:"))
        self.source_validation_input = QTextEdit()
        deposit_details_layout.addWidget(self.source_validation_input)

        deposit_details_layout.addWidget(QLabel("Trust Beneficiary Alignment Notes:"))
        self.trust_beneficiary_notes_input = QTextEdit()
        deposit_details_layout.addWidget(self.trust_beneficiary_notes_input)

        deposit_details_layout.addWidget(QLabel("Postal Equity Agent Signature Placeholder:"))
        self.agent_signature_input = QLineEdit()
        deposit_details_layout.addWidget(self.agent_signature_input)

        deposit_details_layout.addWidget(QLabel("Notary Signature Placeholder:"))
        self.notary_signature_input = QLineEdit()
        deposit_details_layout.addWidget(self.notary_signature_input)

        deposit_details_layout.addWidget(QLabel("Foreign Trustee Act Citation:"))
        self.foreign_trustee_act_input = QLineEdit()
        deposit_details_layout.addWidget(self.foreign_trustee_act_input)

        deposit_details_layout.addWidget(QLabel("Subrogate Practice Act Citation:"))
        self.subrogate_practice_act_input = QLineEdit()
        deposit_details_layout.addWidget(self.subrogate_practice_act_input)

        deposit_details_layout.addWidget(QLabel("Manitoba Statutes Special Deposit Citation:"))
        self.manitoba_statutes_input = QLineEdit()
        deposit_details_layout.addWidget(self.manitoba_statutes_input)

        # Document Linking Fields
        deposit_details_layout.addWidget(QLabel("Linked Family Trust Ref:"))
        link_ft_layout = QHBoxLayout()
        self.family_trust_ref_input = QLineEdit(self.document.family_trust_ref or "")
        self.family_trust_ref_input.setPlaceholderText("Enter ID, relative path, or browse")
        self.family_trust_ref_input.textChanged.connect(self._update_family_trust_ref)
        self.browse_ft_button = QPushButton("Browse...")
        self.browse_ft_button.clicked.connect(lambda: self._browse_linked_document("FamilyTrust"))
        self.clear_ft_button = QPushButton("Clear")
        self.clear_ft_button.clicked.connect(lambda: self._clear_linked_document("FamilyTrust"))
        link_ft_layout.addWidget(self.family_trust_ref_input)
        link_ft_layout.addWidget(self.browse_ft_button)
        link_ft_layout.addWidget(self.clear_ft_button)
        deposit_details_layout.addLayout(link_ft_layout)

        deposit_details_layout.addWidget(QLabel("Linked Postal Charter Ref:"))
        link_pc_layout = QHBoxLayout()
        self.postal_charter_ref_input = QLineEdit(self.document.postal_charter_ref or "")
        self.postal_charter_ref_input.setPlaceholderText("Enter ID, relative path, or browse")
        self.postal_charter_ref_input.textChanged.connect(self._update_postal_charter_ref)
        self.browse_pc_button = QPushButton("Browse...")
        self.browse_pc_button.clicked.connect(lambda: self._browse_linked_document("PostalCharter"))
        self.clear_pc_button = QPushButton("Clear")
        self.clear_pc_button.clicked.connect(lambda: self._clear_linked_document("PostalCharter"))
        link_pc_layout.addWidget(self.postal_charter_ref_input)
        link_pc_layout.addWidget(self.browse_pc_button)
        link_pc_layout.addWidget(self.clear_pc_button)
        deposit_details_layout.addLayout(link_pc_layout)

        self.upu_tracking_number_label = QLabel("UPU Tracking Number:")
        self.upu_tracking_number_input = QLineEdit()
        self.upu_tracking_number_input.setPlaceholderText("Enter UPU tracking number if applicable")
        self.upu_tracking_number_input.textChanged.connect(self._update_jurisdictional_delivery_tag)
        deposit_details_layout.addWidget(self.upu_tracking_number_label)
        deposit_details_layout.addWidget(self.upu_tracking_number_input)
        self.jurisdictional_delivery_tag_label = QLabel("Jurisdictional Delivery Tag:")
        self.jurisdictional_delivery_tag_display = QLabel("N/A")
        self.jurisdictional_delivery_tag_display.setStyleSheet("font-style: italic; color: #555;")
        deposit_details_layout.addWidget(self.jurisdictional_delivery_tag_label)
        deposit_details_layout.addWidget(self.jurisdictional_delivery_tag_display)

        deposit_details_group.setLayout(deposit_details_layout)
        main_layout.addWidget(deposit_details_group)

        # Clauses Group (copied from TrustView, should be identical)
        clauses_group = QGroupBox("Clauses")
        clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget()
        self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)
        self.selected_clause_details_group = QGroupBox("Selected Clause Details")
        selected_clause_layout = QGridLayout()
        self.sel_clause_id_label = QLabel("ID:")
        self.sel_clause_id_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_id_label, 0, 0)
        selected_clause_layout.addWidget(self.sel_clause_id_value, 0, 1)
        self.sel_clause_display_number_label = QLabel("Display No.:")
        self.sel_clause_display_number_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_display_number_label, 1, 0)
        selected_clause_layout.addWidget(self.sel_clause_display_number_value, 1, 1)
        self.sel_clause_jurisdiction_label = QLabel("Jurisdiction:")
        self.sel_clause_jurisdiction_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_jurisdiction_label, 2, 0)
        selected_clause_layout.addWidget(self.sel_clause_jurisdiction_value, 2, 1)
        # ... Add all other sel_clause_* labels and values (origin, text, purpose, level, section_title, dates, version, lock_status)
        # For brevity, assuming these are similar to TrustView
        self.sel_clause_text_label = QLabel("Text:")
        self.sel_clause_text_value = QTextEdit()
        self.sel_clause_text_value.setReadOnly(True)
        selected_clause_layout.addWidget(self.sel_clause_text_label, 4,0) # Example
        selected_clause_layout.addWidget(self.sel_clause_text_value, 5,0,1,2) # Example

        self.sel_clause_lock_status_label = QLabel("Status:")
        self.sel_clause_lock_status_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_lock_status_label, 12, 0)
        selected_clause_layout.addWidget(self.sel_clause_lock_status_value, 12, 1)

        buttons_sel_clause_layout = QHBoxLayout()
        self.edit_selected_clause_button = QPushButton("Edit Selected Clause")
        self.edit_selected_clause_button.setEnabled(False)
        self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)
        self.generate_qr_button = QPushButton("Generate QR Code")
        self.generate_qr_button.setEnabled(False)
        self.generate_qr_button.clicked.connect(self._generate_clause_qr_code)
        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button)
        buttons_sel_clause_layout.addWidget(self.generate_qr_button)
        selected_clause_layout.addLayout(buttons_sel_clause_layout, 13, 0, 1, 2)
        self.selected_clause_details_group.setLayout(selected_clause_layout)
        self.selected_clause_details_group.setVisible(False)
        clauses_layout.addWidget(self.selected_clause_details_group)

        clause_action_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add New Clause")
        self.add_clause_button.clicked.connect(self.add_clause)
        self.remove_clause_button = QPushButton("Remove Selected Clause")
        self.remove_clause_button.setEnabled(False)
        self.remove_clause_button.clicked.connect(self.remove_selected_clause)
        # ... Move Up/Down buttons
        clause_action_buttons_layout.addWidget(self.add_clause_button)
        clause_action_buttons_layout.addWidget(self.remove_clause_button)
        clauses_layout.addLayout(clause_action_buttons_layout)
        clauses_group.setLayout(clauses_layout)
        main_layout.addWidget(clauses_group)

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

        self.conformance_check_button = QPushButton("Run Basic Conformance Check")
        self.conformance_check_button.clicked.connect(self.run_basic_conformance_check)
        self.create_github_issue_button = QPushButton("Create GitHub Issue for Conformance Failures")
        self.create_github_issue_button.clicked.connect(self._create_github_issue_for_conformance)
        self.create_github_issue_button.setVisible(False)

        conformance_layout = QHBoxLayout()
        conformance_layout.addWidget(self.conformance_check_button)
        conformance_layout.addWidget(self.create_github_issue_button)
        conformance_layout.addStretch()
        main_layout.addLayout(conformance_layout)

        main_layout.addStretch()
        self.load_document_data_into_ui()

    def _update_document_jurisdiction(self, text: str):
        self.document.jurisdiction = text
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
        self._mark_as_modified()

    def _collect_data_from_ui(self):
        self.document.name = self.name_input.text()
        # Parse filed_docs_input: "Name1: ID1\nName2: ID2" into list of dicts
        filed_docs_list = []
        for line in self.filed_docs_input.toPlainText().splitlines():
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    filed_docs_list.append({"doc_name": parts[0].strip(), "details": parts[1].strip()})
                else:
                    filed_docs_list.append({"doc_name": parts[0].strip(), "details": ""}) # Or handle error
        self.document.filed_documents = filed_docs_list

        self.document.source_validation_details = self.source_validation_input.toPlainText()
        self.document.trust_beneficiary_alignment_notes = self.trust_beneficiary_notes_input.toPlainText()
        self.document.postal_equity_agent_signature_placeholder = self.agent_signature_input.text()
        self.document.notary_signature_placeholder = self.notary_signature_input.text()
        self.document.foreign_trustee_act_citation = self.foreign_trustee_act_input.text()
        self.document.subrogate_practice_act_citation = self.subrogate_practice_act_input.text()
        self.document.manitoba_statutes_special_deposit_citation = self.manitoba_statutes_input.text()
        self.document.family_trust_ref = self.family_trust_ref_input.text().strip() or None
        self.document.postal_charter_ref = self.postal_charter_ref_input.text().strip() or None
        self.document.upu_tracking_number = self.upu_tracking_number_input.text().strip()
        if self.document.upu_tracking_number:
            self._generate_and_set_delivery_tag()
        else:
            self.document.jurisdictional_delivery_tag = None


    def _generate_and_set_delivery_tag(self): # Copied from CharterView
        if self.document.upu_tracking_number:
            year = datetime.datetime.now().year
            sequence = self.document.upu_tracking_number[-4:] if len(self.document.upu_tracking_number) >= 4 else "001"
            prefix = "LEXPOST-CA-MB-UPU"
            self.document.jurisdictional_delivery_tag = f"{prefix}-{year}-{sequence}"
        else:
            self.document.jurisdictional_delivery_tag = None
        self.jurisdictional_delivery_tag_display.setText(self.document.jurisdictional_delivery_tag or "N/A")
        self._mark_as_modified()

    def _update_jurisdictional_delivery_tag(self, text=None): # Copied from CharterView
        self.document.upu_tracking_number = self.upu_tracking_number_input.text().strip()
        self._generate_and_set_delivery_tag()


    def _refresh_clause_list_display(self): # Standard implementation
        current_selected_id = None
        if self.clauses_list_widget.currentItem():
            current_selected_id = self.clauses_list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        self.clauses_list_widget.clear()
        if not self.document or not self.document.clauses:
            self.display_selected_clause_details()
            return
        display_numbers = generate_display_clause_numbers(self.document.clauses)
        new_selected_row = -1
        for i, clause_obj in enumerate(self.document.clauses):
            display_number = display_numbers[i] if i < len(display_numbers) else "Err!"
            item_text = f"{display_number} {str(clause_obj)}"
            if clause_obj.section_title: item_text = f"{display_number}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, clause_obj.id)
            self.clauses_list_widget.addItem(item)
            if clause_obj.id == current_selected_id: new_selected_row = i
        if new_selected_row != -1: self.clauses_list_widget.setCurrentRow(new_selected_row)
        else: self.display_selected_clause_details()

    def load_document_data_into_ui(self):
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {self.document.jurisdiction}")

        # Format filed_documents for display
        filed_docs_text = "\n".join([f"{item.get('doc_name', 'N/A')}: {item.get('details', 'N/A')}" for item in self.document.filed_documents])
        self.filed_docs_input.setPlainText(filed_docs_text)

        self.source_validation_input.setPlainText(self.document.source_validation_details)
        self.trust_beneficiary_notes_input.setPlainText(self.document.trust_beneficiary_alignment_notes)
        self.agent_signature_input.setText(self.document.postal_equity_agent_signature_placeholder)
        self.notary_signature_input.setText(self.document.notary_signature_placeholder)
        self.foreign_trustee_act_input.setText(self.document.foreign_trustee_act_citation)
        self.subrogate_practice_act_input.setText(self.document.subrogate_practice_act_citation)
        self.manitoba_statutes_input.setText(self.document.manitoba_statutes_special_deposit_citation)
        self.family_trust_ref_input.setText(self.document.family_trust_ref or "")
        self.postal_charter_ref_input.setText(self.document.postal_charter_ref or "")
        self.upu_tracking_number_input.setText(self.document.upu_tracking_number or "")
        self.jurisdictional_delivery_tag_display.setText(self.document.jurisdictional_delivery_tag or "N/A")

        self._refresh_clause_list_display()
        self.is_modified = False
        # Auto conformance check on load
        main_window_instance = self.window()
        if hasattr(main_window_instance, 'settings_view') and \
           main_window_instance.settings_view.get_setting("enforce_clauseconformer_all_docs"):
            self.run_basic_conformance_check(is_auto_check=True)

    def new_document(self):
        # Untrack current document if it exists
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e: print(f"Error untracking deposit {self.document.id}: {e}")

        self.document = MichaudSpecialDepositDocument(name="Untitled Special Deposit Document")
        self.current_document_path = None
        self.is_modified = False
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Special Deposit document initialized.")

    def add_clause(self): # Standard
        dialog = EditClauseDialog(default_jurisdiction=self.document.jurisdiction, parent=self)
        if dialog.exec():
            new_clause = dialog.get_clause()
            self.document.clauses.append(new_clause)
            self._refresh_clause_list_display()
            if self.clauses_list_widget.count() > 0:
                self.clauses_list_widget.setCurrentRow(self.clauses_list_widget.count() - 1)
            self._mark_as_modified()

    def display_selected_clause_details(self): # Standard, ensure all sel_clause_* are populated
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]
            clause_id = list_item.data(Qt.ItemDataRole.UserRole)
            clause_obj = next((c for c in self.document.clauses if c.id == clause_id), None)
            current_row = self.clauses_list_widget.row(list_item)
            if clause_obj:
                # Populate all sel_clause_* fields, including display_number, level, section_title, lock_status
                display_numbers = generate_display_clause_numbers(self.document.clauses)
                self.sel_clause_display_number_value.setText(display_numbers[current_row] if current_row < len(display_numbers) else "N/A")
                self.sel_clause_id_value.setText(clause_obj.id)
                self.sel_clause_jurisdiction_value.setText(clause_obj.jurisdiction)
                # self.sel_clause_origin_value.setText(clause_obj.origin) # Assuming it exists
                self.sel_clause_text_value.setPlainText(clause_obj.text)
                # self.sel_clause_purpose_value.setText(clause_obj.metadata.get("purpose_type", "N/A"))
                # self.sel_clause_level_value.setText(str(clause_obj.level))
                # self.sel_clause_section_title_value.setText(clause_obj.section_title or "N/A")
                # ... dates, version ...
                self.sel_clause_lock_status_value.setText("🔒 Locked" if clause_obj.is_locked else "✏️ Editable")
                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True)
                self.remove_clause_button.setEnabled(True)
                # ... move buttons, qr button ...
                main_window_instance = self.window()
                qr_setting_enabled = False
                if hasattr(main_window_instance, 'settings_view') and \
                   hasattr(main_window_instance.settings_view, 'get_setting'):
                    qr_setting_enabled = main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled")
                self.generate_qr_button.setEnabled(qr_setting_enabled)

            else: self.selected_clause_details_group.setVisible(False) # Error case
        else: self.selected_clause_details_group.setVisible(False) # No selection

    def edit_selected_clause(self): # Standard
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: return
        list_item = selected_items[0]
        clause_id = list_item.data(Qt.ItemDataRole.UserRole)
        clause_to_edit = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_to_edit:
            dialog = EditClauseDialog(clause=clause_to_edit, parent=self)
            if dialog.exec():
                self._refresh_clause_list_display()
                for i in range(self.clauses_list_widget.count()):
                    if self.clauses_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == clause_id:
                        self.clauses_list_widget.setCurrentRow(i); break
                self._mark_as_modified()

    def remove_selected_clause(self): # Standard
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: return
        # ... confirmation and removal ...
        list_item = selected_items[0]
        clause_id = list_item.data(Qt.ItemDataRole.UserRole)
        clause_to_remove = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_to_remove:
            reply = QMessageBox.question(self, "Remove Clause", f"Remove '{str(clause_to_remove)}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.document.clauses.remove(clause_to_remove)
                self._refresh_clause_list_display()
                self._mark_as_modified()


    def save_document(self, silent=False): # Standard, adapt messages
        self._collect_data_from_ui()
        if not self._validate_document_basic():
            if not silent: QMessageBox.warning(self, "Validation Failed", "Cannot save: validation errors.")
            return False
        if not self.current_document_path: return self.save_document_as(silent=silent)
        try:
            with open(self.current_document_path, 'w') as f: json.dump(self.document.to_dict(), f, indent=4)
            if not silent: QMessageBox.information(self, "Save", f"Deposit saved to\n{self.current_document_path}")
            else: # Auto-save message
                main_window = self.window();
                if hasattr(main_window, 'status_bar'): main_window.status_bar.showMessage(f"Auto-saved: {os.path.basename(self.current_document_path)}",3000)
            self.is_modified = False
            # Track change
            doc_tracker = DocumentTracker(app_context=self.window())
            doc_tracker.track_document_change(self.document.id, self.document.to_dict())
            return True
        except Exception as e:
            if not silent: QMessageBox.critical(self, "Save Error", f"Could not save: {e}")
            else: print(f"Auto-save error: {e}")
            return False

    def save_document_as(self, silent=False): # Standard, adapt messages and filter
        self._collect_data_from_ui()
        if not self._validate_document_basic():
            if not silent: QMessageBox.warning(self, "Validation Failed", "Cannot save: validation errors.")
            return False

        deposit_dir = os.path.join(CODEX_VAULT_DIR, "deposits")
        safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
        safe_filename = safe_filename.replace(' ', '_') + ".mpea_deposit"

        filePath, _ = QFileDialog.getSaveFileName(self, "Save Special Deposit As...",
                                                  os.path.join(deposit_dir, safe_filename),
                                                  "MPEA Deposit Files (*.mpea_deposit);;All Files (*)")
        if not filePath: return False

        if self.current_document_path and hasattr(self.document, 'id'): # Untrack old if exists
            doc_tracker = DocumentTracker(app_context=self.window())
            doc_tracker.untrack_document(self.document.id)

        self.current_document_path = filePath
        self.document.id = str(uuid.uuid4()) # New ID for Save As
        self.id_display.setText(self.document.id)

        try:
            with open(self.current_document_path, 'w') as f: json.dump(self.document.to_dict(), f, indent=4)
            if not silent: QMessageBox.information(self, "Save As", f"Deposit saved to\n{self.current_document_path}")
            else: # Auto-save message
                main_window = self.window();
                if hasattr(main_window, 'status_bar'): main_window.status_bar.showMessage(f"Auto-saved (new): {os.path.basename(self.current_document_path)}",3000)
            self.is_modified = False
            # Track new document
            doc_tracker = DocumentTracker(app_context=self.window())
            doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
            return True
        except Exception as e:
            if not silent: QMessageBox.critical(self, "Save As Error", f"Could not save: {e}")
            else: print(f"Auto-save (new) error: {e}")
            return False

    def load_document(self): # Standard, adapt messages and filter
        if self.current_document_path and hasattr(self.document, 'id'): # Untrack current
            doc_tracker = DocumentTracker(app_context=self.window())
            doc_tracker.untrack_document(self.document.id)

        deposit_dir = os.path.join(CODEX_VAULT_DIR, "deposits")
        filePath, _ = QFileDialog.getOpenFileName(self, "Load Special Deposit", deposit_dir,
                                                  "MPEA Deposit Files (*.mpea_deposit);;All Files (*)")
        if not filePath: return
        try:
            with open(filePath, 'r') as f: doc_data = json.load(f)
            self.document = MichaudSpecialDepositDocument.from_dict(doc_data)
            self.current_document_path = filePath
            self.is_modified = False
            self.load_document_data_into_ui()
            QMessageBox.information(self, "Load Successful", f"Deposit loaded from\n{filePath}")
            # Track loaded document
            doc_tracker = DocumentTracker(app_context=self.window())
            doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load: {e}")

    def _validate_document_basic(self) -> bool: # Basic validation
        self._collect_data_from_ui()
        errors = []
        if not self.document.name.strip(): errors.append("Deposit Name cannot be empty.")
        # Add other specific validations for DepositDocument if needed
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return False
        return True

    def _generate_clause_qr_code(self): # Standard
        # ... (implementation similar to TrustView/CharterView) ...
        # For brevity, assuming it's correctly implemented as in other views
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "QR Error", "No clause selected."); return
        # ... rest of QR generation logic
        pass

    def run_basic_conformance_check(self, is_auto_check=False): # Standard
        self._collect_data_from_ui()
        main_window_instance = self.window()
        conformer = ClauseConformer(app_context=main_window_instance)
        self.last_conformance_issues = conformer.check_document_for_basic_issues(self.document)

        if self.last_conformance_issues:
            detailed_report_items = []
            warning_count = 0
            info_count = 0
            for item in self.last_conformance_issues:
                issue_detail_line = f"- ID: {item.get('id', 'N/A')[:15]}... ({item.get('severity', 'N/A')}): {item.get('issue', 'N/A')}"
                if "suggestions" in item and item["suggestions"]:
                    issue_detail_line += "\n  Suggestions:"
                    for sugg in item["suggestions"]:
                        issue_detail_line += f"\n    - {sugg}"
                detailed_report_items.append(issue_detail_line)

                if item.get('severity') == 'warning': warning_count += 1
                else: info_count += 1
            summary = f"{len(self.last_conformance_issues)} issue(s) found: {warning_count} warning(s), {info_count} info."

            self.create_github_issue_button.setVisible(True)

            if is_auto_check:
                if hasattr(main_window_instance, 'status_bar'):
                    main_window_instance.status_bar.showMessage(f"Conformance: {summary}", 10000)
                print(f"Auto Conformance Check (Deposit):\n{summary}\nDetails:\n" + "\n".join(detailed_report_items))
            else:
                QMessageBox.warning(self, "Conformance Issues Found", summary + "\n\nDetails:\n" + "\n".join(detailed_report_items))
        else:
            self.last_conformance_issues = None
            self.create_github_issue_button.setVisible(False)
            if not is_auto_check:
                QMessageBox.information(self, "Conformance Check", "No basic conformance issues found.")
            else:
                if hasattr(main_window_instance, 'status_bar'):
                    main_window_instance.status_bar.showMessage("Conformance: No basic issues found.", 5000)
                print("Auto Conformance Check (Deposit): No basic issues found.")

    def _create_github_issue_for_conformance(self): # Copied from TrustView/CharterView
        if not self.last_conformance_issues:
            QMessageBox.information(self, "No Issues", "No conformance issues to report.")
            return

        repo_name, ok = QInputDialog.getText(self, "GitHub Repository",
                                             "Enter repository name (owner/repo):")
        if not ok or not repo_name.strip():
            QMessageBox.warning(self, "Input Error", "Repository name cannot be empty.")
            return

        repo_name = repo_name.strip()
        issue_title = f"Conformance Issues in Document: {self.document.name} ({self.document.id})"
        body_parts = ["Conformance issues detected in document:\n"]
        for item in self.last_conformance_issues:
            body_parts.append(f"- **Severity:** {item.get('severity', 'N/A')}")
            body_parts.append(f"  **Clause/Doc ID:** {item.get('id', 'N/A')}")
            body_parts.append(f"  **Issue:** {item.get('issue', 'N/A')}\n")
        issue_body = "\n".join(body_parts)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        project_root_for_path = None
        try:
            import sys
            import os
            project_root_for_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if project_root_for_path not in sys.path:
                sys.path.insert(0, project_root_for_path)
            from api_integrations import github_create_issue

            created_issue = github_create_issue(repo_name, issue_title, issue_body)
            QApplication.restoreOverrideCursor()

            if created_issue and created_issue.get("html_url"):
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("GitHub Issue Created")
                msg_box.setTextFormat(Qt.TextFormat.RichText)
                msg_box.setText(f"Successfully created GitHub issue in '{repo_name}'.\n"
                                f"<a href='{created_issue.get('html_url')}'>View Issue: {created_issue.get('number')}</a>")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
            else:
                QMessageBox.information(self, "GitHub Issue Created",
                                        f"Issue created in '{repo_name}', but no URL or full data returned.")
        except ImportError as ie:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"Could not import API integration module: {ie}")
        except ValueError as ve:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Configuration Error", str(ve))
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "API Error", f"Could not create GitHub issue:\n{e}")
        finally:
            if project_root_for_path and project_root_for_path in sys.path and sys.path[0] == project_root_for_path:
                sys.path.pop(0)

    # Linking methods
    def _update_family_trust_ref(self, text: str):
        self.document.family_trust_ref = text.strip() or None
        self._mark_as_modified()

    def _update_postal_charter_ref(self, text: str):
        self.document.postal_charter_ref = text.strip() or None
        self._mark_as_modified()

    def _browse_linked_document(self, link_type: str):
        if link_type == "FamilyTrust":
            doc_dir_name = "trusts"
            file_filter = "MPEA Trust Files (*.mpea_trust);;All Files (*)"
            target_input_widget = self.family_trust_ref_input
            model_attribute_name = "family_trust_ref"
            dialog_title = "Select Linked Family Trust"
        elif link_type == "PostalCharter":
            doc_dir_name = "charters"
            file_filter = "MPEA Charter Files (*.mpea_charter);;All Files (*)"
            target_input_widget = self.postal_charter_ref_input
            model_attribute_name = "postal_charter_ref"
            dialog_title = "Select Linked Postal Charter"
        else:
            QMessageBox.warning(self, "Error", f"Unknown link type: {link_type}")
            return

        start_dir = os.path.join(CODEX_VAULT_DIR, doc_dir_name)
        os.makedirs(start_dir, exist_ok=True)
        filePath, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, file_filter)

        if filePath:
            try: relative_path = os.path.relpath(filePath, CODEX_VAULT_DIR); display_path = relative_path
            except ValueError: display_path = filePath
            if os.path.isabs(display_path) and filePath.startswith(os.path.abspath(CODEX_VAULT_DIR)):
                 display_path = os.path.relpath(filePath, CODEX_VAULT_DIR)
            target_input_widget.setText(display_path)
            setattr(self.document, model_attribute_name, display_path)
            self._mark_as_modified()
            QMessageBox.information(self, "Link Set", f"{link_type} linked to: {display_path}")

    def _clear_linked_document(self, link_type: str):
        if link_type == "FamilyTrust":
            self.family_trust_ref_input.clear()
            self.document.family_trust_ref = None
        elif link_type == "PostalCharter":
            self.postal_charter_ref_input.clear()
            self.document.postal_charter_ref = None
        else: return
        self._mark_as_modified()
        QMessageBox.information(self, "Link Cleared", f"{link_type} link cleared.")


if __name__ == '__main__':
    # This needs QApplication from PyQt6.QtWidgets for standalone run
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    deposit_view = DepositView()
    deposit_view.setWindowTitle("Test Michaud Special Deposit View")
    deposit_view.setGeometry(100,100, 850, 750) # Adjusted size
    deposit_view.show()
    sys.exit(app.exec())
