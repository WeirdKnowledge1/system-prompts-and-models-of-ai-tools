from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QLineEdit,
                             QDialogButtonBox, QListWidgetItem, QLabel)
from PyQt6.QtCore import Qt
import os

# Assuming LAW_LIBRARY_PATH would be imported from a central constants/config
# For now, defining it here based on previous structure.
# In a real app, this might come from app_context or a settings manager.
from app.utils.constants import CODEX_VAULT_DIR # Assuming this is the base 'data' dir
LAW_LIBRARY_SUBDIR_IN_CODEX = "codex_vault_sources/law_library"
LAW_LIBRARY_PATH_FOR_DIALOG = os.path.join(CODEX_VAULT_DIR, LAW_LIBRARY_SUBDIR_IN_CODEX)


class SelectLawLibraryRefDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Law Library Reference")
        self.setMinimumSize(400, 300)

        self.selected_reference_path = None # Store the relative path of the selected file

        self._setup_ui()
        self._load_library_files()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter documents by name...")
        self.search_input.textChanged.connect(self._filter_list)
        layout.addWidget(self.search_input)

        self.doc_list_widget = QListWidget()
        self.doc_list_widget.itemDoubleClicked.connect(self.accept) # Double-click to select and OK
        layout.addWidget(self.doc_list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _load_library_files(self):
        self.doc_list_widget.clear()
        try:
            os.makedirs(LAW_LIBRARY_PATH_FOR_DIALOG, exist_ok=True)

            all_files = []
            for filename in os.listdir(LAW_LIBRARY_PATH_FOR_DIALOG):
                if filename.lower().endswith((".txt", ".md", ".pdf", ".docx")) and \
                   os.path.isfile(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, filename)):
                    all_files.append(filename)

            all_files.sort(key=str.lower)

            if not all_files:
                self.doc_list_widget.addItem(QListWidgetItem("No documents found in Law Library."))
                self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            else:
                for filename in all_files:
                    # Store the filename (which is relative to LAW_LIBRARY_PATH_FOR_DIALOG)
                    # or a path relative to a known root if preferred.
                    # For simplicity, store filename, EditClauseDialog can prepend path if needed.
                    # Or better, store path relative to LAW_LIBRARY_SUBDIR_IN_CODEX
                    relative_path = os.path.join(LAW_LIBRARY_SUBDIR_IN_CODEX, filename)
                    item = QListWidgetItem(filename)
                    item.setData(Qt.ItemDataRole.UserRole, relative_path)
                    self.doc_list_widget.addItem(item)
                self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

        except OSError as e:
            self.doc_list_widget.addItem(QListWidgetItem(f"Error accessing Law Library: {e.strerror}"))
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        except Exception as e_gen:
            self.doc_list_widget.addItem(QListWidgetItem(f"Unexpected error: {str(e_gen)}"))
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)


    def _filter_list(self):
        filter_text = self.search_input.text().lower()
        for i in range(self.doc_list_widget.count()):
            item = self.doc_list_widget.item(i)
            # Only try to filter if item is not an error/info message
            if item.data(Qt.ItemDataRole.UserRole) is not None:
                item.setHidden(filter_text not in item.text().lower())

    def accept(self):
        selected_items = self.doc_list_widget.selectedItems()
        if selected_items:
            self.selected_reference_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            super().accept()
        else:
            # If OK is clicked with no selection, do nothing or show a message
            # For now, just don't accept if nothing is selected and it's not an info item
            if self.doc_list_widget.count() > 0 and self.doc_list_widget.item(0).data(Qt.ItemDataRole.UserRole) is not None:
                 QMessageBox.warning(self, "No Selection", "Please select a document or cancel.")
            else: # List is empty or shows an error
                 super().reject() # Effectively a cancel if list is unusable


    def get_selected_reference(self) -> str | None:
        return self.selected_reference_path


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    # Create dummy law library files for testing
    os.makedirs(LAW_LIBRARY_PATH_FOR_DIALOG, exist_ok=True)
    with open(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Statute_A.txt"), "w") as f: f.write("Content of Statute A.")
    with open(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Case_Law_B.md"), "w") as f: f.write("# Case Law B\nSummary...")
    with open(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Regulation_C.pdf"), "w") as f: f.write("PDF Content C (mock).")
    with open(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "guideline_d.docx"), "w") as f: f.write("DOCX Content D (mock).")


    app = QApplication(sys.argv)
    dialog = SelectLawLibraryRefDialog()
    if dialog.exec():
        print(f"Selected reference: {dialog.get_selected_reference()}")
    else:
        print("Selection cancelled.")

    # Clean up dummy files
    try:
        os.remove(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Statute_A.txt"))
        os.remove(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Case_Law_B.md"))
        os.remove(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "Regulation_C.pdf"))
        os.remove(os.path.join(LAW_LIBRARY_PATH_FOR_DIALOG, "guideline_d.docx"))
        # Try to remove dir if empty, but don't fail if it's not (e.g. if other tests use it)
        if not os.listdir(LAW_LIBRARY_PATH_FOR_DIALOG):
            os.rmdir(LAW_LIBRARY_PATH_FOR_DIALOG)
            if not os.listdir(os.path.dirname(LAW_LIBRARY_PATH_FOR_DIALOG)): # codex_vault_sources
                 os.rmdir(os.path.dirname(LAW_LIBRARY_PATH_FOR_DIALOG))

    except OSError as e:
        print(f"Error cleaning up test files: {e}")


    sys.exit(app.exec())
