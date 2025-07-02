from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox, QListWidgetItem, QInputDialog, QApplication)
from PyQt6.QtCore import Qt
from collections import deque
import json
import os
import datetime
import uuid

from app.core.document_models import MichaudSpecialDepositDocument
from app.core.commands import Command, AddClauseCommand, RemoveClauseCommand, EditClauseCommand, MoveClauseCommand
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
        self.last_conformance_issues = None

        self.UNDO_STACK_LIMIT = 50
        self.undo_stack = deque(maxlen=self.UNDO_STACK_LIMIT)
        self.redo_stack = deque(maxlen=self.UNDO_STACK_LIMIT)

        self._setup_ui()
        self._connect_ui_signals_to_model_direct_updates()
        self._update_undo_redo_button_states()

    def _connect_ui_signals_to_model_direct_updates(self):
        self.name_input.textChanged.connect(lambda text: self._update_doc_attr_direct('name', text))
        self.jurisdiction_input.textChanged.connect(self._update_document_jurisdiction_direct)

        self.filed_docs_input.textChanged.connect(self._update_filed_docs_direct)
        self.source_validation_input.textChanged.connect(lambda: self._update_doc_attr_direct('source_validation_details', self.source_validation_input.toPlainText()))
        self.trust_beneficiary_notes_input.textChanged.connect(lambda: self._update_doc_attr_direct('trust_beneficiary_alignment_notes', self.trust_beneficiary_notes_input.toPlainText()))
        self.agent_signature_input.textChanged.connect(lambda text: self._update_doc_attr_direct('postal_equity_agent_signature_placeholder', text))
        self.notary_signature_input.textChanged.connect(lambda text: self._update_doc_attr_direct('notary_signature_placeholder', text))
        self.foreign_trustee_act_input.textChanged.connect(lambda text: self._update_doc_attr_direct('foreign_trustee_act_citation', text))
        self.subrogate_practice_act_input.textChanged.connect(lambda text: self._update_doc_attr_direct('subrogate_practice_act_citation', text))
        self.manitoba_statutes_input.textChanged.connect(lambda text: self._update_doc_attr_direct('manitoba_statutes_special_deposit_citation', text))

        self.family_trust_ref_input.textChanged.connect(self._update_family_trust_ref_direct)
        self.postal_charter_ref_input.textChanged.connect(self._update_postal_charter_ref_direct)
        self.upu_tracking_number_input.textChanged.connect(self._update_upu_tracking_and_delivery_tag_direct)

    def _update_doc_attr_direct(self, attr_name, value):
        if getattr(self.document, attr_name) != value:
            setattr(self.document, attr_name, value)
            self._mark_as_modified()

    def _update_filed_docs_direct(self):
        # This needs careful handling if we want undo for it. For now, direct.
        filed_docs_list = []
        for line in self.filed_docs_input.toPlainText().splitlines():
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2: filed_docs_list.append({"doc_name": parts[0].strip(), "details": parts[1].strip()})
                else: filed_docs_list.append({"doc_name": parts[0].strip(), "details": ""})
        if self.document.filed_documents != filed_docs_list:
            self.document.filed_documents = filed_docs_list
            self._mark_as_modified()


    def _mark_as_modified(self):
        self.is_modified = True

    def _setup_ui(self):
        # ... (UI setup largely as before, condensed for brevity) ...
        main_layout = QVBoxLayout(self)
        self.jurisdiction_header_label = QLabel("Jurisdiction: N/A") # Details omitted
        main_layout.addWidget(self.jurisdiction_header_label)
        doc_info_group = QGroupBox("Document Information") # Details omitted
        doc_info_layout = QGridLayout(); self.name_label = QLabel("Deposit Name:"); self.name_input = QLineEdit()
        doc_info_layout.addWidget(self.name_label,0,0); doc_info_layout.addWidget(self.name_input,0,1)
        self.id_label = QLabel("Document ID:"); self.id_display = QLabel(self.document.id)
        doc_info_layout.addWidget(self.id_label,1,0); doc_info_layout.addWidget(self.id_display,1,1)
        self.jurisdiction_label = QLabel("Jurisdiction:"); self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        doc_info_layout.addWidget(self.jurisdiction_label,2,0); doc_info_layout.addWidget(self.jurisdiction_input,2,1)
        doc_info_group.setLayout(doc_info_layout); main_layout.addWidget(doc_info_group)

        deposit_details_group = QGroupBox("Special Deposit Specifics") # Details omitted
        deposit_details_layout = QVBoxLayout()
        deposit_details_layout.addWidget(QLabel("Filed Documents (e.g., 'Name: ID', one per line):")); self.filed_docs_input = QTextEdit()
        deposit_details_layout.addWidget(self.filed_docs_input)
        deposit_details_layout.addWidget(QLabel("Source Validation Details:")); self.source_validation_input = QTextEdit()
        deposit_details_layout.addWidget(self.source_validation_input)
        # ... (other specific fields for Deposit document) ...
        self.trust_beneficiary_notes_input = QTextEdit(); deposit_details_layout.addWidget(QLabel("Trust Beneficiary Alignment Notes:")); deposit_details_layout.addWidget(self.trust_beneficiary_notes_input)
        self.agent_signature_input = QLineEdit(); deposit_details_layout.addWidget(QLabel("Postal Equity Agent Signature Placeholder:")); deposit_details_layout.addWidget(self.agent_signature_input)
        self.notary_signature_input = QLineEdit(); deposit_details_layout.addWidget(QLabel("Notary Signature Placeholder:")); deposit_details_layout.addWidget(self.notary_signature_input)
        self.foreign_trustee_act_input = QLineEdit(); deposit_details_layout.addWidget(QLabel("Foreign Trustee Act Citation:")); deposit_details_layout.addWidget(self.foreign_trustee_act_input)
        self.subrogate_practice_act_input = QLineEdit(); deposit_details_layout.addWidget(QLabel("Subrogate Practice Act Citation:")); deposit_details_layout.addWidget(self.subrogate_practice_act_input)
        self.manitoba_statutes_input = QLineEdit(); deposit_details_layout.addWidget(QLabel("Manitoba Statutes Special Deposit Citation:")); deposit_details_layout.addWidget(self.manitoba_statutes_input)

        deposit_details_layout.addWidget(QLabel("Linked Family Trust Ref:")) # Linking UI
        link_ft_layout = QHBoxLayout(); self.family_trust_ref_input = QLineEdit(); self.family_trust_ref_input.setPlaceholderText("ID, path, or browse")
        self.browse_ft_button = QPushButton("Browse..."); self.browse_ft_button.clicked.connect(lambda: self._browse_linked_document("FamilyTrust"))
        self.clear_ft_button = QPushButton("Clear"); self.clear_ft_button.clicked.connect(lambda: self._clear_linked_document("FamilyTrust"))
        link_ft_layout.addWidget(self.family_trust_ref_input); link_ft_layout.addWidget(self.browse_ft_button); link_ft_layout.addWidget(self.clear_ft_button)
        deposit_details_layout.addLayout(link_ft_layout)
        deposit_details_layout.addWidget(QLabel("Linked Postal Charter Ref:"))
        link_pc_layout = QHBoxLayout(); self.postal_charter_ref_input = QLineEdit(); self.postal_charter_ref_input.setPlaceholderText("ID, path, or browse")
        self.browse_pc_button = QPushButton("Browse..."); self.browse_pc_button.clicked.connect(lambda: self._browse_linked_document("PostalCharter"))
        self.clear_pc_button = QPushButton("Clear"); self.clear_pc_button.clicked.connect(lambda: self._clear_linked_document("PostalCharter"))
        link_pc_layout.addWidget(self.postal_charter_ref_input); link_pc_layout.addWidget(self.browse_pc_button); link_pc_layout.addWidget(self.clear_pc_button)
        deposit_details_layout.addLayout(link_pc_layout)
        self.upu_tracking_number_label = QLabel("UPU Tracking Number:"); self.upu_tracking_number_input = QLineEdit(); self.upu_tracking_number_input.setPlaceholderText("UPU tracking if applicable")
        deposit_details_layout.addWidget(self.upu_tracking_number_label); deposit_details_layout.addWidget(self.upu_tracking_number_input)
        self.jurisdictional_delivery_tag_label = QLabel("Jurisdictional Delivery Tag:"); self.jurisdictional_delivery_tag_display = QLabel("N/A");
        deposit_details_layout.addWidget(self.jurisdictional_delivery_tag_label); deposit_details_layout.addWidget(self.jurisdictional_delivery_tag_display)
        deposit_details_group.setLayout(deposit_details_layout); main_layout.addWidget(deposit_details_group)

        clauses_group = QGroupBox("Clauses"); clauses_layout = QVBoxLayout() # Details omitted
        self.clauses_list_widget = QListWidget(); self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)
        self.selected_clause_details_group = QGroupBox("Selected Clause Details") # Details omitted
        selected_clause_layout = QGridLayout(); self.sel_clause_id_label = QLabel("ID:"); self.sel_clause_id_value = QLabel("") # etc.
        selected_clause_layout.addWidget(self.sel_clause_id_label,0,0); selected_clause_layout.addWidget(self.sel_clause_id_value,0,1)
        self.sel_clause_display_number_label = QLabel("Display No.:"); self.sel_clause_display_number_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_display_number_label, 1, 0); selected_clause_layout.addWidget(self.sel_clause_display_number_value, 1, 1)
        self.sel_clause_text_label = QLabel("Text:"); self.sel_clause_text_value = QTextEdit(); self.sel_clause_text_value.setReadOnly(True)
        selected_clause_layout.addWidget(self.sel_clause_text_label, 4,0); selected_clause_layout.addWidget(self.sel_clause_text_value, 5,0,1,2)
        self.sel_clause_lock_status_label = QLabel("Status:"); self.sel_clause_lock_status_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_lock_status_label, 12, 0); selected_clause_layout.addWidget(self.sel_clause_lock_status_value, 12, 1)
        buttons_sel_clause_layout = QHBoxLayout()
        self.edit_selected_clause_button = QPushButton("Edit Selected Clause"); self.edit_selected_clause_button.setEnabled(False); self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)
        self.generate_qr_button = QPushButton("Generate QR Code"); self.generate_qr_button.setEnabled(False); self.generate_qr_button.clicked.connect(self._generate_clause_qr_code)
        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button); buttons_sel_clause_layout.addWidget(self.generate_qr_button)
        selected_clause_layout.addLayout(buttons_sel_clause_layout, 13, 0, 1, 2)
        self.selected_clause_details_group.setLayout(selected_clause_layout); self.selected_clause_details_group.setVisible(False)
        clauses_layout.addWidget(self.selected_clause_details_group)
        clause_action_buttons_layout = QHBoxLayout()
        self.add_clause_button = QPushButton("Add New Clause"); self.add_clause_button.clicked.connect(self.add_clause)
        self.remove_clause_button = QPushButton("Remove Selected Clause"); self.remove_clause_button.setEnabled(False); self.remove_clause_button.clicked.connect(self.remove_selected_clause)
        self.move_clause_up_button = QPushButton("Move Up"); self.move_clause_up_button.setEnabled(False); self.move_clause_up_button.clicked.connect(self.move_clause_up)
        self.move_clause_down_button = QPushButton("Move Down"); self.move_clause_down_button.setEnabled(False); self.move_clause_down_button.clicked.connect(self.move_clause_down)
        clause_action_buttons_layout.addWidget(self.add_clause_button); clause_action_buttons_layout.addWidget(self.remove_clause_button); clause_action_buttons_layout.addWidget(self.move_clause_up_button); clause_action_buttons_layout.addWidget(self.move_clause_down_button)
        clauses_layout.addLayout(clause_action_buttons_layout)
        app_action_buttons_layout = QHBoxLayout()
        self.undo_action_button = QPushButton("Undo Clause Op"); self.undo_action_button.setToolTip("Undo last clause operation"); self.undo_action_button.clicked.connect(self._undo_last_command)
        self.redo_action_button = QPushButton("Redo Clause Op"); self.redo_action_button.setToolTip("Redo last undone clause operation"); self.redo_action_button.clicked.connect(self._redo_last_command)
        app_action_buttons_layout.addStretch(); app_action_buttons_layout.addWidget(self.undo_action_button); app_action_buttons_layout.addWidget(self.redo_action_button)
        clauses_layout.addLayout(app_action_buttons_layout)
        clauses_group.setLayout(clauses_layout); main_layout.addWidget(clauses_group)

        file_ops_layout = QHBoxLayout() # Details omitted
        self.new_button = QPushButton("New Deposit Document"); self.new_button.clicked.connect(self.new_document)
        self.save_button = QPushButton("Save Deposit"); self.save_button.clicked.connect(self.save_document)
        self.load_button = QPushButton("Load Deposit"); self.load_button.clicked.connect(self.load_document)
        file_ops_layout.addWidget(self.new_button); file_ops_layout.addWidget(self.save_button); file_ops_layout.addWidget(self.load_button)
        main_layout.addLayout(file_ops_layout)
        conformance_layout = QHBoxLayout() # Details omitted
        self.conformance_check_button = QPushButton("Run Basic Conformance Check"); self.conformance_check_button.clicked.connect(self.run_basic_conformance_check)
        self.create_github_issue_button = QPushButton("Create GitHub Issue"); self.create_github_issue_button.clicked.connect(self._create_github_issue_for_conformance); self.create_github_issue_button.setVisible(False)
        conformance_layout.addWidget(self.conformance_check_button); conformance_layout.addWidget(self.create_github_issue_button); conformance_layout.addStretch()
        main_layout.addLayout(conformance_layout)
        main_layout.addStretch(); self.load_document_data_into_ui()

    def _update_undo_redo_button_states(self):
        self.undo_action_button.setEnabled(bool(self.undo_stack))
        self.redo_action_button.setEnabled(bool(self.redo_stack))

    def _add_command_and_execute(self, command: Command):
        command.execute(); self.undo_stack.append(command)
        self.redo_stack.clear(); self._update_undo_redo_button_states()
        self._mark_as_modified()

    def _undo_last_command(self):
        if self.undo_stack:
            command = self.undo_stack.pop(); command.undo()
            self.redo_stack.append(command); self._update_undo_redo_button_states()
            self._mark_as_modified(); self._refresh_clause_list_display(); self.display_selected_clause_details()

    def _redo_last_command(self):
        if self.redo_stack:
            command = self.redo_stack.pop(); command.execute()
            self.undo_stack.append(command); self._update_undo_redo_button_states()
            self._mark_as_modified(); self._refresh_clause_list_display(); self.display_selected_clause_details()

    def _update_document_jurisdiction_direct(self, text: str):
        if self.document.jurisdiction != text:
            self.document.jurisdiction = text
            self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
            self._mark_as_modified()

    def _update_family_trust_ref_direct(self, text: str):
        ref_text = text.strip() or None
        if self.document.family_trust_ref != ref_text:
            self.document.family_trust_ref = ref_text
            self._mark_as_modified()

    def _update_postal_charter_ref_direct(self, text: str):
        ref_text = text.strip() or None
        if self.document.postal_charter_ref != ref_text:
            self.document.postal_charter_ref = ref_text
            self._mark_as_modified()

    def _update_upu_tracking_and_delivery_tag_direct(self, text=None):
        upu_number = self.upu_tracking_number_input.text().strip()
        if self.document.upu_tracking_number != upu_number:
            self.document.upu_tracking_number = upu_number
            self._generate_and_set_delivery_tag()
        elif not upu_number and self.document.jurisdictional_delivery_tag is not None:
             self._generate_and_set_delivery_tag()


    def _collect_data_from_ui(self):
        self.document.name = self.name_input.text()
        self.document.jurisdiction = self.jurisdiction_input.text()
        filed_docs_list = []
        for line in self.filed_docs_input.toPlainText().splitlines():
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2: filed_docs_list.append({"doc_name": parts[0].strip(), "details": parts[1].strip()})
                else: filed_docs_list.append({"doc_name": parts[0].strip(), "details": ""})
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
        if self.document.upu_tracking_number: self._generate_and_set_delivery_tag()
        else: self.document.jurisdictional_delivery_tag = None

    def _generate_and_set_delivery_tag(self): # As before
        if self.document.upu_tracking_number:
            year = datetime.datetime.now().year
            sequence = self.document.upu_tracking_number[-4:] if len(self.document.upu_tracking_number) >= 4 else "001"
            prefix = "LEXPOST-CA-MB-UPU"; self.document.jurisdictional_delivery_tag = f"{prefix}-{year}-{sequence}"
        else: self.document.jurisdictional_delivery_tag = None
        self.jurisdictional_delivery_tag_display.setText(self.document.jurisdictional_delivery_tag or "N/A")
        self._mark_as_modified()

    def _refresh_clause_list_display(self): # As before
        current_selected_id = None
        if self.clauses_list_widget.currentItem(): current_selected_id = self.clauses_list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        self.clauses_list_widget.clear()
        if not self.document or not self.document.clauses: self.display_selected_clause_details(); return
        display_numbers = generate_display_clause_numbers(self.document.clauses)
        new_selected_row = -1
        for i, clause_obj in enumerate(self.document.clauses):
            display_number = display_numbers[i] if i < len(display_numbers) else "Err!"
            item_text = f"{display_number} {str(clause_obj)}"
            if clause_obj.section_title: item_text = f"{display_number}"
            item = QListWidgetItem(item_text); item.setData(Qt.ItemDataRole.UserRole, clause_obj.id)
            if clause_obj.is_locked: pass
            self.clauses_list_widget.addItem(item)
            if clause_obj.id == current_selected_id: new_selected_row = i
        if new_selected_row != -1: self.clauses_list_widget.setCurrentRow(new_selected_row)
        else: self.display_selected_clause_details()


    def load_document_data_into_ui(self): # With undo/redo stack clearing
        self.name_input.setText(self.document.name); self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {self.document.jurisdiction}")
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
        self._refresh_clause_list_display(); self.is_modified = False
        self.undo_stack.clear(); self.redo_stack.clear(); self._update_undo_redo_button_states()
        main_window_instance = self.window()
        if hasattr(main_window_instance, 'settings_view') and \
           main_window_instance.settings_view.get_setting("enforce_clauseconformer_all_docs"):
            self.run_basic_conformance_check(is_auto_check=True)

    def new_document(self): # With undo/redo stack clearing
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e: print(f"Error untracking deposit {self.document.id}: {e}")
        self.document = MichaudSpecialDepositDocument(name="Untitled Special Deposit Document")
        self.current_document_path = None; self.is_modified = False
        self.load_document_data_into_ui() # Will clear stacks
        QMessageBox.information(self, "New Document", "New Special Deposit document initialized.")

    def add_clause(self):
        dialog = EditClauseDialog(default_jurisdiction=self.document.jurisdiction, parent=self)
        if dialog.exec():
            new_clause_obj = dialog.get_clause()
            current_row = self.clauses_list_widget.currentRow()
            insert_at_index = current_row + 1 if current_row != -1 and self.clauses_list_widget.count() > 0 else len(self.document.clauses)
            add_command = AddClauseCommand(self.document.clauses, new_clause_obj, insert_index=insert_at_index)
            self._add_command_and_execute(add_command)
            self._refresh_clause_list_display()
            for i in range(self.clauses_list_widget.count()):
                if self.clauses_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == new_clause_obj.id:
                    self.clauses_list_widget.setCurrentRow(i); break

    def display_selected_clause_details(self): # As before (ensure all fields populated)
        # ... (implementation similar to TrustView, condensed) ...
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]; clause_id = list_item.data(Qt.ItemDataRole.UserRole)
            clause_obj = next((c for c in self.document.clauses if c.id == clause_id), None)
            current_row = self.clauses_list_widget.row(list_item)
            if clause_obj:
                display_numbers = generate_display_clause_numbers(self.document.clauses)
                self.sel_clause_display_number_value.setText(display_numbers[current_row] if current_row < len(display_numbers) else "N/A")
                self.sel_clause_id_value.setText(clause_obj.id) # And other fields...
                self.sel_clause_text_value.setPlainText(clause_obj.text)
                self.sel_clause_lock_status_value.setText("🔒 Locked" if clause_obj.is_locked else "✏️ Editable")
                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True); self.remove_clause_button.setEnabled(True)
                # ... move buttons, qr button ...
            else: self.selected_clause_details_group.setVisible(False)
        else: self.selected_clause_details_group.setVisible(False)

    def edit_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Edit", "No clause selected."); return
        clause_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        clause_to_edit = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_to_edit:
            old_attrs = { "text": clause_to_edit.text, "jurisdiction": clause_to_edit.jurisdiction, "origin": clause_to_edit.origin,
                          "level": clause_to_edit.level, "section_title": clause_to_edit.section_title,
                          "metadata": clause_to_edit.metadata.copy(), "is_locked": clause_to_edit.is_locked,
                          "version": clause_to_edit.version, "last_modified_date": clause_to_edit.last_modified_date }
            dialog = EditClauseDialog(clause=clause_to_edit, parent=self)
            if dialog.exec():
                updated_clause_obj = dialog.get_clause()
                new_attrs = { "text": updated_clause_obj.text, "jurisdiction": updated_clause_obj.jurisdiction, "origin": updated_clause_obj.origin,
                              "level": updated_clause_obj.level, "section_title": updated_clause_obj.section_title,
                              "metadata": updated_clause_obj.metadata.copy(), "is_locked": updated_clause_obj.is_locked }
                changed_new_attrs = {k: v for k, v in new_attrs.items() if old_attrs.get(k) != v or (isinstance(v, dict) and old_attrs.get(k) != v) or k not in old_attrs}
                if not changed_new_attrs and old_attrs['is_locked'] != new_attrs['is_locked']: changed_new_attrs['is_locked'] = new_attrs['is_locked']
                if changed_new_attrs:
                    precise_old_attrs = {k: old_attrs[k] for k in changed_new_attrs.keys() if k in old_attrs}
                    if 'version' not in precise_old_attrs: precise_old_attrs['version'] = old_attrs['version']
                    if 'last_modified_date' not in precise_old_attrs: precise_old_attrs['last_modified_date'] = old_attrs['last_modified_date']
                    edit_command = EditClauseCommand(clause_to_edit, precise_old_attrs, changed_new_attrs)
                    self._add_command_and_execute(edit_command)
                self._refresh_clause_list_display()
                for i in range(self.clauses_list_widget.count()):
                    if self.clauses_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == clause_id:
                        self.clauses_list_widget.setCurrentRow(i); break
        else: QMessageBox.critical(self, "Error", f"Could not find ID {clause_id} to edit.")

    def remove_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Remove", "No clause selected."); return
        current_row = self.clauses_list_widget.row(selected_items[0])
        if not (0 <= current_row < len(self.document.clauses)): return
        clause_to_remove = self.document.clauses[current_row]
        reply = QMessageBox.question(self, "Remove", f"Remove: {str(clause_to_remove)}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            remove_command = RemoveClauseCommand(self.document.clauses, clause_to_remove, current_row)
            self._add_command_and_execute(remove_command)
            self._refresh_clause_list_display()

    def move_clause_up(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row > 0:
            clause_to_move = self.document.clauses[current_row]
            move_command = MoveClauseCommand(self.document.clauses, clause_to_move, current_row, current_row - 1)
            self._add_command_and_execute(move_command)
            self._refresh_clause_list_display(); self.clauses_list_widget.setCurrentRow(current_row - 1)

    def move_clause_down(self):
        current_row = self.clauses_list_widget.currentRow()
        if 0 <= current_row < len(self.document.clauses) - 1:
            clause_to_move = self.document.clauses[current_row]
            move_command = MoveClauseCommand(self.document.clauses, clause_to_move, current_row, current_row + 1)
            self._add_command_and_execute(move_command)
            self._refresh_clause_list_display(); self.clauses_list_widget.setCurrentRow(current_row + 1)

    def _browse_linked_document(self, link_type: str):
        # ... (Implementation as in TrustView, adapted for Deposit's link types) ...
        if link_type == "FamilyTrust":
            doc_dir_name = "trusts"; file_filter = "MPEA Trust Files (*.mpea_trust);;All Files (*)"
            target_input_widget = self.family_trust_ref_input; model_attribute_name = "family_trust_ref"; dialog_title = "Select Linked Family Trust"
        elif link_type == "PostalCharter":
            doc_dir_name = "charters"; file_filter = "MPEA Charter Files (*.mpea_charter);;All Files (*)"
            target_input_widget = self.postal_charter_ref_input; model_attribute_name = "postal_charter_ref"; dialog_title = "Select Linked Postal Charter"
        else: QMessageBox.warning(self, "Error", f"Unknown link type: {link_type}"); return
        start_dir = os.path.join(CODEX_VAULT_DIR, doc_dir_name); os.makedirs(start_dir, exist_ok=True)
        filePath, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, file_filter)
        if filePath:
            try: relative_path = os.path.relpath(filePath, CODEX_VAULT_DIR); display_path = relative_path
            except ValueError: display_path = filePath
            if os.path.isabs(display_path) and filePath.startswith(os.path.abspath(CODEX_VAULT_DIR)):
                 display_path = os.path.relpath(filePath, CODEX_VAULT_DIR)
            target_input_widget.setText(display_path) # Will trigger direct update method
            QMessageBox.information(self, "Link Set", f"{link_type} linked to: {display_path}")

    def _clear_linked_document(self, link_type: str):
        if link_type == "FamilyTrust": self.family_trust_ref_input.clear()
        elif link_type == "PostalCharter": self.postal_charter_ref_input.clear()
        else: return
        QMessageBox.information(self, "Link Cleared", f"{link_type} link cleared.")

    # Placeholder for other methods similar to TrustView/CharterView
    def save_document(self, silent=False): self._collect_data_from_ui(); print(f"DepositView Save: {self.document.name} (Silent: {silent})")
    def save_document_as(self, silent=False): self._collect_data_from_ui(); print(f"DepositView Save As: {self.document.name} (Silent: {silent})")
    def load_document(self): print("DepositView Load Triggered"); self.undo_stack.clear(); self.redo_stack.clear(); self._update_undo_redo_button_states()
    def _validate_document_basic(self) -> bool: return True
    def _generate_clause_qr_code(self): print("DepositView QR Gen Triggered")
    def run_basic_conformance_check(self, is_auto_check=False): print(f"DepositView Conformance Check (Auto: {is_auto_check})")
    def _create_github_issue_for_conformance(self): print("DepositView Create GitHub Issue Triggered")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    deposit_view = DepositView()
    deposit_view.setWindowTitle("Test Michaud Special Deposit View")
    deposit_view.setGeometry(100,100, 850, 750)
    deposit_view.show()
    sys.exit(app.exec())

# Note on direct edits vs commands:
# Similar to other views, direct edits to main document fields are handled by _connect_ui_signals_to_model_direct_updates
# and are not part of the clause operation undo/redo system.
# new_document() and load_document() clear the undo/redo stacks.
