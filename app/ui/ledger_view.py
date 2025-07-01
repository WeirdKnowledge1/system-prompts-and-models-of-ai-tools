from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                             QPushButton, QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout,
                             QFileDialog) # Added QFileDialog
from PyQt6.QtCore import Qt
import csv # For CSV export
import os # For path operations (already imported but good to note)

# from app.core.document_models import BaseDocument
# from app.core.ledger_models import DocumentLedger, LedgerEntry # For type hinting later
# from .dialogs.add_ledger_entry_dialog import AddLedgerEntryDialog

class LedgerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentLedgerView")
        self.current_document = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5)

        self.title_label = QLabel("Document Ledger: [No Document Selected]")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(self.title_label)

        # --- Filter and Search Row ---
        filter_search_layout = QHBoxLayout()
        filter_search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Title, Notes, Tags...")
        self.search_input.textChanged.connect(self._apply_filters_and_search)
        filter_search_layout.addWidget(self.search_input, 1) # Stretch search input

        filter_search_layout.addWidget(QLabel("Type:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("All Types")
        # Types will be populated from AddLedgerEntryDialog.entry_types or dynamically
        # For now, use a common list.
        common_entry_types = ["Transaction", "Notice Sent", "Notice Received", "Filing",
                              "Clause Reference", "Amendment", "Trustee Action", "System Event", "User Note", "Other"]
        self.type_filter_combo.addItems(common_entry_types)
        self.type_filter_combo.currentIndexChanged.connect(self._apply_filters_and_search)
        filter_search_layout.addWidget(self.type_filter_combo)

        filter_search_layout.addWidget(QLabel("Jurisdiction:"))
        self.jurisdiction_filter_combo = QComboBox()
        self.jurisdiction_filter_combo.addItem("All Jurisdictions")
        common_jurisdictions = ["Lex Aequies", "Lex Postalis", "Lex Naturalis", "Civil", "Ecclesiastical", "N/A", "Unknown"]
        self.jurisdiction_filter_combo.addItems(common_jurisdictions)
        self.jurisdiction_filter_combo.currentIndexChanged.connect(self._apply_filters_and_search)
        filter_search_layout.addWidget(self.jurisdiction_filter_combo)

        main_layout.addLayout(filter_search_layout)

        # --- Ledger Table ---
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(6) # Timestamp, Title, Type, Jurisdiction, Tags, Notes
        self.ledger_table.setHorizontalHeaderLabels(["Timestamp", "Title", "Type", "Jurisdiction", "Category Tags", "Notes (Summary)"])
        self.ledger_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ledger_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ledger_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ledger_table.verticalHeader().setVisible(False)
        self.ledger_table.horizontalHeader().setStretchLastSection(True)
        self.ledger_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ledger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.ledger_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.ledger_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.ledger_table.itemSelectionChanged.connect(self._update_button_states) # Connect selection change
        main_layout.addWidget(self.ledger_table)

        buttons_layout = QHBoxLayout()
        self.add_entry_button = QPushButton("Add Ledger Entry...")
        self.add_entry_button.clicked.connect(self._add_ledger_entry)

        self.edit_entry_button = QPushButton("Edit Selected Entry")
        self.edit_entry_button.clicked.connect(self._edit_selected_ledger_entry)

        self.remove_entry_button = QPushButton("Remove Selected Entry")
        self.remove_entry_button.clicked.connect(self._remove_selected_ledger_entry)

        buttons_layout.addWidget(self.add_entry_button)
        buttons_layout.addWidget(self.edit_entry_button)
        buttons_layout.addWidget(self.remove_entry_button)
        buttons_layout.addStretch()

        self.export_ledger_button = QPushButton("Export Ledger...")
        self.export_ledger_button.clicked.connect(self._export_ledger)
        buttons_layout.addWidget(self.export_ledger_button) # Add to existing button layout

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self._update_button_states() # Set initial button states

    def _update_button_states(self):
        has_document = self.current_document is not None
        has_selection = self.ledger_table.currentRow() != -1 # Check if a row is selected

        self.add_entry_button.setEnabled(has_document)
        self.edit_entry_button.setEnabled(has_document and has_selection)
        self.remove_entry_button.setEnabled(has_document and has_selection)

    def set_document(self, document_obj):
        self.current_document = document_obj
        if self.current_document:
            self.title_label.setText(f"Ledger For: {self.current_document.name} ({self.current_document.doc_type})")
            ledger = self.current_document.get_or_create_ledger()
            self._populate_ledger_table(ledger)
        else:
            self.title_label.setText("Document Ledger: [No Document Selected]")
            self.ledger_table.setRowCount(0)
        self._update_button_states() # Update button states based on new document status

    def _populate_ledger_table(self, ledger): # ledger is DocumentLedger object
        if not ledger:
            self.ledger_table.setRowCount(0)
            self._update_button_states()
            return

        self.ledger_table.setRowCount(0)
        self.ledger_table.setSortingEnabled(False) # Disable sorting during population for performance

        search_term = self.search_input.text().lower()
        selected_type = self.type_filter_combo.currentText()
        selected_jurisdiction = self.jurisdiction_filter_combo.currentText()

        row_idx_in_table = 0 # Separate counter for rows added to table after filtering
        for entry in ledger.entries: # Iterate through all original entries
            # Apply filters
            if selected_type != "All Types" and entry.entry_type != selected_type:
                continue
            if selected_jurisdiction != "All Jurisdictions" and entry.jurisdiction_tag != selected_jurisdiction:
                continue

            # Apply search term (searches title, notes, and tags)
            if search_term:
                matches_search = (
                    search_term in entry.title.lower() or
                    search_term in entry.notes.lower() or
                    any(search_term in tag.lower() for tag in entry.category_tags)
                )
                if not matches_search:
                    continue

            # If entry passes all filters, add it to the table
            self.ledger_table.insertRow(row_idx_in_table)

            ts_item = QTableWidgetItem(entry.timestamp[:19])
            title_item = QTableWidgetItem(entry.title)
            type_item = QTableWidgetItem(entry.entry_type)
            juris_item = QTableWidgetItem(entry.jurisdiction_tag)
            tags_item = QTableWidgetItem(", ".join(entry.category_tags)) # Display tags
            notes_summary = entry.notes[:75] + "..." if len(entry.notes) > 75 else entry.notes
            notes_item = QTableWidgetItem(notes_summary)

            ts_item.setData(Qt.ItemDataRole.UserRole, entry.entry_id)

            self.ledger_table.setItem(row_idx_in_table, 0, ts_item)
            self.ledger_table.setItem(row_idx_in_table, 1, title_item)
            self.ledger_table.setItem(row_idx_in_table, 2, type_item)
            self.ledger_table.setItem(row_idx_in_table, 3, juris_item)
            self.ledger_table.setItem(row_idx_in_table, 4, tags_item) # New column
            self.ledger_table.setItem(row_idx_in_table, 5, notes_item)
            row_idx_in_table +=1

        self.ledger_table.setSortingEnabled(True)
        if self.ledger_table.rowCount() > 0:
             self.ledger_table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self._update_button_states()

    def _apply_filters_and_search(self):
        if not self.current_document or not self.current_document.ledger:
            self.ledger_table.setRowCount(0)
            return
        self._populate_ledger_table(self.current_document.ledger) # This will re-apply filters

    def _add_ledger_entry(self):
        if not self.current_document:
            QMessageBox.warning(self, "No Document", "No document is currently active to add a ledger entry to.")
            return

        from .dialogs.add_ledger_entry_dialog import AddLedgerEntryDialog # Keep local import

        dialog = AddLedgerEntryDialog(default_jurisdiction=self.current_document.jurisdiction, parent=self)
        if dialog.exec():
            entry_data = dialog.get_entry_data() # This is a dict from the dialog
            if entry_data:
                ledger = self.current_document.get_or_create_ledger()
                # LedgerEntry constructor will create ID and timestamp if not in entry_data
                from app.core.ledger_models import LedgerEntry # Import here if not at top
                new_entry = LedgerEntry(
                    title=entry_data["title"],
                    entry_type=entry_data["entry_type"],
                    jurisdiction_tag=entry_data["jurisdiction_tag"],
                    notes=entry_data["notes"],
                    associated_clause_ids=entry_data["associated_clause_ids"],
                    status=entry_data["status"]
                    # category_tags and user-set timestamp will be handled when dialog is updated
                )
                ledger.add_entry(entry=new_entry)
                self._populate_ledger_table(ledger)

                active_doc_view = self._get_main_window_active_doc_view()
                if active_doc_view and hasattr(active_doc_view, '_mark_as_modified'):
                    active_doc_view._mark_as_modified()
                QMessageBox.information(self, "Entry Added", "Ledger entry successfully added.")

    def _edit_selected_ledger_entry(self):
        current_row = self.ledger_table.currentRow()
        if current_row < 0 or not self.current_document or not self.current_document.ledger:
            QMessageBox.warning(self, "Selection Error", "No ledger entry selected or no active ledger.")
            return

        entry_id_item = self.ledger_table.item(current_row, 0)
        if not entry_id_item: return

        entry_id = entry_id_item.data(Qt.ItemDataRole.UserRole)

        entry_to_edit_model = None
        for entry_obj in self.current_document.ledger.entries:
            if entry_obj.entry_id == entry_id:
                entry_to_edit_model = entry_obj
                break

        if not entry_to_edit_model:
            QMessageBox.critical(self, "Error", f"Could not find ledger entry with ID: {entry_id} in the model.")
            return

        from .dialogs.add_ledger_entry_dialog import AddLedgerEntryDialog
        dialog = AddLedgerEntryDialog(entry_data_to_edit=entry_to_edit_model.to_dict(),
                                      default_jurisdiction=entry_to_edit_model.jurisdiction_tag,
                                      parent=self)

        if dialog.exec():
            updated_entry_data = dialog.get_entry_data() # This is a dict
            if updated_entry_data:
                # Update the existing LedgerEntry object in the model
                entry_to_edit_model.title = updated_entry_data.get("title", entry_to_edit_model.title)
                entry_to_edit_model.entry_type = updated_entry_data.get("entry_type", entry_to_edit_model.entry_type)
                entry_to_edit_model.jurisdiction_tag = updated_entry_data.get("jurisdiction_tag", entry_to_edit_model.jurisdiction_tag)
                entry_to_edit_model.notes = updated_entry_data.get("notes", entry_to_edit_model.notes)
                entry_to_edit_model.associated_clause_ids = updated_entry_data.get("associated_clause_ids", entry_to_edit_model.associated_clause_ids)
                entry_to_edit_model.status = updated_entry_data.get("status", entry_to_edit_model.status)
                # category_tags and user-settable timestamp will be handled here once dialog supports them
                # For now, ensure original timestamp and ID are preserved if not changed by dialog
                entry_to_edit_model.timestamp = updated_entry_data.get("timestamp", entry_to_edit_model.timestamp)


                self.current_document.ledger.entries.sort(key=lambda x: x.timestamp, reverse=True) # Re-sort if timestamps can change
                self._populate_ledger_table(self.current_document.ledger)

                active_doc_view = self._get_main_window_active_doc_view()
                if active_doc_view and hasattr(active_doc_view, '_mark_as_modified'):
                    active_doc_view._mark_as_modified()
                QMessageBox.information(self, "Entry Updated", f"Ledger entry '{entry_to_edit_model.title}' updated.")


    def _remove_selected_ledger_entry(self):
        current_row = self.ledger_table.currentRow()
        if current_row < 0 or not self.current_document or not self.current_document.ledger:
            QMessageBox.warning(self, "Selection Error", "No ledger entry selected or no active ledger.")
            return

        entry_id_item = self.ledger_table.item(current_row, 0)
        if not entry_id_item: return

        entry_id_to_remove = entry_id_item.data(Qt.ItemDataRole.UserRole)
        entry_title = self.ledger_table.item(current_row, 1).text()

        reply = QMessageBox.question(self, "Remove Ledger Entry",
                                     f"Are you sure you want to remove entry: '{entry_title}' (ID: {entry_id_to_remove})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            original_length = len(self.current_document.ledger.entries)
            self.current_document.ledger.entries = [
                e for e in self.current_document.ledger.entries if e.entry_id != entry_id_to_remove
            ]
            if len(self.current_document.ledger.entries) < original_length:
                self._populate_ledger_table(self.current_document.ledger)
                active_doc_view = self._get_main_window_active_doc_view()
                if active_doc_view and hasattr(active_doc_view, '_mark_as_modified'):
                    active_doc_view._mark_as_modified()
                QMessageBox.information(self, "Entry Removed", f"Ledger entry '{entry_title}' removed.")
            else:
                QMessageBox.warning(self, "Error", "Could not find or remove the specified ledger entry.")
        self._update_button_states()


    def _get_main_window_active_doc_view(self):
        try:
            main_window = self.window()
            if hasattr(main_window, '_get_active_document_view'): # Check if MainWindow has this helper
                return main_window._get_active_document_view()
        except Exception as e:
            print(f"Error accessing main window active doc view from LedgerView: {e}")
        return None


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from app.core.document_models import MichaudFamilyTrust
    from app.core.ledger_models import LedgerEntry # Import for test

    app = QApplication(sys.argv)

    test_main_win = QMainWindow()
    # Mock methods/attributes that LedgerView might expect from its main window context
    class MockActiveDocView:
        def _mark_as_modified(self): print("Mock DocumentView: Marked as modified.")

    def get_mock_active_doc_view(): return MockActiveDocView()
    test_main_win._get_active_document_view = get_mock_active_doc_view


    ledger_widget = LedgerView(test_main_win)

    dummy_doc = MichaudFamilyTrust(name="Test Trust for Ledger")
    ledger = dummy_doc.get_or_create_ledger()
    ledger.add_entry(entry=LedgerEntry(title="Test Entry 1", entry_type="Test", jurisdiction_tag="Lex Test")) # Pass as object
    import time; time.sleep(0.01)
    ledger.add_entry(entry=LedgerEntry(title="Test Entry 2 - A bit longer notes", entry_type="Test", jurisdiction_tag="Lex Test", notes="These are some more detailed notes for the second entry to see how it displays."))

    ledger_widget.set_document(dummy_doc)

    test_main_win.setCentralWidget(ledger_widget)

    def _export_ledger(self):
        if not self.current_document or not self.current_document.ledger or not self.current_document.ledger.entries:
            QMessageBox.information(self, "Export Ledger", "No ledger entries to export.")
            return

        # Suggest a filename based on the document name
        doc_name_part = "".join(c if c.isalnum() else '_' for c in self.current_document.name[:30])
        suggested_filename = f"{doc_name_part}_ledger"

        filePath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Ledger As",
            suggested_filename,
            "CSV files (*.csv);;Text files (*.txt);;All Files (*)"
        )

        if not filePath:
            return # User cancelled

        # Get currently displayed (filtered) entries from the table
        # This is more robust than re-filtering the model if UI has complex sort/filter not in model
        # However, for simplicity and consistency with the plan, we'll re-filter the model's data
        # based on current UI filter settings to get the data to export.

        ledger = self.current_document.ledger
        search_term = self.search_input.text().lower()
        selected_type = self.type_filter_combo.currentText()
        selected_jurisdiction = self.jurisdiction_filter_combo.currentText()

        entries_to_export = []
        for entry in ledger.entries:
            if selected_type != "All Types" and entry.entry_type != selected_type:
                continue
            if selected_jurisdiction != "All Jurisdictions" and entry.jurisdiction_tag != selected_jurisdiction:
                continue
            if search_term:
                matches_search = (
                    search_term in entry.title.lower() or
                    search_term in entry.notes.lower() or
                    any(search_term in tag.lower() for tag in entry.category_tags)
                )
                if not matches_search:
                    continue
            entries_to_export.append(entry)

        # Sort by timestamp (original order in ledger.entries is already sorted this way)
        # If a different sort order is applied in table, we might want to export that order.
        # For now, using the model's default sort (most recent first).

        if not entries_to_export:
            QMessageBox.information(self, "Export Ledger", "No entries match the current filter criteria to export.")
            return

        try:
            if filePath.lower().endswith(".csv"):
                headers = ["Timestamp", "Title", "Type", "Jurisdiction", "Category Tags", "Notes", "Status", "Entry ID", "Associated Clause IDs"]
                with open(filePath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    for entry in entries_to_export:
                        writer.writerow([
                            entry.timestamp,
                            entry.title,
                            entry.entry_type,
                            entry.jurisdiction_tag,
                            ", ".join(entry.category_tags),
                            entry.notes,
                            entry.status,
                            entry.entry_id,
                            ", ".join(entry.associated_clause_ids)
                        ])
                QMessageBox.information(self, "Export Successful", f"Ledger exported to CSV:\n{filePath}")

            elif filePath.lower().endswith(".txt"):
                with open(filePath, 'w', encoding='utf-8') as txtfile:
                    txtfile.write(f"Ledger Export for: {self.current_document.name}\n")
                    txtfile.write(f"Export Date: {datetime.datetime.now().isoformat()[:19]}\n")
                    txtfile.write("="*50 + "\n\n")
                    for entry in entries_to_export:
                        txtfile.write(f"Timestamp: {entry.timestamp[:19]}\n")
                        txtfile.write(f"Title: {entry.title}\n")
                        txtfile.write(f"Type: {entry.entry_type}\n")
                        txtfile.write(f"Jurisdiction: {entry.jurisdiction_tag}\n")
                        txtfile.write(f"Category Tags: {', '.join(entry.category_tags)}\n")
                        txtfile.write(f"Status: {entry.status}\n")
                        txtfile.write(f"Entry ID: {entry.entry_id}\n")
                        if entry.associated_clause_ids:
                            txtfile.write(f"Associated Clauses: {', '.join(entry.associated_clause_ids)}\n")
                        txtfile.write(f"Notes:\n{entry.notes}\n")
                        txtfile.write("-" * 30 + "\n\n")
                QMessageBox.information(self, "Export Successful", f"Ledger exported to TXT:\n{filePath}")
            else:
                QMessageBox.warning(self, "Unsupported Format", "File will be saved as TXT. Please choose .csv or .txt for formatted export.")
                # Fallback to TXT if no recognized extension or user chose "All Files" with weird ext
                # This part can be removed if we strictly enforce .csv or .txt via filter.
                # For now, let's assume if filter is "All Files" they might type "ledger.dat"
                # In that case, we could default to TXT or error.
                # Here, we'll just assume the selected_filter from QFileDialog handles it. If not, this is a fallback.
                # If selected_filter was used, it would be like:
                # if "(*.csv)" in selected_filter: ... elif "(*.txt)" in selected_filter: ...
                # For now, simple endswith is fine.
                QMessageBox.information(self, "Export Note", "File saved with the chosen extension. For specific formatting, please select .csv or .txt.")


        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export ledger: {e}")


    test_main_win.setGeometry(200, 200, 800, 500)
    test_main_win.setWindowTitle("Ledger View Test")
    test_main_win.show()

    sys.exit(app.exec())
