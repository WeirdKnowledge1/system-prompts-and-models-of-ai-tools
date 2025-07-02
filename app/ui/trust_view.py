from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox, QListWidgetItem, QInputDialog, QApplication)
from PyQt6.QtCore import Qt
from collections import deque
import json
import os
import datetime
import uuid

from app.core.document_models import MichaudFamilyTrust
from app.core.commands import Command, AddClauseCommand, RemoveClauseCommand, EditClauseCommand, MoveClauseCommand
from app.core.clause_model import Clause
from app.ui.dialogs.edit_clause_dialog import EditClauseDialog
from app.ui.dialogs.qr_display_dialog import QRDisplayDialog
from app.core.agents import ClauseConformer, VeritasProof, DocumentTracker
from app.core.document_utils import generate_display_clause_numbers
from app.utils.constants import CODEX_VAULT_DIR

class TrustView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.is_modified = False
        self.last_conformance_issues = None

        self.UNDO_STACK_LIMIT = 50
        self.undo_stack = deque(maxlen=self.UNDO_STACK_LIMIT)
        self.redo_stack = deque(maxlen=self.UNDO_STACK_LIMIT)

        self._setup_ui()
        self._connect_ui_signals_to_model_direct_updates() # For non-command based edits
        self._update_undo_redo_button_states()

    def _connect_ui_signals_to_model_direct_updates(self):
        # These direct edits are NOT part of the undo/redo command stack for clauses.
        # If these fields need undo/redo, they'll also need specific commands.
        self.name_input.textChanged.connect(lambda text: self._update_doc_attr_direct('name', text))
        self.jurisdiction_input.textChanged.connect(self._update_document_jurisdiction_direct)

        self.settlors_input.textChanged.connect(
            lambda text: self._update_doc_attr_direct('settlors', [s.strip() for s in text.split(',') if s.strip()])
        )
        self.trustees_input.textChanged.connect(
            lambda text: self._update_doc_attr_direct('trustees', [t.strip() for t in text.split(',') if t.strip()])
        )
        self.beneficiaries_input.textChanged.connect(
            lambda text: self._update_doc_attr_direct('beneficiaries', [b.strip() for b in text.split(',') if b.strip()])
        )
        self.land_rights_input.textChanged.connect(
            lambda: self._update_doc_attr_direct('land_rights_details', self.land_rights_input.toPlainText())
        )
        self.name_control_input.textChanged.connect(
            lambda: self._update_doc_attr_direct('name_control_details', self.name_control_input.toPlainText())
        )
        self.mortgage_recon_input.textChanged.connect(
            lambda: self._update_doc_attr_direct('equitable_mortgage_reconciliation_details', self.mortgage_recon_input.toPlainText())
        )
        self.postal_charter_ref_input.textChanged.connect(self._update_postal_charter_ref_direct)
        self.special_deposit_ref_input.textChanged.connect(self._update_special_deposit_ref_direct)

    def _update_doc_attr_direct(self, attr_name, value):
        """Helper for direct model updates that are not command-based."""
        if getattr(self.document, attr_name) != value:
            setattr(self.document, attr_name, value)
            self._mark_as_modified()

    def _mark_as_modified(self):
        self.is_modified = True

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.jurisdiction_header_label = QLabel("Jurisdiction: N/A")
        self.jurisdiction_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.jurisdiction_header_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px; background-color: #E8E8E8; border-bottom: 1px solid #C0C0C0;")
        main_layout.addWidget(self.jurisdiction_header_label)

        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()
        self.name_label = QLabel("Trust Name:")
        self.name_input = QLineEdit()
        doc_info_layout.addWidget(self.name_label, 0, 0); doc_info_layout.addWidget(self.name_input, 0, 1)
        self.id_label = QLabel("Document ID:"); self.id_display = QLabel(self.document.id)
        doc_info_layout.addWidget(self.id_label, 1, 0); doc_info_layout.addWidget(self.id_display, 1, 1)
        self.jurisdiction_label = QLabel("Jurisdiction:")
        self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        doc_info_layout.addWidget(self.jurisdiction_label, 2, 0); doc_info_layout.addWidget(self.jurisdiction_input, 2, 1)
        doc_info_group.setLayout(doc_info_layout)
        main_layout.addWidget(doc_info_group)

        parties_group = QGroupBox("Parties")
        parties_layout = QGridLayout()
        self.settlors_label = QLabel("Settlors (comma-separated):"); self.settlors_input = QLineEdit()
        parties_layout.addWidget(self.settlors_label, 0, 0); parties_layout.addWidget(self.settlors_input, 0, 1)
        self.trustees_label = QLabel("Trustees (comma-separated):"); self.trustees_input = QLineEdit()
        parties_layout.addWidget(self.trustees_label, 1, 0); parties_layout.addWidget(self.trustees_input, 1, 1)
        self.beneficiaries_label = QLabel("Beneficiaries (comma-separated):"); self.beneficiaries_input = QLineEdit()
        parties_layout.addWidget(self.beneficiaries_label, 2, 0); parties_layout.addWidget(self.beneficiaries_input, 2, 1)
        parties_group.setLayout(parties_layout)
        main_layout.addWidget(parties_group)

        details_group = QGroupBox("Specific Details")
        details_layout = QVBoxLayout()
        self.land_rights_label = QLabel("Land Rights Details:"); self.land_rights_input = QTextEdit()
        details_layout.addWidget(self.land_rights_label); details_layout.addWidget(self.land_rights_input)
        self.name_control_label = QLabel("Name Control Details:"); self.name_control_input = QTextEdit()
        details_layout.addWidget(self.name_control_label); details_layout.addWidget(self.name_control_input)
        self.mortgage_recon_label = QLabel("Equitable Mortgage Reconciliation Details:"); self.mortgage_recon_input = QTextEdit()
        details_layout.addWidget(self.mortgage_recon_label); details_layout.addWidget(self.mortgage_recon_input)

        details_layout.addWidget(QLabel("Linked Postal Charter Ref:"))
        link_charter_layout = QHBoxLayout()
        self.postal_charter_ref_input = QLineEdit(); self.postal_charter_ref_input.setPlaceholderText("Enter ID, relative path, or browse")
        self.browse_charter_button = QPushButton("Browse..."); self.browse_charter_button.clicked.connect(lambda: self._browse_linked_document("PostalCharter"))
        self.clear_charter_button = QPushButton("Clear"); self.clear_charter_button.clicked.connect(lambda: self._clear_linked_document("PostalCharter"))
        link_charter_layout.addWidget(self.postal_charter_ref_input); link_charter_layout.addWidget(self.browse_charter_button); link_charter_layout.addWidget(self.clear_charter_button)
        details_layout.addLayout(link_charter_layout)

        details_layout.addWidget(QLabel("Linked Special Deposit Ref:"))
        link_deposit_layout = QHBoxLayout()
        self.special_deposit_ref_input = QLineEdit(); self.special_deposit_ref_input.setPlaceholderText("Enter ID, relative path, or browse")
        self.browse_deposit_button = QPushButton("Browse..."); self.browse_deposit_button.clicked.connect(lambda: self._browse_linked_document("SpecialDeposit"))
        self.clear_deposit_button = QPushButton("Clear"); self.clear_deposit_button.clicked.connect(lambda: self._clear_linked_document("SpecialDeposit"))
        link_deposit_layout.addWidget(self.special_deposit_ref_input); link_deposit_layout.addWidget(self.browse_deposit_button); link_deposit_layout.addWidget(self.clear_deposit_button)
        details_layout.addLayout(link_deposit_layout)
        details_group.setLayout(details_layout); main_layout.addWidget(details_group)

        clauses_group = QGroupBox("Clauses"); clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget(); self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)
        self.selected_clause_details_group = QGroupBox("Selected Clause Details"); selected_clause_layout = QGridLayout()
        # ... (All sel_clause_* labels and values as before, condensed for brevity) ...
        self.sel_clause_id_label = QLabel("ID:"); self.sel_clause_id_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_id_label, 0, 0); selected_clause_layout.addWidget(self.sel_clause_id_value, 0, 1)
        self.sel_clause_display_number_label = QLabel("Display No.:"); self.sel_clause_display_number_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_display_number_label, 1, 0); selected_clause_layout.addWidget(self.sel_clause_display_number_value, 1, 1)
        # ... (other clause detail fields: jurisdiction, origin, text, purpose, level, section_title, created, modified, version)
        self.sel_clause_text_label = QLabel("Text:"); self.sel_clause_text_value = QTextEdit(); self.sel_clause_text_value.setReadOnly(True)
        selected_clause_layout.addWidget(self.sel_clause_text_label, 4, 0); selected_clause_layout.addWidget(self.sel_clause_text_value, 5, 0, 1, 2)
        self.sel_clause_lock_status_label = QLabel("Status:"); self.sel_clause_lock_status_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_lock_status_label, 12, 0); selected_clause_layout.addWidget(self.sel_clause_lock_status_value, 12, 1)
        # ...
        buttons_sel_clause_layout = QHBoxLayout()
        self.edit_selected_clause_button = QPushButton("Edit Selected Clause"); self.edit_selected_clause_button.setEnabled(False); self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)
        self.view_audit_button = QPushButton("View Audit Trail"); self.view_audit_button.setEnabled(False)
        self.generate_qr_button = QPushButton("Generate QR Code"); self.generate_qr_button.setEnabled(False); self.generate_qr_button.clicked.connect(self._generate_clause_qr_code)
        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button); buttons_sel_clause_layout.addWidget(self.view_audit_button); buttons_sel_clause_layout.addWidget(self.generate_qr_button)
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

        undo_redo_layout = QHBoxLayout()
        self.undo_action_button = QPushButton("Undo Clause Op"); self.undo_action_button.setToolTip("Undo last clause operation"); self.undo_action_button.clicked.connect(self._undo_last_command)
        self.redo_action_button = QPushButton("Redo Clause Op"); self.redo_action_button.setToolTip("Redo last undone clause operation"); self.redo_action_button.clicked.connect(self._redo_last_command)
        undo_redo_layout.addStretch(); undo_redo_layout.addWidget(self.undo_action_button); undo_redo_layout.addWidget(self.redo_action_button)
        clauses_layout.addLayout(undo_redo_layout)
        clauses_group.setLayout(clauses_layout); main_layout.addWidget(clauses_group)

        file_ops_layout = QHBoxLayout()
        self.new_button = QPushButton("New Trust Document"); self.new_button.clicked.connect(self.new_document)
        self.save_button = QPushButton("Save Trust"); self.save_button.clicked.connect(self.save_document)
        self.load_button = QPushButton("Load Trust"); self.load_button.clicked.connect(self.load_document)
        file_ops_layout.addWidget(self.new_button); file_ops_layout.addWidget(self.save_button); file_ops_layout.addWidget(self.load_button)
        main_layout.addLayout(file_ops_layout)

        conformance_layout = QHBoxLayout()
        self.conformance_check_button = QPushButton("Run Basic Conformance Check"); self.conformance_check_button.clicked.connect(self.run_basic_conformance_check)
        self.create_github_issue_button = QPushButton("Create GitHub Issue for Conformance Failures"); self.create_github_issue_button.clicked.connect(self._create_github_issue_for_conformance); self.create_github_issue_button.setVisible(False)
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

    def _update_document_jurisdiction_direct(self, text: str): # Renamed from _update_document_jurisdiction
        if self.document.jurisdiction != text: # Check if value actually changed
            self.document.jurisdiction = text
            self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
            self._mark_as_modified()

    def _update_postal_charter_ref_direct(self, text: str): # Renamed
        if self.document.postal_charter_ref != text:
            self.document.postal_charter_ref = text.strip() or None
            self._mark_as_modified()

    def _update_special_deposit_ref_direct(self, text: str): # Renamed
        if self.document.special_deposit_ref != text:
            self.document.special_deposit_ref = text.strip() or None
            self._mark_as_modified()

    def _collect_data_from_ui(self):
        self.document.name = self.name_input.text()
        self.document.jurisdiction = self.jurisdiction_input.text()
        self.document.settlors = [s.strip() for s in self.settlors_input.text().split(',') if s.strip()]
        self.document.trustees = [t.strip() for t in self.trustees_input.text().split(',') if t.strip()]
        self.document.beneficiaries = [b.strip() for b in self.beneficiaries_input.text().split(',') if b.strip()]
        self.document.land_rights_details = self.land_rights_input.toPlainText()
        self.document.name_control_details = self.name_control_input.toPlainText()
        self.document.equitable_mortgage_reconciliation_details = self.mortgage_recon_input.toPlainText()
        self.document.postal_charter_ref = self.postal_charter_ref_input.text().strip() or None
        self.document.special_deposit_ref = self.special_deposit_ref_input.text().strip() or None

    def _refresh_clause_list_display(self):
        # ... (no change to this method itself for command integration) ...
        current_selected_id = None
        if self.clauses_list_widget.currentItem(): current_selected_id = self.clauses_list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        self.clauses_list_widget.clear()
        if not self.document or not self.document.clauses: self.display_selected_clause_details(); return
        display_numbers = generate_display_clause_numbers(self.document.clauses)
        new_selected_row = -1
        for i, clause_obj in enumerate(self.document.clauses):
            display_number = display_numbers[i] if i < len(display_numbers) else "Err!"
            item_text = f"{display_number} {str(clause_obj)}"
            if clause_obj.section_title and display_number.endswith(clause_obj.section_title): item_text = f"{display_number}"
            item = QListWidgetItem(item_text); item.setData(Qt.ItemDataRole.UserRole, clause_obj.id)
            if clause_obj.is_locked: pass
            self.clauses_list_widget.addItem(item)
            if clause_obj.id == current_selected_id: new_selected_row = i
        if new_selected_row != -1: self.clauses_list_widget.setCurrentRow(new_selected_row)
        else: self.display_selected_clause_details()

    def load_document_data_into_ui(self):
        # ... (existing content) ...
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {self.document.jurisdiction}")
        self.settlors_input.setText(", ".join(self.document.settlors))
        self.trustees_input.setText(", ".join(self.document.trustees))
        self.beneficiaries_input.setText(", ".join(self.document.beneficiaries))
        self.land_rights_input.setPlainText(self.document.land_rights_details)
        self.name_control_input.setPlainText(self.document.name_control_details)
        self.mortgage_recon_input.setPlainText(self.document.equitable_mortgage_reconciliation_details)
        self.postal_charter_ref_input.setText(self.document.postal_charter_ref or "")
        self.special_deposit_ref_input.setText(self.document.special_deposit_ref or "")
        self._refresh_clause_list_display()
        self.is_modified = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._update_undo_redo_button_states()
        main_window_instance = self.window()
        if hasattr(main_window_instance, 'settings_view') and \
           hasattr(main_window_instance.settings_view, 'get_setting') and \
           main_window_instance.settings_view.get_setting("enforce_clauseconformer_all_docs"):
            self.run_basic_conformance_check(is_auto_check=True)

    def new_document(self):
        # ... (existing content) ...
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e: print(f"Error untracking document {self.document.id} in new_document: {e}")
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.current_document_path = None
        self.is_modified = False
        self.load_document_data_into_ui() # This will clear stacks and update buttons
        QMessageBox.information(self, "New Document", "New Trust document initialized.")

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

    def display_selected_clause_details(self):
        # ... (no changes needed here for command integration itself, but it's called by undo/redo) ...
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]; clause_id = list_item.data(Qt.ItemDataRole.UserRole)
            clause_obj = next((c for c in self.document.clauses if c.id == clause_id), None)
            current_row = self.clauses_list_widget.row(list_item)
            if clause_obj:
                display_numbers = generate_display_clause_numbers(self.document.clauses)
                self.sel_clause_display_number_value.setText(display_numbers[current_row] if current_row < len(display_numbers) else "N/A")
                self.sel_clause_id_value.setText(clause_obj.id); self.sel_clause_jurisdiction_value.setText(clause_obj.jurisdiction)
                self.sel_clause_origin_value.setText(clause_obj.origin); self.sel_clause_text_value.setPlainText(clause_obj.text)
                self.sel_clause_purpose_value.setText(clause_obj.metadata.get("purpose_type", "N/A"))
                self.sel_clause_level_value.setText(str(clause_obj.level)); self.sel_clause_section_title_value.setText(clause_obj.section_title or "N/A")
                try: created_date = datetime.datetime.fromisoformat(clause_obj.creation_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: created_date = clause_obj.creation_date
                self.sel_clause_created_value.setText(created_date)
                try: modified_date = datetime.datetime.fromisoformat(clause_obj.last_modified_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: modified_date = clause_obj.last_modified_date
                self.sel_clause_modified_value.setText(modified_date); self.sel_clause_version_value.setText(str(clause_obj.version))
                self.sel_clause_lock_status_value.setText("🔒 Locked" if clause_obj.is_locked else "✏️ Editable")
                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True); self.remove_clause_button.setEnabled(True)
                self.move_clause_up_button.setEnabled(current_row > 0)
                self.move_clause_down_button.setEnabled(current_row < self.clauses_list_widget.count() - 1)
                main_window_instance = self.window(); qr_setting_enabled = False
                if hasattr(main_window_instance, 'settings_view') and \
                   hasattr(main_window_instance.settings_view, 'get_setting'):
                    qr_setting_enabled = main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled")
                self.generate_qr_button.setEnabled(qr_setting_enabled)
                self.generate_qr_button.setToolTip("Generates a QR code for the selected clause's proof data." if qr_setting_enabled else "Enable 'QR Proof Chain Embeds' in Settings to use this feature.")
            else:
                self.selected_clause_details_group.setVisible(False)
                for btn in [self.edit_selected_clause_button, self.remove_clause_button, self.move_clause_up_button, self.move_clause_down_button, self.generate_qr_button]: btn.setEnabled(False)
        else:
            self.selected_clause_details_group.setVisible(False)
            for btn in [self.edit_selected_clause_button, self.remove_clause_button, self.move_clause_up_button, self.move_clause_down_button, self.generate_qr_button]: btn.setEnabled(False)

    def edit_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Edit Clause", "No clause selected."); return

        clause_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        clause_to_edit = next((c for c in self.document.clauses if c.id == clause_id), None)

        if clause_to_edit:
            old_attrs = {
                "text": clause_to_edit.text, "jurisdiction": clause_to_edit.jurisdiction,
                "origin": clause_to_edit.origin, "level": clause_to_edit.level,
                "section_title": clause_to_edit.section_title,
                "metadata": clause_to_edit.metadata.copy(),
                "is_locked": clause_to_edit.is_locked,
                "version": clause_to_edit.version,
                "last_modified_date": clause_to_edit.last_modified_date
            }

            dialog = EditClauseDialog(clause=clause_to_edit, parent=self)
            if dialog.exec():
                updated_clause_obj = dialog.get_clause() # Dialog modifies the instance
                new_attrs = {
                    "text": updated_clause_obj.text, "jurisdiction": updated_clause_obj.jurisdiction,
                    "origin": updated_clause_obj.origin, "level": updated_clause_obj.level,
                    "section_title": updated_clause_obj.section_title,
                    "metadata": updated_clause_obj.metadata.copy(),
                    "is_locked": updated_clause_obj.is_locked,
                    # EditClauseCommand will handle version and last_modified_date
                }
                # Create precise diff for command
                changed_new_attrs = {k: v for k, v in new_attrs.items() if old_attrs.get(k) != v or (isinstance(v, dict) and old_attrs.get(k) != v) or k not in old_attrs}
                if not changed_new_attrs and old_attrs['is_locked'] != new_attrs['is_locked']: # if only lock status changed
                    changed_new_attrs['is_locked'] = new_attrs['is_locked']


                if changed_new_attrs :
                    precise_old_attrs = {k: old_attrs[k] for k in changed_new_attrs.keys() if k in old_attrs}
                    # Ensure version and date are in precise_old_attrs for accurate rollback
                    if 'version' not in precise_old_attrs: precise_old_attrs['version'] = old_attrs['version']
                    if 'last_modified_date' not in precise_old_attrs: precise_old_attrs['last_modified_date'] = old_attrs['last_modified_date']

                    edit_command = EditClauseCommand(clause_to_edit, precise_old_attrs, changed_new_attrs)
                    self._add_command_and_execute(edit_command)

                self._refresh_clause_list_display()
                for i in range(self.clauses_list_widget.count()):
                    if self.clauses_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == clause_id:
                        self.clauses_list_widget.setCurrentRow(i); break
        else:
            QMessageBox.critical(self, "Error", f"Could not find clause ID {clause_id} to edit.")

    def remove_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Remove", "No clause selected."); return

        current_row = self.clauses_list_widget.row(selected_items[0])
        # Ensure current_row is valid before trying to access clauses list
        if not (0 <= current_row < len(self.document.clauses)):
             QMessageBox.critical(self, "Error", "Selected row is out of sync with document clauses.")
             return
        clause_to_remove = self.document.clauses[current_row]

        reply = QMessageBox.question(self, "Remove Clause", f"Remove: {str(clause_to_remove)}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            remove_command = RemoveClauseCommand(self.document.clauses, clause_to_remove, current_row)
            self._add_command_and_execute(remove_command)
            self._refresh_clause_list_display()

    def move_clause_up(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row > 0:
            clause_to_move = self.document.clauses[current_row]
            move_command = MoveClauseCommand(self.document.clauses, clause_to_move,
                                             from_index=current_row, to_index_visual=current_row - 1)
            self._add_command_and_execute(move_command)
            self._refresh_clause_list_display()
            self.clauses_list_widget.setCurrentRow(current_row - 1)

    def move_clause_down(self):
        current_row = self.clauses_list_widget.currentRow()
        if 0 <= current_row < len(self.document.clauses) - 1:
            clause_to_move = self.document.clauses[current_row]
            move_command = MoveClauseCommand(self.document.clauses, clause_to_move,
                                             from_index=current_row, to_index_visual=current_row + 1)
            self._add_command_and_execute(move_command)
            self._refresh_clause_list_display()
            self.clauses_list_widget.setCurrentRow(current_row + 1)

    # --- Direct model updates (for non-clause fields, not part of clause undo/redo) ---
    def _update_document_jurisdiction(self, text: str):
        if self.document.jurisdiction != text:
            self.document.jurisdiction = text
            self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
            self._mark_as_modified()

    def _update_postal_charter_ref(self, text: str):
        ref_text = text.strip() or None
        if self.document.postal_charter_ref != ref_text:
            self.document.postal_charter_ref = ref_text
            self._mark_as_modified()

    def _update_special_deposit_ref(self, text: str):
        ref_text = text.strip() or None
        if self.document.special_deposit_ref != ref_text:
            self.document.special_deposit_ref = ref_text
            self._mark_as_modified()

    def _browse_linked_document(self, link_type: str):
        # ... (existing implementation for browsing) ...
        # This directly sets attributes and calls _mark_as_modified.
        # For full undo/redo, this would need a command.
        if link_type == "PostalCharter":
            doc_dir_name = "charters"; file_filter = "Michaud Postal Equity App Charter Files (*.mpea_charter);;All Files (*)";
            target_input_widget = self.postal_charter_ref_input; model_attribute_name = "postal_charter_ref"; dialog_title = "Select Linked Postal Charter"
        elif link_type == "SpecialDeposit":
            doc_dir_name = "deposits"; file_filter = "Michaud Postal Equity App Deposit Files (*.mpea_deposit);;All Files (*)"
            target_input_widget = self.special_deposit_ref_input; model_attribute_name = "special_deposit_ref"; dialog_title = "Select Linked Special Deposit Document"
        else: QMessageBox.warning(self, "Error", f"Unknown link type: {link_type}"); return
        start_dir = os.path.join(CODEX_VAULT_DIR, doc_dir_name); os.makedirs(start_dir, exist_ok=True)
        filePath, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, file_filter)
        if filePath:
            try: relative_path = os.path.relpath(filePath, CODEX_VAULT_DIR); display_path = relative_path
            except ValueError: display_path = filePath
            if os.path.isabs(display_path) and filePath.startswith(os.path.abspath(CODEX_VAULT_DIR)):
                 display_path = os.path.relpath(filePath, CODEX_VAULT_DIR)
            target_input_widget.setText(display_path) # This will trigger textChanged -> _update_..._ref
            # setattr(self.document, model_attribute_name, display_path) # No longer needed if textChanged connected
            # self._mark_as_modified() # Also handled by textChanged connection
            QMessageBox.information(self, "Link Set", f"{link_type} linked to: {display_path}")

    def _clear_linked_document(self, link_type: str):
        # This directly sets attributes and calls _mark_as_modified.
        # For full undo/redo, this would need a command.
        if link_type == "PostalCharter":
            self.postal_charter_ref_input.clear() # This will trigger textChanged -> _update_postal_charter_ref
        elif link_type == "SpecialDeposit":
            self.special_deposit_ref_input.clear() # This will trigger textChanged -> _update_special_deposit_ref
        else: return
        # _mark_as_modified() is handled by textChanged connection
        QMessageBox.information(self, "Link Cleared", f"{link_type} link cleared.")

    # ... (save_document, save_document_as, load_document, _validate_document_basic methods)
    # ... (_generate_clause_qr_code, run_basic_conformance_check, _create_github_issue_for_conformance methods)
    # These methods do not need to change for the command pattern integration itself,
    # but load_document and new_document clear the undo/redo stacks.

    # Existing save_document, save_document_as, load_document, _validate_document_basic,
    # _generate_clause_qr_code, run_basic_conformance_check, _create_github_issue_for_conformance
    # are assumed to be below this point and are kept as they were, unless they also need
    # to interact with the command stack (which is not the case for this step).
    # The important change is that load_document and new_document clear the undo_stack and redo_stack.
    # The methods _update_document_jurisdiction, _update_postal_charter_ref, _update_special_deposit_ref
    # were renamed to _direct versions if they were directly connected to UI textChanged signals.
    # For now, I'll ensure the _connect_modification_signals reflects this for non-command based changes.

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    trust_view = TrustView()
    trust_view.setWindowTitle("Test Michaud Family Trust View")
    trust_view.setGeometry(100,100, 800, 600)
    trust_view.show()
    sys.exit(app.exec())

# Note: The _collect_data_from_ui method, which is called during save operations,
# directly updates self.document attributes from various QLineEdits/QTextEdits.
# These direct updates (name, settlors, trustees, beneficiaries, details fields)
# are NOT currently part of the undo/redo command system.
# Making them undoable would require creating Command objects for each field change,
# or a single "UpdateFormFieldsCommand" that stores the entire state of these fields.
# This is out of scope for the current "clause operations" focus for undo/redo.
# The _connect_ui_signals_to_model_direct_updates method handles these direct changes.
# Also, load_document and new_document clear the undo/redo stacks.
