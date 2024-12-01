from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QDialogButtonBox, QLabel

from .connection_manager import ConnectionManager
from .connection_dialog import ConnectionDialog


class ConnectionSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Connection")
        self.setModal(True)

        self.connection_manager = ConnectionManager()

        layout = QVBoxLayout()

        # Connection selector
        layout.addWidget(QLabel("Select a connection:"))
        self.connection_combo = QComboBox()
        self.connection_combo.addItems(
            sorted(self.connection_manager.get_all_connections().keys())
        )
        layout.addWidget(self.connection_combo)

        # Manage connections button
        manage_button = QPushButton("Manage Connections")
        manage_button.clicked.connect(self.show_connection_manager)
        layout.addWidget(manage_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selected_connection(self):
        return self.connection_combo.currentText()

    def show_connection_manager(self):
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.connection_combo.clear()
            self.connection_manager.addItems(
                sorted(self.connection_manager.get_all_connections().keys())
            )
