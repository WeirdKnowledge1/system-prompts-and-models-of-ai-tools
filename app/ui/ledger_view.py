from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                             QPushButton, QAbstractItemView, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt

# Assuming document models and ledger models will be imported when needed
# from app.core.document_models import BaseDocument
# from app.core.ledger_models import DocumentLedger, LedgerEntry
# from .dialogs.add_ledger_entry_dialog import AddLedgerEntryDialog # To be created

class LedgerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentLedgerView")

        self.current_document = None # Will hold the active BaseDocument object

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5) # Reduced margins for tighter fit

        self.title_label = QLabel("Document Ledger: [No Document Selected]")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(self.title_label)

        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(5) # Timestamp, Title, Type, Jurisdiction, Notes Summary
        self.ledger_table.setHorizontalHeaderLabels(["Timestamp", "Title", "Type", "Jurisdiction", "Notes (Summary)"])
        self.ledger_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only table
        self.ledger_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ledger_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ledger_table.verticalHeader().setVisible(False)
        self.ledger_table.horizontalHeader().setStretchLastSection(True)
        self.ledger_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Timestamp
        self.ledger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Title
        self.ledger_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Type
        self.ledger_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Jurisdiction
        # Notes will stretch

        main_layout.addWidget(self.ledger_table)

        self.add_entry_button = QPushButton("Add Ledger Entry...")
        self.add_entry_button.clicked.connect(self._add_ledger_entry)
        self.add_entry_button.setEnabled(False) # Disabled until a document is set
        main_layout.addWidget(self.add_entry_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.setLayout(main_layout)

    def set_document(self, document_obj): # Type hint with BaseDocument later
        self.current_document = document_obj
        if self.current_document:
            self.title_label.setText(f"Ledger For: {self.current_document.name} ({self.current_document.doc_type})")
            # Ensure ledger exists
            ledger = self.current_document.get_or_create_ledger() # Ensure ledger object exists
            self.add_entry_button.setEnabled(True)
            self._populate_ledger_table(ledger)
        else:
            self.title_label.setText("Document Ledger: [No Document Selected]")
            self.ledger_table.setRowCount(0) # Clear table
            self.add_entry_button.setEnabled(False)

    def _populate_ledger_table(self, ledger): # Type hint with DocumentLedger later
        if not ledger:
            self.ledger_table.setRowCount(0)
            return

        self.ledger_table.setRowCount(0) # Clear before populating
        self.ledger_table.setSortingEnabled(False) # Disable sorting during population

        for row, entry in enumerate(ledger.entries): # Assuming entries are sorted by timestamp desc
            self.ledger_table.insertRow(row)

            ts_item = QTableWidgetItem(entry.timestamp[:19]) # Show YYYY-MM-DD HH:MM:SS
            title_item = QTableWidgetItem(entry.title)
            type_item = QTableWidgetItem(entry.entry_type)
            juris_item = QTableWidgetItem(entry.jurisdiction_tag)
            notes_summary = entry.notes[:75] + "..." if len(entry.notes) > 75 else entry.notes
            notes_item = QTableWidgetItem(notes_summary)

            # Store full entry object or ID for later retrieval if needed (e.g., on double click)
            # For now, items are display only.
            # title_item.setData(Qt.ItemDataRole.UserRole, entry.entry_id)

            self.ledger_table.setItem(row, 0, ts_item)
            self.ledger_table.setItem(row, 1, title_item)
            self.ledger_table.setItem(row, 2, type_item)
            self.ledger_table.setItem(row, 3, juris_item)
            self.ledger_table.setItem(row, 4, notes_item)

        self.ledger_table.setSortingEnabled(True)
        if self.ledger_table.rowCount() > 0:
             self.ledger_table.sortByColumn(0, Qt.SortOrder.DescendingOrder) # Sort by timestamp initially


    def _add_ledger_entry(self):
        if not self.current_document:
            QMessageBox.warning(self, "No Document", "No document is currently active to add a ledger entry to.")
            return

        # Import here to avoid circular dependency issues if AddLedgerEntryDialog also imports LedgerView or models
        from .dialogs.add_ledger_entry_dialog import AddLedgerEntryDialog

        dialog = AddLedgerEntryDialog(default_jurisdiction=self.current_document.jurisdiction, parent=self)
        if dialog.exec():
            entry_data = dialog.get_entry_data()
            if entry_data:
                ledger = self.current_document.get_or_create_ledger()
                # The LedgerEntry will auto-generate ID and timestamp if not provided
                ledger.add_entry(**entry_data)
                self._populate_ledger_table(ledger) # Refresh table

                # Mark the main document as modified since its ledger changed
                # This requires document views to have an is_modified flag and _mark_as_modified method
                # This interaction needs careful thought - LedgerView modifying another view's state.
                # For now, assume the main document view handles its own 'modified' status when its 'document' object changes.
                # A signal/slot mechanism would be cleaner.
                active_doc_view = self.parent().parent()._get_active_document_view() # Example of trying to get main_window then active_view
                if active_doc_view and hasattr(active_doc_view, '_mark_as_modified'):
                    active_doc_view._mark_as_modified()

                QMessageBox.information(self, "Entry Added", "Ledger entry successfully added.")

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from app.core.document_models import MichaudFamilyTrust # For testing

    app = QApplication(sys.argv)

    # Create a dummy main window to host the ledger view for testing
    # In real app, MainWindow would manage this.
    test_main_win = QMainWindow()
    ledger_widget = LedgerView(test_main_win)

    # Create a dummy document and set it
    dummy_doc = MichaudFamilyTrust(name="Test Trust for Ledger")
    dummy_doc.get_or_create_ledger().add_entry(title="Test Entry 1", entry_type="Test", jurisdiction_tag="Lex Test")
    import time; time.sleep(0.01) # ensure different timestamp
    dummy_doc.get_or_create_ledger().add_entry(title="Test Entry 2 - A bit longer notes", entry_type="Test", jurisdiction_tag="Lex Test", notes="These are some more detailed notes for the second entry to see how it displays.")


    ledger_widget.set_document(dummy_doc)

    test_main_win.setCentralWidget(ledger_widget)
    test_main_win.setGeometry(200, 200, 800, 500)
    test_main_win.setWindowTitle("Ledger View Test")
    test_main_win.show()

    sys.exit(app.exec())
