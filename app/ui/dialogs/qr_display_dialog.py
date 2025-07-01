from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class QRDisplayDialog(QDialog):
    def __init__(self, pixmap: QPixmap, title: str = "QR Code", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        main_layout = QVBoxLayout(self)

        self.qr_label = QLabel()
        if pixmap and not pixmap.isNull():
            # Scale pixmap if it's too large for a dialog, while keeping aspect ratio
            max_size = 400
            if pixmap.width() > max_size or pixmap.height() > max_size:
                self.qr_label.setPixmap(pixmap.scaled(max_size, max_size,
                                                      Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation))
            else:
                self.qr_label.setPixmap(pixmap)
        else:
            self.qr_label.setText("QR Code image not available.")

        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.qr_label)

        # OK Button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        main_layout.addWidget(self.button_box)

        self.setMinimumSize(200, 200) # Ensure dialog is not too small

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    # This test requires a QPixmap, which VeritasProof would generate.
    # For a standalone test, we'd need to create a dummy QPixmap.
    # from app.core.agents import VeritasProof # Assuming VeritasProof is importable

    app = QApplication(sys.argv)

    # Create a dummy pixmap for testing
    dummy_pixmap = QPixmap(200, 200)
    dummy_pixmap.fill(Qt.GlobalColor.cyan)

    # Example with a dummy pixmap
    # In real use, pixmap would come from VeritasProof agent
    # agent = VeritasProof()
    # real_pixmap = agent.generate_qr_for_text("Test QR Data 123")
    # if real_pixmap:
    #    dialog = QRDisplayDialog(real_pixmap, title="Test QR Code")
    #    dialog.exec()
    # else:
    #    print("Failed to generate QR for test.")

    dialog = QRDisplayDialog(dummy_pixmap, title="Dummy QR Code Display")
    dialog.exec()

    sys.exit(app.exec())
