from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QTextEdit,
                             QPushButton, QListWidget, QGroupBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer # QTimer might be used later for live updates

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MasterAIDashboardView") # For potential styling
        self._setup_ui()
        # In future, might pass main_window_instance or app_context for interactions

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding

        # Top row for key status items using QHBoxLayout
        status_layout = QHBoxLayout()

        # Current Document in Progress
        doc_status_group = QGroupBox("Current Document")
        doc_status_v_layout = QVBoxLayout()
        self.current_doc_label = QLabel("Document: Not Active")
        self.current_doc_label.setWordWrap(True)
        self.current_doc_jurisdiction_label = QLabel("Jurisdiction: N/A")
        doc_status_v_layout.addWidget(self.current_doc_label)
        doc_status_v_layout.addWidget(self.current_doc_jurisdiction_label)
        doc_status_group.setLayout(doc_status_v_layout)
        status_layout.addWidget(doc_status_group)

        # Dominion Status
        dominion_status_group = QGroupBox("Dominion Status")
        dominion_status_v_layout = QVBoxLayout()
        self.dominion_status_label = QLabel("Status: Draft Mode") # Placeholder
        dominion_status_v_layout.addWidget(self.dominion_status_label)
        dominion_status_group.setLayout(dominion_status_v_layout)
        status_layout.addWidget(dominion_status_group)

        main_layout.addLayout(status_layout)

        # Middle row for summaries and notifications
        mid_layout = QHBoxLayout()

        # Active Memory Summary
        memory_summary_group = QGroupBox("Active Memory Summary (Today)")
        memory_summary_layout = QVBoxLayout()
        self.memory_summary_text = QTextEdit("No significant memory events logged today.") # Placeholder
        self.memory_summary_text.setReadOnly(True)
        self.memory_summary_text.setFixedHeight(100) # Limit height
        memory_summary_layout.addWidget(self.memory_summary_text)
        memory_summary_group.setLayout(memory_summary_layout)
        mid_layout.addWidget(memory_summary_group, 1) # Stretch factor 1

        # Latest Ledger Entry Preview
        ledger_preview_group = QGroupBox("Latest Ledger Entry Preview")
        ledger_preview_layout = QVBoxLayout()
        self.ledger_preview_text = QLabel("No ledger entries yet.") # Placeholder
        self.ledger_preview_text.setWordWrap(True)
        self.ledger_preview_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        ledger_preview_layout.addWidget(self.ledger_preview_text)
        ledger_preview_group.setLayout(ledger_preview_layout)
        ledger_preview_group.setMinimumHeight(100)
        mid_layout.addWidget(ledger_preview_group, 1) # Stretch factor 1

        main_layout.addLayout(mid_layout)

        # Codex Notifications
        notifications_group = QGroupBox("Time-Stamped Codex Notifications")
        notifications_layout = QVBoxLayout()
        self.notifications_list = QListWidget()
        self.notifications_list.addItem("System Initialized - All agents nominal.") # Placeholder
        notifications_layout.addWidget(self.notifications_list)
        notifications_group.setLayout(notifications_layout)
        main_layout.addWidget(notifications_group, 1) # Stretch factor for vertical space

        # Action Buttons (Large, plain terms)
        actions_group = QGroupBox("Quick Actions")
        actions_grid_layout = QGridLayout() # Use grid for uniform button sizes potentially

        self.start_new_doc_button = QPushButton("Start New Document")
        self.edit_current_doc_button = QPushButton("Edit Current Document") # Changed from "Edit Current Trust"
        self.add_person_info_button = QPushButton("Add Person’s Info")
        self.review_clauses_button = QPushButton("Review Clauses")
        self.audit_document_button = QPushButton("Audit This Document")
        self.export_print_button = QPushButton("Export or Print")

        # Set object names for styling if needed
        self.start_new_doc_button.setObjectName("dashboardActionButton")
        # ... and so on for other buttons

        # Placeholder connections
        buttons = [
            self.start_new_doc_button, self.edit_current_doc_button,
            self.add_person_info_button, self.review_clauses_button,
            self.audit_document_button, self.export_print_button
        ]

        row, col = 0, 0
        for btn in buttons:
            btn.setMinimumHeight(40) # Make buttons larger
            btn.clicked.connect(self._on_action_button_clicked)
            actions_grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 1 : # Max 2 buttons per row for this example
                col = 0
                row += 1

        actions_group.setLayout(actions_grid_layout)
        main_layout.addWidget(actions_group)

        main_layout.addStretch(0) # No final stretch, let content fill

        self.setLayout(main_layout)

    def _on_action_button_clicked(self):
        sender = self.sender()
        from PyQt6.QtWidgets import QMessageBox # Local import
        QMessageBox.information(self, "Action Triggered", f"'{sender.text()}' clicked. (Not Implemented)")

    # Methods to update dashboard elements (will be called by MainWindow or other services)
    def update_current_document(self, doc_name: str | None, jurisdiction: str | None):
        if doc_name:
            self.current_doc_label.setText(f"Document: {doc_name}")
            self.current_doc_jurisdiction_label.setText(f"Jurisdiction: {jurisdiction or 'N/A'}")
        else:
            self.current_doc_label.setText("Document: Not Active")
            self.current_doc_jurisdiction_label.setText("Jurisdiction: N/A")

    def update_dominion_status(self, status: str):
        self.dominion_status_label.setText(f"Status: {status}")

    def add_notification(self, message: str):
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.notifications_list.insertItem(0, f"{timestamp} - {message}") # Add to top
        if self.notifications_list.count() > 100: # Limit list size
            self.notifications_list.takeItem(100)

    def update_ledger_preview(self, entry_summary: str | None):
        if entry_summary:
            self.ledger_preview_text.setText(entry_summary)
        else:
            self.ledger_preview_text.setText("No recent ledger activity.")

    def update_memory_summary(self, summary_text: str):
        self.memory_summary_text.setPlainText(summary_text)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dashboard = DashboardView()
    dashboard.setWindowTitle("Master AI Dashboard Test")
    dashboard.setGeometry(100, 100, 800, 600)
    dashboard.show()

    # Example updates
    dashboard.update_current_document("Michaud Family Trust - Draft 2024", "Lex Aequies")
    dashboard.update_dominion_status("Draft (Unsaved Changes)")
    dashboard.add_notification("ClauseConformer found 2 minor issues in loaded document.")
    dashboard.update_ledger_preview("01/07/2024: Added Beneficiary 'Child A'. Notes: Primary heir.")
    dashboard.update_memory_summary("Today's Edits:\n- Modified 3 clauses in Trust.\n- Added 1 Person Profile.\n- Saved Charter document.")

    sys.exit(app.exec())
