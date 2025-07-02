from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox, QListWidgetItem, QInputDialog, QApplication) # Added QInputDialog, QApplication
from PyQt6.QtCore import Qt
import json
import os
import datetime
import uuid

from app.core.document_models import MichaudFamilyPostalCharter
from app.core.clause_model import Clause # Clause __str__ now includes lock icon
from app.ui.dialogs.edit_clause_dialog import EditClauseDialog # Dialog handles lock checkbox and field states
from app.ui.dialogs.qr_display_dialog import QRDisplayDialog
from app.core.agents import ClauseConformer, VeritasProof, DocumentTracker
from app.core.document_utils import generate_display_clause_numbers
from app.utils.constants import CODEX_VAULT_DIR

class CharterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudFamilyPostalCharter(name="Untitled Michaud Family Postal Charter")
        self.is_modified = False
        self.last_conformance_issues = None # To store issues for GitHub reporting
        self._setup_ui()
        self._connect_modification_signals()

    def _connect_modification_signals(self):
        self.name_input.textChanged.connect(self._mark_as_modified)
        self.jurisdiction_input.textChanged.connect(self._mark_as_modified)
        self.upu_format_input.textChanged.connect(self._mark_as_modified)
        self.global_tracking_input.textChanged.connect(self._mark_as_modified)
        self.canada_post_input.textChanged.connect(self._mark_as_modified)
        self.usps_input.textChanged.connect(self._mark_as_modified)
        self.vienna_ref_input.textChanged.connect(self._mark_as_modified)
        self.postal_treaty_input.textChanged.connect(self._mark_as_modified)
        self.family_trust_ref_input.textChanged.connect(self._mark_as_modified)
        self.upu_tracking_number_input.textChanged.connect(self._mark_as_modified)

    def _mark_as_modified(self, text=None):
        self.is_modified = True

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.jurisdiction_header_label = QLabel("Jurisdiction: N/A")
        self.jurisdiction_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.jurisdiction_header_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px; background-color: #E8E8E8; border-bottom: 1px solid #C0C0C0;")
        main_layout.addWidget(self.jurisdiction_header_label)

        doc_info_group = QGroupBox("Document Information")
        doc_info_layout = QGridLayout()
        self.name_label = QLabel("Charter Name:")
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(lambda text: setattr(self.document, 'name', text))
        doc_info_layout.addWidget(self.name_label, 0, 0)
        doc_info_layout.addWidget(self.name_input, 0, 1)
        self.id_label = QLabel("Document ID:")
        self.id_display = QLabel(self.document.id)
        doc_info_layout.addWidget(self.id_label, 1, 0)
        doc_info_layout.addWidget(self.id_display, 1, 1)
        self.jurisdiction_label = QLabel("Jurisdiction:")
        self.jurisdiction_input = QLineEdit(self.document.jurisdiction)
        self.jurisdiction_input.textChanged.connect(self._update_document_jurisdiction)
        doc_info_layout.addWidget(self.jurisdiction_label, 2, 0)
        doc_info_layout.addWidget(self.jurisdiction_input, 2, 1)
        doc_info_group.setLayout(doc_info_layout)
        main_layout.addWidget(doc_info_group)

        charter_details_group = QGroupBox("Postal Charter Specifics")
        charter_details_layout = QVBoxLayout()
        self.upu_format_label = QLabel("UPU Recognized Format Details:")
        self.upu_format_input = QTextEdit()
        charter_details_layout.addWidget(self.upu_format_label)
        charter_details_layout.addWidget(self.upu_format_input)
        self.global_tracking_label = QLabel("Global UPU Tracking Number Fields:")
        self.global_tracking_input = QTextEdit()
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

        # Family Trust Reference with Browse
        self.family_trust_ref_label = QLabel("Family Trust Reference (ID/Path):")
        link_ft_layout = QHBoxLayout()
        self.family_trust_ref_input = QLineEdit(self.document.family_trust_ref or "")
        self.family_trust_ref_input.setPlaceholderText("Enter ID, relative path, or browse")
        self.family_trust_ref_input.textChanged.connect(self._update_family_trust_ref)
        self.browse_ft_button = QPushButton("Browse...")
        self.browse_ft_button.clicked.connect(lambda: self._browse_linked_document("FamilyTrust"))
        self.clear_ft_button = QPushButton("Clear") # New Clear Button
        self.clear_ft_button.clicked.connect(lambda: self._clear_linked_document("FamilyTrust")) # New Slot
        link_ft_layout.addWidget(self.family_trust_ref_input)
        link_ft_layout.addWidget(self.browse_ft_button)
        link_ft_layout.addWidget(self.clear_ft_button) # Add Clear button to layout
        charter_details_layout.addWidget(self.family_trust_ref_label)
        charter_details_layout.addLayout(link_ft_layout)

        self.upu_tracking_number_label = QLabel("UPU Tracking Number:")
        self.upu_tracking_number_input = QLineEdit()
        self.upu_tracking_number_input.setPlaceholderText("Enter UPU tracking number if applicable")
        self.upu_tracking_number_input.textChanged.connect(self._update_jurisdictional_delivery_tag)
        charter_details_layout.addWidget(self.upu_tracking_number_label)
        charter_details_layout.addWidget(self.upu_tracking_number_input)
        self.jurisdictional_delivery_tag_label = QLabel("Jurisdictional Delivery Tag:")
        self.jurisdictional_delivery_tag_display = QLabel("N/A")
        self.jurisdictional_delivery_tag_display.setStyleSheet("font-style: italic; color: #555;")
        charter_details_layout.addWidget(self.jurisdictional_delivery_tag_label)
        charter_details_layout.addWidget(self.jurisdictional_delivery_tag_display)
        charter_details_group.setLayout(charter_details_layout)
        main_layout.addWidget(charter_details_group)

        clauses_group = QGroupBox("Clauses")
        clauses_layout = QVBoxLayout()
        self.clauses_list_widget = QListWidget()
        self.clauses_list_widget.itemSelectionChanged.connect(self.display_selected_clause_details)
        clauses_layout.addWidget(self.clauses_list_widget)
        self.selected_clause_details_group = QGroupBox("Selected Clause Details")
        selected_clause_layout = QGridLayout()
        # ... (All sel_clause_* labels and values including Display No., Level, Section Title, Dates, Version)
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
        self.sel_clause_origin_label = QLabel("Origin:")
        self.sel_clause_origin_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_origin_label, 3, 0)
        selected_clause_layout.addWidget(self.sel_clause_origin_value, 3, 1)
        self.sel_clause_text_label = QLabel("Text:")
        self.sel_clause_text_value = QTextEdit()
        self.sel_clause_text_value.setReadOnly(True)
        selected_clause_layout.addWidget(self.sel_clause_text_label, 4, 0)
        selected_clause_layout.addWidget(self.sel_clause_text_value, 5, 0, 1, 2)
        self.sel_clause_purpose_label = QLabel("Purpose/Type:")
        self.sel_clause_purpose_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_purpose_label, 6, 0)
        selected_clause_layout.addWidget(self.sel_clause_purpose_value, 6, 1)
        self.sel_clause_level_label = QLabel("Level:")
        self.sel_clause_level_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_level_label, 7,0)
        selected_clause_layout.addWidget(self.sel_clause_level_value, 7,1)
        self.sel_clause_section_title_label = QLabel("Section Title:")
        self.sel_clause_section_title_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_section_title_label, 8,0)
        selected_clause_layout.addWidget(self.sel_clause_section_title_value, 8,1)
        self.sel_clause_created_label = QLabel("Created:")
        self.sel_clause_created_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_created_label, 9, 0)
        selected_clause_layout.addWidget(self.sel_clause_created_value, 9, 1)
        self.sel_clause_modified_label = QLabel("Modified:")
        self.sel_clause_modified_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_modified_label, 10, 0)
        selected_clause_layout.addWidget(self.sel_clause_modified_value, 10, 1)
        self.sel_clause_version_label = QLabel("Version:")
        self.sel_clause_version_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_version_label, 11, 0)
        selected_clause_layout.addWidget(self.sel_clause_version_value, 11, 1)
        self.sel_clause_lock_status_label = QLabel("Status:") # For Lock status
        self.sel_clause_lock_status_value = QLabel("")
        selected_clause_layout.addWidget(self.sel_clause_lock_status_label, 12, 0)
        selected_clause_layout.addWidget(self.sel_clause_lock_status_value, 12, 1)

        buttons_sel_clause_layout = QHBoxLayout()
        self.edit_selected_clause_button = QPushButton("Edit Selected Clause")
        self.edit_selected_clause_button.setEnabled(False)
        self.edit_selected_clause_button.clicked.connect(self.edit_selected_clause)
        self.view_audit_button = QPushButton("View Audit Trail") # Placeholder
        self.view_audit_button.setEnabled(False)
        self.view_audit_button.setToolTip("Functionality to be implemented in a future phase.")
        self.generate_qr_button = QPushButton("Generate QR Code")
        self.generate_qr_button.setEnabled(False)
        self.generate_qr_button.clicked.connect(self._generate_clause_qr_code)
        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button)
        buttons_sel_clause_layout.addWidget(self.view_audit_button)
        buttons_sel_clause_layout.addWidget(self.generate_qr_button)
        selected_clause_layout.addLayout(buttons_sel_clause_layout, 13, 0, 1, 2) # Adjusted row
        self.selected_clause_details_group.setLayout(selected_clause_layout)
        self.selected_clause_details_group.setVisible(False)
        clauses_layout.addWidget(self.selected_clause_details_group)

        clause_action_buttons_layout = QHBoxLayout()
        # ... (Add, Remove, Move Up, Move Down buttons)
        self.add_clause_button = QPushButton("Add New Clause")
        self.add_clause_button.clicked.connect(self.add_clause)
        self.remove_clause_button = QPushButton("Remove Selected Clause")
        self.remove_clause_button.setEnabled(False)
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

        app_action_buttons_layout = QHBoxLayout() # For Undo/Redo
        self.undo_action_button = QPushButton("Undo Action")
        self.undo_action_button.setToolTip("Undo last significant application action (Not Implemented Yet)")
        self.undo_action_button.setEnabled(False)
        self.undo_action_button.clicked.connect(lambda: QMessageBox.information(self, "Undo", "Application-level Undo not yet implemented."))
        self.redo_action_button = QPushButton("Redo Action")
        self.redo_action_button.setToolTip("Redo last undone application action (Not Implemented Yet)")
        self.redo_action_button.setEnabled(False)
        self.redo_action_button.clicked.connect(lambda: QMessageBox.information(self, "Redo", "Application-level Redo not yet implemented."))
        app_action_buttons_layout.addStretch()
        app_action_buttons_layout.addWidget(self.undo_action_button)
        app_action_buttons_layout.addWidget(self.redo_action_button)
        clauses_layout.addLayout(app_action_buttons_layout)

        clauses_group.setLayout(clauses_layout)
        main_layout.addWidget(clauses_group)

        file_ops_layout = QHBoxLayout()
        # ... (File ops buttons)
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

    def _update_family_trust_ref(self, text: str):
        self.document.family_trust_ref = text.strip() or None
        self._mark_as_modified()

    def _browse_linked_document(self, link_type: str): # Was doc_type_name, changed to link_type for consistency
        if link_type == "FamilyTrust":
            doc_dir_name = "trusts"
            file_filter = "Michaud Postal Equity App Trust Files (*.mpea_trust);;All Files (*)"
            target_input_widget = self.family_trust_ref_input
            model_attribute_name = "family_trust_ref"
            dialog_title = "Select Linked Family Trust Document"
        else:
            QMessageBox.warning(self, "Error", f"Unknown link type for Charter: {link_type}")
            return

        start_dir = os.path.join(CODEX_VAULT_DIR, doc_dir_name)
        os.makedirs(start_dir, exist_ok=True)

        filePath, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, file_filter)

        if filePath:
            try:
                relative_path = os.path.relpath(filePath, CODEX_VAULT_DIR)
                display_path = relative_path
            except ValueError:
                display_path = filePath

            if os.path.isabs(display_path) and filePath.startswith(os.path.abspath(CODEX_VAULT_DIR)):
                 display_path = os.path.relpath(filePath, CODEX_VAULT_DIR)

            target_input_widget.setText(display_path)
            setattr(self.document, model_attribute_name, display_path)
            self._mark_as_modified()
            QMessageBox.information(self, "Link Set", f"{link_type} linked to: {display_path}")

    def _clear_linked_document(self, link_type: str): # New method
        if link_type == "FamilyTrust":
            self.family_trust_ref_input.clear()
            self.document.family_trust_ref = None
        else:
            return
        self._mark_as_modified()
        QMessageBox.information(self, "Link Cleared", f"{link_type} link cleared.")

    # ... (all other methods: _update_document_jurisdiction, _collect_data_from_ui,
    #      _generate_and_set_delivery_tag, _update_jurisdictional_delivery_tag,
    #      _refresh_clause_list_display, load_document_data_into_ui, new_document, add_clause,
    #      display_selected_clause_details, edit_selected_clause, remove_selected_clause,
    #      save_document, save_document_as, load_document, move_clause_up, move_clause_down,
    #      _generate_clause_qr_code, _validate_document_basic, run_basic_conformance_check)
    # Ensure display_selected_clause_details populates sel_clause_lock_status_value
    # and edit_selected_clause_button.setEnabled(not clause_obj.is_locked)

    def _update_document_jurisdiction(self, text: str):
        self.document.jurisdiction = text
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
        self._mark_as_modified()

    def _collect_data_from_ui(self):
        self.document.name = self.name_input.text()
        self.document.upu_recognized_format_details = self.upu_format_input.toPlainText()
        self.document.global_upu_tracking_number_fields = self.global_tracking_input.toPlainText()
        self.document.canada_post_format_compliance_details = self.canada_post_input.toPlainText()
        self.document.usps_format_compliance_details = self.usps_input.toPlainText()
        self.document.vienna_convention_reference_details = self.vienna_ref_input.toPlainText()
        self.document.postal_treaty_law_reference_details = self.postal_treaty_input.toPlainText()
        self.document.family_trust_ref = self.family_trust_ref_input.text().strip() or None # Updated
        self.document.upu_tracking_number = self.upu_tracking_number_input.text().strip()
        if self.document.upu_tracking_number:
            self._generate_and_set_delivery_tag()
        else:
            self.document.jurisdictional_delivery_tag = None

    def _generate_and_set_delivery_tag(self):
        if self.document.upu_tracking_number:
            year = datetime.datetime.now().year
            sequence = self.document.upu_tracking_number[-4:] if len(self.document.upu_tracking_number) >= 4 else "001"
            prefix = "LEXPOST-CA-MB-UPU"
            self.document.jurisdictional_delivery_tag = f"{prefix}-{year}-{sequence}"
        else:
            self.document.jurisdictional_delivery_tag = None
        self.jurisdictional_delivery_tag_display.setText(self.document.jurisdictional_delivery_tag or "N/A")
        self._mark_as_modified()

    def _update_jurisdictional_delivery_tag(self, text=None):
        self.document.upu_tracking_number = self.upu_tracking_number_input.text().strip()
        self._generate_and_set_delivery_tag()

    def _refresh_clause_list_display(self):
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
            if clause_obj.section_title:
                item_text = f"{display_number}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, clause_obj.id)
            if clause_obj.is_locked: # Visual cue for locked
                # from PyQt6.QtGui import QColor # Import if not at top
                # item.setForeground(QColor("gray")) # Or a muted red
                pass # Rely on icon from __str__
            self.clauses_list_widget.addItem(item)
            if clause_obj.id == current_selected_id:
                new_selected_row = i
        if new_selected_row != -1:
            self.clauses_list_widget.setCurrentRow(new_selected_row)
        else:
            self.display_selected_clause_details()

    def load_document_data_into_ui(self):
        self.name_input.setText(self.document.name)
        self.id_display.setText(self.document.id)
        self.jurisdiction_input.setText(self.document.jurisdiction)
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {self.document.jurisdiction}")
        self.upu_format_input.setPlainText(self.document.upu_recognized_format_details)
        self.global_tracking_input.setPlainText(self.document.global_upu_tracking_number_fields)
        self.canada_post_input.setPlainText(self.document.canada_post_format_compliance_details)
        self.usps_input.setPlainText(self.document.usps_format_compliance_details)
        self.vienna_ref_input.setPlainText(self.document.vienna_convention_reference_details)
        self.postal_treaty_input.setPlainText(self.document.postal_treaty_law_reference_details)
        self.family_trust_ref_input.setText(self.document.family_trust_ref or "") # Updated
        self.upu_tracking_number_input.setText(self.document.upu_tracking_number or "")
        self.jurisdictional_delivery_tag_display.setText(self.document.jurisdictional_delivery_tag or "N/A")
        self._refresh_clause_list_display()
        self.is_modified = False
        main_window_instance = self.window()
        if hasattr(main_window_instance, 'settings_view') and \
           hasattr(main_window_instance.settings_view, 'get_setting') and \
           main_window_instance.settings_view.get_setting("enforce_clauseconformer_all_docs"):
            self.run_basic_conformance_check(is_auto_check=True)

    def new_document(self):
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e:
                print(f"Error untracking charter {self.document.id} in new_document: {e}")
        self.document = MichaudFamilyPostalCharter(name="Untitled Michaud Family Postal Charter")
        self.current_document_path = None
        self.is_modified = False
        self.load_document_data_into_ui()
        QMessageBox.information(self, "New Document", "New Postal Charter document initialized.")

    def add_clause(self):
        dialog = EditClauseDialog(default_jurisdiction=self.document.jurisdiction, parent=self)
        if dialog.exec():
            new_clause = dialog.get_clause()
            self.document.clauses.append(new_clause)
            self._refresh_clause_list_display()
            if self.clauses_list_widget.count() > 0:
                self.clauses_list_widget.setCurrentRow(self.clauses_list_widget.count() - 1)
            QMessageBox.information(self, "Clause Added", f"Clause '{new_clause.id}' successfully added.")
            self._mark_as_modified()

    def display_selected_clause_details(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]
            clause_id = list_item.data(Qt.ItemDataRole.UserRole)
            clause_obj = next((c for c in self.document.clauses if c.id == clause_id), None)
            current_row = self.clauses_list_widget.row(list_item)
            if clause_obj:
                display_numbers = generate_display_clause_numbers(self.document.clauses)
                self.sel_clause_display_number_value.setText(display_numbers[current_row] if current_row < len(display_numbers) else "N/A")
                self.sel_clause_id_value.setText(clause_obj.id)
                self.sel_clause_jurisdiction_value.setText(clause_obj.jurisdiction)
                self.sel_clause_origin_value.setText(clause_obj.origin)
                self.sel_clause_text_value.setPlainText(clause_obj.text)
                self.sel_clause_purpose_value.setText(clause_obj.metadata.get("purpose_type", "N/A"))
                self.sel_clause_level_value.setText(str(clause_obj.level))
                self.sel_clause_section_title_value.setText(clause_obj.section_title or "N/A")
                try: created_date = datetime.datetime.fromisoformat(clause_obj.creation_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: created_date = clause_obj.creation_date
                self.sel_clause_created_value.setText(created_date)
                try: modified_date = datetime.datetime.fromisoformat(clause_obj.last_modified_date).strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: modified_date = clause_obj.last_modified_date
                self.sel_clause_modified_value.setText(modified_date)
                self.sel_clause_version_value.setText(str(clause_obj.version))
                self.sel_clause_lock_status_value.setText("🔒 Locked" if clause_obj.is_locked else "✏️ Editable")
                self.selected_clause_details_group.setVisible(True)
                self.edit_selected_clause_button.setEnabled(True) # Dialog will handle if locked
                self.remove_clause_button.setEnabled(True)
                self.move_clause_up_button.setEnabled(current_row > 0)
                self.move_clause_down_button.setEnabled(current_row < self.clauses_list_widget.count() - 1)
                main_window_instance = self.window()
                qr_setting_enabled = False
                if hasattr(main_window_instance, 'settings_view') and \
                   hasattr(main_window_instance.settings_view, 'get_setting'):
                    qr_setting_enabled = main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled")
                self.generate_qr_button.setEnabled(qr_setting_enabled)
                self.generate_qr_button.setToolTip("Generates a QR code for the selected clause." if qr_setting_enabled else "Enable 'QR Proof Chain Embeds' in Settings.")
            else:
                self.selected_clause_details_group.setVisible(False)
                for btn in [self.edit_selected_clause_button, self.remove_clause_button, self.move_clause_up_button, self.move_clause_down_button, self.generate_qr_button]:
                    btn.setEnabled(False)
        else:
            self.selected_clause_details_group.setVisible(False)
            for btn in [self.edit_selected_clause_button, self.remove_clause_button, self.move_clause_up_button, self.move_clause_down_button, self.generate_qr_button]:
                btn.setEnabled(False)

    def edit_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Edit Clause", "No clause selected to edit."); return
        list_item = selected_items[0]
        clause_id = list_item.data(Qt.ItemDataRole.UserRole)
        clause_to_edit = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_to_edit:
            dialog = EditClauseDialog(clause=clause_to_edit, parent=self)
            if dialog.exec():
                self._refresh_clause_list_display()
                for i in range(self.clauses_list_widget.count()):
                    if self.clauses_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == clause_id:
                        self.clauses_list_widget.setCurrentRow(i)
                        break
                QMessageBox.information(self, "Clause Updated", f"Clause '{clause_to_edit.id}' successfully updated.")
                self._mark_as_modified()
        else: QMessageBox.critical(self, "Error", f"Could not find clause with ID {clause_id} to edit.")

    def remove_selected_clause(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Remove Clause", "No clause selected to remove."); return
        list_item = selected_items[0]
        clause_id = list_item.data(Qt.ItemDataRole.UserRole)
        clause_to_remove = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_to_remove:
            reply = QMessageBox.question(self, "Remove Clause",
                                         f"Are you sure you want to remove: {str(clause_to_remove)}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.document.clauses.remove(clause_to_remove)
                self._refresh_clause_list_display()
                QMessageBox.information(self, "Clause Removed", f"Clause {clause_to_remove.id} removed.")
                self._mark_as_modified()
        else: QMessageBox.critical(self, "Error", f"Could not find clause with ID {clause_id} to remove.")

    def save_document(self, silent=False):
        self._collect_data_from_ui()
        if not self._validate_document_basic():
            if not silent: QMessageBox.warning(self, "Validation Failed", "Cannot save document due to validation errors.")
            return False
        if not self.current_document_path:
            return self.save_document_as(silent=silent)
        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)
            if not silent:
                QMessageBox.information(self, "Save Successful", f"Postal Charter document saved to\n{self.current_document_path}")
            else:
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Auto-saved: {os.path.basename(self.current_document_path)}", 3000)
            self.is_modified = False
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.track_document_change(self.document.id, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking charter change for {self.document.id}: {e}")
            return True
        except Exception as e:
            if not silent: QMessageBox.critical(self, "Save Error", f"Could not save document: {e}")
            else: print(f"Auto-save error for {self.current_document_path}: {e}")
            return False

    def save_document_as(self, silent=False):
        self._collect_data_from_ui()
        if not self._validate_document_basic():
            if not silent: QMessageBox.warning(self, "Validation Failed", "Cannot save document due to validation errors.")
            return False
        charter_dir = os.path.join(CODEX_VAULT_DIR, "charters")
        safe_default_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
        safe_default_filename = safe_default_filename.replace(' ', '_') + ".mpea_charter"
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Save Postal Charter As...",
            os.path.join(charter_dir, safe_default_filename),
            "Michaud Postal Equity App Charter Files (*.mpea_charter);;All Files (*)")
        if not filePath: return False
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                old_doc_id = self.document.id
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(old_doc_id)
            except Exception as e:
                print(f"Error untracking old charter {old_doc_id} during Save As: {e}")
        self.current_document_path = filePath
        self.document.id = str(uuid.uuid4())
        self.id_display.setText(self.document.id)
        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)
            if not silent:
                QMessageBox.information(self, "Save As Successful", f"Postal Charter document saved to\n{self.current_document_path}")
            else:
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Auto-saved (as new): {os.path.basename(self.current_document_path)}", 3000)
            self.is_modified = False
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking charter after Save As for {self.document.id}: {e}")
            return True
        except Exception as e:
            if not silent: QMessageBox.critical(self, "Save As Error", f"Could not save document: {e}")
            else: print(f"Auto-save (as new) error for {self.current_document_path}: {e}")
            return False

    def load_document(self):
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e:
                print(f"Error untracking charter {self.document.id} before load: {e}")
        charter_dir = os.path.join(CODEX_VAULT_DIR, "charters")
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Load Postal Charter Document", charter_dir,
            "Michaud Postal Equity App Charter Files (*.mpea_charter);;All Files (*)")
        if not filePath: return
        try:
            with open(filePath, 'r') as f: doc_data = json.load(f)
            self.document = MichaudFamilyPostalCharter.from_dict(doc_data)
            self.current_document_path = filePath
            self.is_modified = False
            self.load_document_data_into_ui()
            QMessageBox.information(self, "Load Successful", f"Postal Charter document loaded from\n{filePath}")
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking charter open for {self.document.id}: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load document: {e}")

    def move_clause_up(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row > 0:
            clause_to_move = self.document.clauses.pop(current_row)
            self.document.clauses.insert(current_row - 1, clause_to_move)
            self._refresh_clause_list_display()
            self.clauses_list_widget.setCurrentRow(current_row - 1)
            self._mark_as_modified()

    def move_clause_down(self):
        current_row = self.clauses_list_widget.currentRow()
        if 0 <= current_row < self.clauses_list_widget.count() - 1:
            clause_to_move = self.document.clauses.pop(current_row)
            self.document.clauses.insert(current_row + 1, clause_to_move)
            self._refresh_clause_list_display()
            self.clauses_list_widget.setCurrentRow(current_row + 1)
            self._mark_as_modified()

    def _generate_clause_qr_code(self):
        selected_items = self.clauses_list_widget.selectedItems()
        if not selected_items: QMessageBox.warning(self, "QR Generation Error", "No clause selected."); return
        list_item = selected_items[0]
        clause_id = list_item.data(Qt.ItemDataRole.UserRole)
        clause_obj = next((c for c in self.document.clauses if c.id == clause_id), None)
        if clause_obj:
            main_window_instance = self.window()
            if hasattr(main_window_instance, 'settings_view') and \
               main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled"):
                veritas = VeritasProof(app_context=main_window_instance)

                current_user_id = getattr(main_window_instance, 'current_user_id', None)
                current_doc_id = self.document.id if self.document else None

                pixmap = veritas.generate_clause_proof_qr(clause_obj, current_user_id, current_doc_id)
                if pixmap:
                    dialog = QRDisplayDialog(pixmap, title=f"Proof QR - Clause {clause_obj.id}", parent=self)
                    dialog.exec()
                else: QMessageBox.warning(self, "QR Generation Failed", "Could not generate QR code.")
            else: QMessageBox.information(self, "QR Generation Disabled", "Enable 'QR Proof Chain Embeds' in Settings.")
        else: QMessageBox.critical(self, "Error", f"Could not find clause with ID {clause_id} for QR generation.")

    def _validate_document_basic(self) -> bool:
        self._collect_data_from_ui()
        errors = []
        if not self.document.name.strip(): errors.append("Charter Name cannot be empty.")
        if not self.document.upu_recognized_format_details.strip(): errors.append("UPU Recognized Format Details cannot be empty.")
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return False
        return True

    def run_basic_conformance_check(self, is_auto_check=False):
        self._collect_data_from_ui()
        main_window_instance = self.window()
        conformer = ClauseConformer(app_context=main_window_instance)
        self.last_conformance_issues = conformer.check_document_for_basic_issues(self.document) # Store

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

            self.create_github_issue_button.setVisible(True) # Show button

            if is_auto_check:
                if hasattr(main_window_instance, 'status_bar'):
                    main_window_instance.status_bar.showMessage(f"Conformance: {summary}", 10000)
                print(f"Auto Conformance Check (Charter):\n{summary}\nDetails:\n" + "\n".join(detailed_report_items))
            else:
                QMessageBox.warning(self, "Conformance Issues Found", summary + "\n\nDetails:\n" + "\n".join(detailed_report_items))
        else:
            self.last_conformance_issues = None
            self.create_github_issue_button.setVisible(False) # Hide button
            if not is_auto_check:
                QMessageBox.information(self, "Conformance Check", "No basic conformance issues found.")
            else:
                if hasattr(main_window_instance, 'status_bar'):
                    main_window_instance.status_bar.showMessage("Conformance: No basic issues found.", 5000)
                print("Auto Conformance Check (Charter): No basic issues found.")

    def _create_github_issue_for_conformance(self): # Copied from TrustView, should be identical
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
        project_root_for_path = None # For finally block
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

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    charter_view = CharterView()
    charter_view.setWindowTitle("Test Michaud Family Postal Charter View")
    charter_view.setGeometry(100,100, 800, 700)
    charter_view.show()
    sys.exit(app.exec())
