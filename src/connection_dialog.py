# connection_dialog.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDialogButtonBox, QMessageBox, QPushButton, QLabel, QFrame, QListWidget, QMenu
)

from .connection_manager import ConnectionManager


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Manager")
        self.setModal(True)
        self.resize(600, 400)

        self.connection_manager = ConnectionManager()
        self.setup_ui()
        self.load_saved_connections()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Left side - Connection List
        left_layout = QVBoxLayout()

        # Connection list
        self.connection_list = QListWidget()
        self.connection_list.itemClicked.connect(self.load_connection)  # type: ignore
        self.connection_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connection_list.customContextMenuRequested.connect(self.show_context_menu)  # type: ignore
        left_layout.addWidget(QLabel("Saved Connections:"))
        left_layout.addWidget(self.connection_list)

        # Buttons for list management
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.clear_form)  # type: ignore
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_connection)  # type: ignore
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)

        # Right side - Connection Details
        right_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Connection name field
        self.connection_name = QLineEdit()
        form_layout.addRow("Connection Name:", self.connection_name)

        # Input fields
        self.hostname_input = QLineEdit()
        self.hostname_input.setPlaceholderText("https://tenant.npr.mykronos.com")
        self.hostname_input.setToolTip("Enter the base hostname, e.g., https://teamglobalexp-uat.npr.mykronos.com")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Client ID")
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Client Secret")
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Tenant URL:", self.hostname_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Client ID:", self.client_id_input)
        form_layout.addRow("Client Secret:", self.client_secret_input)

        right_layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Close
        )
        self.save_button = buttons.button(QDialogButtonBox.Save)
        self.save_button.clicked.connect(self.save_connection)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        right_layout.addWidget(buttons)

        # Add layouts to main layout
        layout.addLayout(left_layout, 1)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        layout.addLayout(right_layout, 2)
        self.setLayout(layout)

    def load_saved_connections(self):
        """Load saved connections into the list"""
        self.connection_list.clear()
        connections = self.connection_manager.get_all_connections()
        self.connection_list.addItems(sorted(connections.keys()))

    def load_connection(self, item):
        """Load selected connection details into form"""
        connection_name = item.text()
        credentials = self.connection_manager.get_connection(connection_name)

        self.connection_name.setText(connection_name)
        self.hostname_input.setText(credentials.get('base_hostname', ''))
        self.username_input.setText(credentials.get('username', ''))
        self.password_input.setText(credentials.get('password', ''))
        self.client_id_input.setText(credentials.get('client_id', ''))
        self.client_secret_input.setText(credentials.get('client_secret', ''))

    def clear_form(self):
        """Clear all form fields"""
        self.connection_name.clear()
        self.hostname_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.client_id_input.clear()
        self.client_secret_input.clear()
        self.connection_list.clearSelection()

    def save_connection(self):
        """Save or update connection details"""
        connection_name = self.connection_name.text().strip()

        if not connection_name:
            QMessageBox.warning(self, "Error", "Please enter a connection name.")
            return

        credentials = {
            'base_hostname': self.hostname_input.text().strip(),
            'username': self.username_input.text().strip(),
            'client_id': self.client_id_input.text().strip(),
            'client_secret': self.client_secret_input.text().strip(),
            'password': self.password_input.text().strip()
        }

        if not all(credentials.values()):
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        self.connection_manager.save_connection(connection_name, credentials)
        self.load_saved_connections()
        QMessageBox.information(self, "Success", "Connection saved successfully.")
        self.clear_form()

    def delete_connection(self):
        """Delete selected connection"""
        current_item = self.connection_list.currentItem()
        if not current_item:
            return

        connection_name = current_item.text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the connection '{connection_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.connection_manager.remove_connection(connection_name)
            self.load_saved_connections()
            self.clear_form()

    def show_context_menu(self, position):
        """Show context menu for connection list"""
        current_item = self.connection_list.currentItem()
        if not current_item:
            return

        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.connection_list.mapToGlobal(position))

        if action == delete_action:
            self.delete_connection()
