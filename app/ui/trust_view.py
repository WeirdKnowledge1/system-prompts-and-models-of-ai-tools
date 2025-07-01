from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QMessageBox, QListWidget, QFileDialog,
                             QHBoxLayout, QGroupBox)
from PyQt6.QtCore import Qt
import json
import os
import datetime
import uuid # Import uuid for new document IDs

from app.core.document_models import MichaudFamilyTrust
from app.core.clause_model import Clause
from app.ui.dialogs.edit_clause_dialog import EditClauseDialog
from app.ui.dialogs.qr_display_dialog import QRDisplayDialog
from app.core.agents import ClauseConformer, VeritasProof, DocumentTracker # Import DocumentTracker
from app.utils.constants import CODEX_VAULT_DIR

class TrustView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document_path = None
        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.is_modified = False # Initialize is_modified flag
        self._setup_ui()
        self._connect_modification_signals()


    def _connect_modification_signals(self):
        """Connects UI elements' change signals to set the is_modified flag."""
        # Connect textChanged for QLineEdits
        self.name_input.textChanged.connect(self._mark_as_modified)
        self.jurisdiction_input.textChanged.connect(self._mark_as_modified)
        self.settlors_input.textChanged.connect(self._mark_as_modified)
        self.trustees_input.textChanged.connect(self._mark_as_modified)
        self.beneficiaries_input.textChanged.connect(self._mark_as_modified)
        # Connect textChanged for QTextEdits
        self.land_rights_input.textChanged.connect(self._mark_as_modified)
        self.name_control_input.textChanged.connect(self._mark_as_modified)
        self.mortgage_recon_input.textChanged.connect(self._mark_as_modified)
        # For QListWidget (clauses), modification is handled by add/remove/edit methods
        # For QComboBox, use currentIndexChanged

    def _mark_as_modified(self, text=None): # text arg to match signal, not always used
        self.is_modified = True
        # Optional: update window title to indicate unsaved changes, e.g., append "*"
        # parent_window = self.window()
        # if parent_window and not parent_window.windowTitle().endswith("*"):
        #     parent_window.setWindowTitle(parent_window.windowTitle() + "*")


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Jurisdiction Header Label ---
        self.jurisdiction_header_label = QLabel("Jurisdiction: N/A")
        self.jurisdiction_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Basic styling for prominence, can be refined
        self.jurisdiction_header_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px; background-color: #E8E8E8; border-bottom: 1px solid #C0C0C0;")
        main_layout.addWidget(self.jurisdiction_header_label)

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
        # Update both document model and header label on text change
        self.jurisdiction_input.textChanged.connect(self._update_document_jurisdiction)
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

        self.generate_qr_button = QPushButton("Generate QR Code")
        self.generate_qr_button.setEnabled(False)
        self.generate_qr_button.clicked.connect(self._generate_clause_qr_code)

        buttons_sel_clause_layout.addWidget(self.edit_selected_clause_button)
        buttons_sel_clause_layout.addWidget(self.view_audit_button)
        buttons_sel_clause_layout.addWidget(self.generate_qr_button) # Add new button
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
        # If a document was loaded from a file and is being replaced by "new"
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e:
                print(f"Error untracking document {self.document.id} in new_document: {e}")

        self.document = MichaudFamilyTrust(name="Untitled Michaud Family Trust")
        self.current_document_path = None
        self.is_modified = False # New document is not modified initially
        self.load_document_data_into_ui() # This will also trigger auto-conformance if enabled
        QMessageBox.information(self, "New Document", "New Trust document initialized.")

        # Since a new (unsaved) document is created, it's not yet tracked by path.
        # Tracking by ID for unsaved documents could be an enhancement if needed.
        # For now, track_document_open is primarily for file-based documents.

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
            self._mark_as_modified()

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

                # Enable/Disable QR button based on setting
                main_window_instance = self.window()
                qr_setting_enabled = False
                if hasattr(main_window_instance, 'settings_view') and \
                   hasattr(main_window_instance.settings_view, 'get_setting'):
                    qr_setting_enabled = main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled")
                self.generate_qr_button.setEnabled(qr_setting_enabled)
                self.generate_qr_button.setToolTip("Generates a QR code for the selected clause's ID and text." if qr_setting_enabled else "Enable 'QR Proof Chain Embeds' in Settings to use this feature.")

            else:
                # Should not happen if selection is valid and lists are in sync
                self.selected_clause_details_group.setVisible(False)
                self.edit_selected_clause_button.setEnabled(False)
                self.remove_clause_button.setEnabled(False)
                self.move_clause_up_button.setEnabled(False)
                self.move_clause_down_button.setEnabled(False)
                self.generate_qr_button.setEnabled(False)
        else:
            self.selected_clause_details_group.setVisible(False)
            self.edit_selected_clause_button.setEnabled(False)
            self.remove_clause_button.setEnabled(False)
            self.move_clause_up_button.setEnabled(False)
            self.move_clause_down_button.setEnabled(False)
            self.generate_qr_button.setEnabled(False)

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
                self._mark_as_modified()
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
                self._mark_as_modified()
        else:
            QMessageBox.warning(self, "Remove Clause", "No clause selected to remove.")

    def save_document(self, silent=False): # Added silent flag for auto-save
        self._collect_data_from_ui()

        if not self._validate_document_basic():
            if not silent: # Only show validation popup for manual save
                 QMessageBox.warning(self, "Validation Failed", "Cannot save document due to validation errors.")
            return False # Indicate save failed

        if not self.current_document_path:
            # If no path, this is effectively a "Save As" situation for a new doc
            # or if user explicitly chose "Save" on a new doc.
            return self.save_document_as(silent=silent) # Pass silent flag

        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)

            if not silent:
                QMessageBox.information(self, "Save Successful", f"Trust document saved to\n{self.current_document_path}")
            else: # For auto-save, maybe a status bar message
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Auto-saved: {os.path.basename(self.current_document_path)}", 3000)

            self.is_modified = False # Clear modified flag
            # Update window title if it had "*"
            # parent_window = self.window()
            # if parent_window and parent_window.windowTitle().endswith("*"):
            #    parent_window.setWindowTitle(parent_window.windowTitle()[:-1])

            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.track_document_change(self.document.id, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking document change for {self.document.id}: {e}")
            return True # Indicate save success

        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Save Error", f"Could not save document: {e}")
            else:
                print(f"Auto-save error for {self.current_document_path}: {e}")
            # self.current_document_path = None # Don't reset path on failed save, user might want to retry
            return False # Indicate save failed

    def save_document_as(self, silent=False): # Added silent flag
        self._collect_data_from_ui()
        if not self._validate_document_basic():
            if not silent:
                QMessageBox.warning(self, "Validation Failed", "Cannot save document due to validation errors.")
            return False

        trust_dir = os.path.join(CODEX_VAULT_DIR, "trusts")
        safe_default_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in self.document.name)
        safe_default_filename = safe_default_filename.replace(' ', '_') + ".mpea_trust"

        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Trust Document As...",
            os.path.join(trust_dir, safe_default_filename),
            "Michaud Postal Equity App Trust Files (*.mpea_trust);;All Files (*)"
        )
        if not filePath:
            return False # User cancelled

        # "Save As" implies a new identity for this specific file instance if we want to avoid
        # the original DocumentTracker entry being overwritten by saves to a new file.
        # For now, we'll generate a new ID for the document object in this view context.
        # The old document (if any) remains unchanged in its original file or memory until replaced.

        # Untrack the old ID if it was being tracked from a specific path
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                old_doc_id = self.document.id
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(old_doc_id) # Untrack by old ID
            except Exception as e:
                print(f"Error untracking old document {old_doc_id} during Save As: {e}")

        self.current_document_path = filePath
        self.document.id = str(uuid.uuid4()) # Generate new ID for this "copy"
        self.id_display.setText(self.document.id) # Update UI
        # Also update document name in UI if it's part of the filename potentially
        # self.name_input.setText(os.path.basename(filePath).replace(".mpea_trust","")) # Optional

        try:
            with open(self.current_document_path, 'w') as f:
                json.dump(self.document.to_dict(), f, indent=4)

            if not silent:
                QMessageBox.information(self, "Save As Successful", f"Trust document saved to\n{self.current_document_path}")
            else:
                main_window = self.window()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Auto-saved (as new): {os.path.basename(self.current_document_path)}", 3000)

            self.is_modified = False
            # Update window title if necessary

            # Track this new document ID and path
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                # Use track_document_open as it's now a new file path being tracked with a new/potentially new ID context
                doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking document after Save As for {self.document.id}: {e}")
            return True
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Save As Error", f"Could not save document: {e}")
            else:
                print(f"Auto-save (as new) error for {self.current_document_path}: {e}")
            return False


    def load_document(self):
        # If a document is already loaded, untrack it first
        if self.current_document_path and hasattr(self.document, 'id'):
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.untrack_document(self.document.id)
            except Exception as e:
                print(f"Error untracking document {self.document.id} before load: {e}")

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
            self.is_modified = False # Loaded document is initially not modified
            self.load_document_data_into_ui() # This will also trigger auto-conformance if enabled
            QMessageBox.information(self, "Load Successful", f"Trust document loaded from\n{filePath}")

            # Track newly opened document
            try:
                doc_tracker = DocumentTracker(app_context=self.window())
                doc_tracker.track_document_open(self.document.id, self.current_document_path, self.document.to_dict())
            except Exception as e:
                print(f"Error tracking document open for {self.document.id}: {e}")

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

    def _update_document_jurisdiction(self, text: str):
        """Updates the document model's jurisdiction and the header label."""
        self.document.jurisdiction = text
        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {text}")
        # Potentially trigger re-styling or other actions if jurisdiction change has wide effects

    def _generate_clause_qr_code(self):
        current_row = self.clauses_list_widget.currentRow()
        if current_row >= 0:
            if 0 <= current_row < len(self.document.clauses):
                clause_obj = self.document.clauses[current_row]

                # Check setting again just before generation (though button state should reflect it)
                main_window_instance = self.window()
                if hasattr(main_window_instance, 'settings_view') and \
                   main_window_instance.settings_view.get_setting("qr_proof_chain_embeds_enabled"):

                    veritas = VeritasProof(app_context=main_window_instance)
                    # Combine key info for the QR code data
                    qr_data = f"ClauseID: {clause_obj.id}\nJurisdiction: {clause_obj.jurisdiction}\nOrigin: {clause_obj.origin}\nText: {clause_obj.text[:100]}..." # Truncate text for QR

                    pixmap = veritas.generate_qr_for_text(qr_data)

                    if pixmap:
                        dialog = QRDisplayDialog(pixmap, title=f"QR Code - Clause {clause_obj.id}", parent=self)
                        dialog.exec()
                    else:
                        QMessageBox.warning(self, "QR Generation Failed", "Could not generate QR code for the selected clause.")
                else:
                    QMessageBox.information(self, "QR Generation Disabled", "Please enable 'QR Proof Chain Embeds' in System Preferences to generate QR codes.")
        else:
            QMessageBox.warning(self, "QR Generation Error", "No clause selected.")


    def run_basic_conformance_check(self, is_auto_check=False):
        """Runs the basic conformance check using ClauseConformer agent."""
        self._collect_data_from_ui() # Ensure document is up-to-date

        # Access MainWindow to get settings_view. This is a bit fragile.
        # A better way would be to pass app_context or settings_view reference during init.
        main_window = self.parent().parent().parent() # Potentially: self -> QGroupBox -> QVBoxLayout -> TrustView(QWidget) -> QStackedWidget(tab content) -> QTabWidget -> MainWindow
        # This path might vary if the view is directly added to the tab widget or nested differently.
        # For now, let's assume a common structure or try to get it from QApplication instance if view is top-level.

        # A more robust way to get MainWindow if views are direct children of tab content widgets:
        # current_tab_widget = self.parentWidget()
        # if current_tab_widget:
        #    main_window = current_tab_widget.parentWidget().parentWidget() # Potentially
        # This is still brittle. Best is dependency injection or a singleton app context.

        # Simplification: Assume main_window can be accessed if it's a known ancestor.
        # If self.window() returns the MainWindow instance:
        main_window_instance = self.window()


        conformer = ClauseConformer(app_context=main_window_instance) # Pass main_window as a basic context
        issues_report = conformer.check_document_for_basic_issues(self.document)

        if issues_report:
            detailed_report = []
            warning_count = 0
            info_count = 0
            for item in issues_report:
                detailed_report.append(f"- ID: {item['id'][:15]}... ({item['severity']}): {item['issue']}")
                if item['severity'] == 'warning':
                    warning_count += 1
                else:
                    info_count += 1

            summary = f"{len(issues_report)} issue(s) found: {warning_count} warning(s), {info_count} info."

            if is_auto_check:
                if hasattr(main_window_instance, 'status_bar'):
                    main_window_instance.status_bar.showMessage(f"Conformance: {summary}", 10000) # Show for 10s
                print(f"Auto Conformance Check:\n{summary}\n" + "\n".join(detailed_report))
            else:
                QMessageBox.warning(self, "Conformance Issues Found", summary + "\n\nDetails:\n" + "\n".join(detailed_report))
        else:
            if not is_auto_check:
                QMessageBox.information(self, "Conformance Check", "No basic conformance issues found.")
            else:
                if hasattr(main_window_instance, 'status_bar'):
                     main_window_instance.status_bar.showMessage("Conformance: No basic issues found.", 5000)
                print("Auto Conformance Check: No basic issues found.")

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
        for clause_obj in self.document.clauses:
            self.clauses_list_widget.addItem(str(clause_obj))

        self.jurisdiction_header_label.setText(f"Document Jurisdiction: {self.document.jurisdiction}")
        self.display_selected_clause_details()

        # Auto-check if setting is enabled
        main_window_instance = self.window()
        if hasattr(main_window_instance, 'settings_view') and \
           main_window_instance.settings_view.get_setting("enforce_clauseconformer_all_docs"):
            self.run_basic_conformance_check(is_auto_check=True)


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
