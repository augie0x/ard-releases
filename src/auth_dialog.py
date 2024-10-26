# auth_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QCheckBox
)

from .api_client import APIClient
from .utils import SettingsManager


class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OAuth Authentication")
        self.setModal(True)
        self.resize(400, 300)

        self.api_client = APIClient()
        self.settings_manager = SettingsManager()

        # Layouts
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Input Fields
        self.hostname_input = QLineEdit()
        self.hostname_input.setToolTip("Enter only the base hostname")
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.client_id_input = QLineEdit()
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)

        # Remember Me Checkbox
        self.remember_checkbox = QCheckBox("Remember these settings")

        # Load saved settings if they exist
        self.load_saved_settings()

        # Adding widgets to form layout
        form_layout.addRow("Tenant URL:", self.hostname_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Client ID:", self.client_id_input)
        form_layout.addRow("Client Secret:", self.client_secret_input)
        form_layout.addRow(self.remember_checkbox)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.authenticate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_saved_settings(self):
        """Load saved settings if they exist"""
        if self.settings_manager.has_saved_credentials():
            self.hostname_input.setText(self.settings_manager.base_hostname or '')
            self.username_input.setText(self.settings_manager.username or '')
            self.password_input.setText(self.settings_manager.password or '')
            self.client_id_input.setText(self.settings_manager.client_id or '')
            self.client_secret_input.setText(self.settings_manager.client_secret or '')
            self.remember_checkbox.setChecked(True)

    def authenticate(self):
        """
        Handles the authentication process when the user clicks OK.
        """
        # Gather input data
        base_hostname = self.hostname_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        # Validate input
        if not all([base_hostname, username, password, client_id, client_secret]):
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        # Validate the URL format
        if not (base_hostname.startswith("http://") or base_hostname.startswith("https://")):
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL (including http:// or https://).")
            return

        # Ensure no trailing slash
        if base_hostname.endswith("/"):
            base_hostname = base_hostname[:-1]

        # Authenticate using APIClient
        try:
            token_data = self.api_client.authenticate(
                base_hostname, username, password, client_id, client_secret
            )
            if token_data:
                if self.remember_checkbox.isChecked():
                    # Save credentials and tokens
                    self.settings_manager.save_credentials(
                        base_hostname, username, password, client_id, client_secret, token_data
                    )
                else:
                    # Clear saved credentials if "Remember Me" is unchecked
                    self.settings_manager.clear_credentials()

                QMessageBox.information(self, "Success", "Authentication successful.")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Authentication Failed", f"Error: {str(e)}")
