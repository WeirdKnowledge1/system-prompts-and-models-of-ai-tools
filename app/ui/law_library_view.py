from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
                             QLabel, QSplitter, QGroupBox, QListWidgetItem, QPushButton, # Added QPushButton
                             QFileDialog, QMessageBox) # Added QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QDir
import os
import shutil # For file copying
from app.utils.constants import CODEX_VAULT_DIR

LAW_LIBRARY_SUBDIR = "codex_vault_sources/law_library"
LAW_LIBRARY_PATH = os.path.join(CODEX_VAULT_DIR, LAW_LIBRARY_SUBDIR)

class LawLibraryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LawLibraryView")
        self._setup_ui()
        self.refresh_library_list() # Initial load

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title Label (Optional, but good for clarity)
        title_label = QLabel("Law Library & Codex Explorer")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Main content area with a splitter
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left Panel: Document List
        left_panel_group = QGroupBox("Library Documents")
        left_panel_layout = QVBoxLayout()

        # Search layout
        search_layout = QHBoxLayout()
        self.search_library_input = QLineEdit()
        self.search_library_input.setPlaceholderText("Enter keyword to search...")
        self.search_library_button = QPushButton("Search")
        self.search_library_button.clicked.connect(self._search_library_documents)
        self.clear_search_button = QPushButton("Show All")
        self.clear_search_button.clicked.connect(self.refresh_library_list)
        search_layout.addWidget(self.search_library_input, 1) # Stretch input
        search_layout.addWidget(self.search_library_button)
        search_layout.addWidget(self.clear_search_button)
        left_panel_layout.addLayout(search_layout)

        self.doc_list_widget = QListWidget()
        self.doc_list_widget.itemSelectionChanged.connect(self._on_document_selected) # Connect the signal
        left_panel_layout.addWidget(self.doc_list_widget)

        self.upload_to_library_button = QPushButton("Upload Document(s) to Library")
        self.upload_to_library_button.clicked.connect(self._upload_files_to_library)
        left_panel_layout.addWidget(self.upload_to_library_button)

        left_panel_group.setLayout(left_panel_layout)

        splitter.addWidget(left_panel_group)

        # Right Panel: Document Content Viewer
        right_panel_group = QGroupBox("Document Content")
        right_panel_layout = QVBoxLayout()

        self.doc_content_viewer = QTextEdit()
        self.doc_content_viewer.setReadOnly(True)
        right_panel_layout.addWidget(self.doc_content_viewer)
        right_panel_group.setLayout(right_panel_layout)

        splitter.addWidget(right_panel_group)

        # Adjust initial sizes of splitter panes (e.g., 1/3 for list, 2/3 for content)
        splitter.setSizes([250, 750]) # Adjust these values as needed

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def refresh_library_list(self):
        """Scans the law library directory and populates the list widget."""
        self.doc_list_widget.clear()
        self.doc_content_viewer.setPlainText("Select a document from the list to view its content.") # Reset content view

        try:
            os.makedirs(LAW_LIBRARY_PATH, exist_ok=True)

            found_files = []
            for filename in os.listdir(LAW_LIBRARY_PATH):
                if filename.lower().endswith((".txt", ".md")):
                    full_path = os.path.join(LAW_LIBRARY_PATH, filename)
                    if os.path.isfile(full_path): # Ensure it's a file
                        found_files.append({"name": filename, "path": full_path})

            # Sort files by name for consistent order
            found_files.sort(key=lambda x: x["name"].lower())

            if not found_files:
                self.doc_list_widget.addItem(QListWidgetItem("No library documents found."))
                # self.doc_list_widget.setEnabled(False) # Optional: disable list if empty
            else:
                # self.doc_list_widget.setEnabled(True) # Optional: ensure enabled
                for file_info in found_files:
                    item = QListWidgetItem(file_info["name"])
                    item.setData(Qt.ItemDataRole.UserRole, file_info["path"]) # Store full path
                    self.doc_list_widget.addItem(item)

        except OSError as e:
            error_item = QListWidgetItem(f"Error accessing library: {e.strerror}")
            self.doc_list_widget.addItem(error_item)
            self.doc_content_viewer.setPlainText(f"Could not load library documents.\nError: {e}")
            # self.doc_list_widget.setEnabled(False)
        except Exception as e_gen: # Catch any other unexpected error
            error_item = QListWidgetItem(f"Unexpected error: {str(e_gen)}")
            self.doc_list_widget.addItem(error_item)
            self.doc_content_viewer.setPlainText(f"An unexpected error occurred while loading library documents.\nError: {str(e_gen)}")
            # self.doc_list_widget.setEnabled(False)


    def _on_document_selected(self):
        selected_items = self.doc_list_widget.selectedItems()
        if not selected_items:
            self.doc_content_viewer.setPlainText("Select a document from the list to view its content.")
            return

        list_item = selected_items[0]
        file_path = list_item.data(Qt.ItemDataRole.UserRole) # Retrieve the full path

        if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Basic content type differentiation for display (e.g., Markdown vs Plain Text)
                if file_path.lower().endswith(".md"):
                    # QTextEdit can render some basic Markdown.
                    # For more complex rendering, a dedicated Markdown library/widget would be needed.
                    self.doc_content_viewer.setMarkdown(content)
                else: # .txt files
                    self.doc_content_viewer.setPlainText(content)

            except UnicodeDecodeError:
                self.doc_content_viewer.setPlainText(f"Error: Could not decode file '{os.path.basename(file_path)}'.\n"
                                                     "The file may not be UTF-8 encoded or is corrupted.")
            except IOError as e:
                self.doc_content_viewer.setPlainText(f"Error reading file: {os.path.basename(file_path)}\n{e.strerror}")
            except Exception as e_gen:
                 self.doc_content_viewer.setPlainText(f"An unexpected error occurred while reading file: {os.path.basename(file_path)}\n{str(e_gen)}")
        elif file_path: # Path stored but file doesn't exist (e.g. deleted externally)
            self.doc_content_viewer.setPlainText(f"Error: File not found or is not accessible:\n{file_path}")
            # Optionally, remove the item from the list if it's confirmed missing
            # self.doc_list_widget.takeItem(self.doc_list_widget.row(list_item))
        else: # No path data associated with item, or item is placeholder like "No documents found"
            # This case might happen if the "No library documents found." item is somehow selected,
            # or if an item was added without proper UserRole data.
            if list_item.text() == "No library documents found.":
                 self.doc_content_viewer.setPlainText("The library is currently empty or could not be accessed.")
            else:
                 self.doc_content_viewer.setPlainText("Invalid item selected or no file path associated.")

    def _upload_files_to_library(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Text or Markdown Files to Upload to Law Library",
            QDir.homePath(), # Start in user's home directory
            "Text & Markdown Files (*.txt *.md);;All Files (*)"
        )

        if not file_paths:
            return # User cancelled

        success_files = []
        error_files = []
        skipped_files = []

        os.makedirs(LAW_LIBRARY_PATH, exist_ok=True) # Ensure target directory exists

        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(LAW_LIBRARY_PATH, file_name)

                if os.path.exists(destination_path):
                    reply = QMessageBox.question(
                        self, "File Exists",
                        f"The file '{file_name}' already exists in the Law Library.\nOverwrite it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Cancel:
                        QMessageBox.information(self, "Upload Cancelled", "File upload operation cancelled by user.")
                        # Refresh list with any files processed before cancellation
                        self.refresh_library_list()
                        return
                    elif reply == QMessageBox.StandardButton.No:
                        skipped_files.append(file_name)
                        continue # Skip this file
                    # If Yes, proceed to overwrite

                shutil.copy2(file_path, destination_path) # copy2 preserves metadata
                success_files.append(file_name)
            except Exception as e:
                error_files.append(f"{os.path.basename(file_path)} (Error: {e})")

        # Refresh the list widget to show newly uploaded files
        self.refresh_library_list()

        # Prepare and show report message
        message_parts = []
        if success_files:
            message_parts.append(f"Successfully uploaded:\n- " + "\n- ".join(success_files))
        if skipped_files:
            message_parts.append(f"Skipped (not overwritten):\n- " + "\n- ".join(skipped_files))
        if error_files:
            message_parts.append(f"Errors during upload:\n- " + "\n- ".join(error_files))

        if not message_parts:
             final_message = "No files were selected or processed."
        else:
            final_message = "\n\n".join(message_parts)

        QMessageBox.information(self, "Law Library Upload Report", final_message.strip())

    def _search_library_documents(self):
        search_term = self.search_library_input.text().strip().lower() # Case-insensitive search

        if not search_term:
            self.refresh_library_list() # If search term is empty, show all
            self.doc_content_viewer.setPlainText("Search cleared. Select a document from the list to view its content.")
            return

        self.doc_list_widget.clear()
        # Keep content viewer as is, or update with search status
        # self.doc_content_viewer.setPlainText(f"Searching for '{search_term}'...") # Optional feedback

        matching_files_count = 0
        try:
            # Ensure LAW_LIBRARY_PATH exists, though refresh_library_list usually does this.
            # No, _search_library_documents should not create the directory. It should only search.
            # If the directory doesn't exist, os.listdir will raise FileNotFoundError, caught below.

            for filename in os.listdir(LAW_LIBRARY_PATH): # Search current files in directory
                if filename.lower().endswith((".txt", ".md")):
                    full_path = os.path.join(LAW_LIBRARY_PATH, filename)
                    if os.path.isfile(full_path):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if search_term in content.lower(): # Case-insensitive content check
                                item = QListWidgetItem(filename)
                                item.setData(Qt.ItemDataRole.UserRole, full_path)
                                self.doc_list_widget.addItem(item)
                                matching_files_count += 1
                        except UnicodeDecodeError:
                            print(f"Skipping file due to encoding error during search: {filename}")
                        except IOError:
                            print(f"Skipping file due to IO error during search: {filename}")

            if matching_files_count == 0:
                self.doc_list_widget.addItem(QListWidgetItem(f"No documents found containing '{search_term}'."))
                self.doc_content_viewer.setPlainText(f"No results for '{search_term}'.")
            else:
                # Content viewer message updated after list is populated
                self.doc_content_viewer.setPlainText(f"{matching_files_count} document(s) found containing '{search_term}'. Select one to view.")

        except FileNotFoundError:
             self.doc_list_widget.addItem(QListWidgetItem("Law Library directory not found."))
             self.doc_content_viewer.setPlainText("Error: Law Library directory does not exist.")
        except OSError as e:
            self.doc_list_widget.addItem(QListWidgetItem(f"Error during search: {e.strerror}"))
            self.doc_content_viewer.setPlainText(f"Error accessing library for search.\nError: {e}")
        except Exception as e_gen: # Catch any other unexpected error
            self.doc_list_widget.addItem(QListWidgetItem(f"Unexpected error during search: {str(e_gen)}"))
            self.doc_content_viewer.setPlainText(f"An unexpected error occurred during search.\nError: {str(e_gen)}")


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    library_view = LawLibraryView()
    library_view.setWindowTitle("Law Library & Codex View - Test")
    library_view.setGeometry(100, 100, 1000, 700)
    library_view.show()

    sys.exit(app.exec())
