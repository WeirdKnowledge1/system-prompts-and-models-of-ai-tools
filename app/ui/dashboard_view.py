from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QTextEdit,
                             QPushButton, QListWidget, QGroupBox, QHBoxLayout, QApplication) # Added QApplication
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

        # --- Master AI Command Group ---
        master_ai_command_group = QGroupBox("Master AI Command Interface")
        master_ai_layout = QVBoxLayout()

        command_input_layout = QHBoxLayout()
        self.master_ai_command_input = QLineEdit()
        self.master_ai_command_input.setPlaceholderText("Enter command for Master AI (e.g., 'validate current document')...")
        self.submit_master_ai_command_button = QPushButton("Send Command")
        self.submit_master_ai_command_button.clicked.connect(self._send_command_to_master_ai)

        command_input_layout.addWidget(self.master_ai_command_input, 1)
        command_input_layout.addWidget(self.submit_master_ai_command_button)
        master_ai_layout.addLayout(command_input_layout)

        # Optional: A small area for direct Master AI responses or status, separate from notifications
        # self.master_ai_response_display = QTextEdit()
        # self.master_ai_response_display.setReadOnly(True)
        # self.master_ai_response_display.setPlaceholderText("Master AI responses/status...")
        # self.master_ai_response_display.setFixedHeight(80)
        # master_ai_layout.addWidget(self.master_ai_response_display)

        master_ai_command_group.setLayout(master_ai_layout)
        main_layout.addWidget(master_ai_command_group)
        # --- End Master AI Command Group ---


        # GitHub Tools Group
        github_tools_group = QGroupBox("GitHub Repository Tools")
        github_tools_layout = QVBoxLayout()

        repo_input_layout = QHBoxLayout()
        self.github_repo_label = QLabel("Repo (owner/repo):")
        self.github_repo_input = QLineEdit()
        self.github_repo_input.setPlaceholderText("e.g., octocat/Spoon-Knife")
        self.fetch_repo_info_button = QPushButton("Fetch Repo Info")
        self.fetch_repo_info_button.clicked.connect(self._fetch_github_repo_info) # Connect the button

        repo_input_layout.addWidget(self.github_repo_label)
        repo_input_layout.addWidget(self.github_repo_input, 1) # Stretch input field
        repo_input_layout.addWidget(self.fetch_repo_info_button)
        github_tools_layout.addLayout(repo_input_layout)

        self.github_repo_info_display = QTextEdit()
        self.github_repo_info_display.setReadOnly(True)
        self.github_repo_info_display.setPlaceholderText("Repository information will be displayed here...")
        self.github_repo_info_display.setFixedHeight(100) # Adjust as needed
        github_tools_layout.addWidget(self.github_repo_info_display)

        github_tools_group.setLayout(github_tools_layout)
        main_layout.addWidget(github_tools_group) # Add before notifications or actions

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

    def _send_command_to_master_ai(self):
        command_text = self.master_ai_command_input.text().strip()
        if not command_text:
            self.add_notification("Master AI Command Error: Command cannot be empty.")
            return

        self.add_notification(f"Sending to Master AI: '{command_text}'")
        QApplication.processEvents()

        main_window = self.window() # Get reference to MainWindow
        if not hasattr(main_window, 'master_ai_agent') or not main_window.master_ai_agent:
            self.add_notification("Master AI Error: Master AI Agent not initialized in MainWindow.")
            return

        try:
            # The Master AI's interpret_command might need context, like the current document
            # This context needs to be determined by MainWindow or passed appropriately
            active_doc_view = main_window._get_active_document_view()
            context_document_obj = active_doc_view.document if active_doc_view else None

            # The interpret_command in PostalEquityAppAI currently returns a string.
            # We want it to potentially return structured data or trigger further actions
            # that result in notifications.
            # For now, we assume it might return a direct response string or None if it posts its own notifications.
            response = main_window.master_ai_agent.interpret_command(command_text, context_document=context_document_obj)

            if response: # If Master AI returns a direct textual response
                self.add_notification(f"Master AI Response: {response}")

            # If the command was 'validate current document', the Master AI (or ClauseConformer via MasterAI)
            # might have added its own detailed notifications.
            # The dashboard's notification list will show these.

            self.master_ai_command_input.clear() # Clear input after sending

        except Exception as e:
            error_msg = f"Error processing Master AI command: {e}"
            print(error_msg)
            self.add_notification(error_msg)


    def _fetch_github_repo_info(self):
        repo_name = self.github_repo_input.text().strip()
        if not repo_name:
            self.github_repo_info_display.setText("Error: Repository name cannot be empty.")
            return

        self.github_repo_info_display.setText(f"Fetching information for {repo_name}...")
        QApplication.processEvents() # Ensure UI updates before potentially long call

        try:
            # It's better to import where needed or at the top of the module,
            # but for this specific integration, ensure it's available.
            # Assuming api_integrations.py is in a place Python can find it (e.g., PYTHONPATH or same level)
            # For our project structure, it's one level up from app.ui then into root.
            # Proper way would be to access it via a controller or service in app.core
            # that has access to api_integrations. For now, direct import for simplicity in this step.

            # --- Temporary direct import path adjustment for this example ---
            # This is NOT ideal for production code but helps in this isolated step.
            import sys
            import os
            # Add project root to path to find api_integrations.py
            # This assumes dashboard_view.py is in app/ui/
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            # --- End temporary path adjustment ---

            from api_integrations import github_fetch_repo_metadata # Now this import should work

            metadata = github_fetch_repo_metadata(repo_name)

            if metadata:
                info_text = (
                    f"Name: {metadata.get('name', 'N/A')}\n"
                    f"Full Name: {metadata.get('full_name', 'N/A')}\n"
                    f"Description: {metadata.get('description', 'N/A')}\n"
                    f"Stars: {metadata.get('stargazers_count', 'N/A')}\n"
                    f"Forks: {metadata.get('forks_count', 'N/A')}\n"
                    f"Last Updated: {metadata.get('updated_at', 'N/A')}\n"
                    f"URL: {metadata.get('html_url', 'N/A')}"
                )
                self.github_repo_info_display.setText(info_text)
            else:
                self.github_repo_info_display.setText(f"No metadata returned for {repo_name}.")

        except ImportError as ie:
            error_msg = "Error: Could not import API integration module. Ensure 'api_integrations.py' is accessible."
            print(f"{error_msg}\nDetails: {ie}")
            self.github_repo_info_display.setText(error_msg)
        except ValueError as ve: # Handles GITHUB_PAT not set from api_integrations
            error_msg = f"Configuration Error: {ve}"
            print(error_msg)
            self.github_repo_info_display.setText(error_msg)
        except Exception as e: # Catches HTTPError and other RequestExceptions from _make_github_request
            error_msg = f"API Error: Could not fetch repository info for '{repo_name}'.\nDetails: {e}"
            print(error_msg) # Log the full error to console
            # Display a user-friendly part of the error.
            # The exception 'e' from _make_github_request already contains a formatted string.
            self.github_repo_info_display.setText(str(e))
        finally:
            # Clean up path if it was modified, though for multiple calls it might be better to set it once.
            # This is simplistic for now.
            if project_root in sys.path and project_root == sys.path[0]: # if we added it
                 if sys.path[0] == project_root: # Check if it's still the first item
                    sys.path.pop(0)


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
