# main.py
import csv
import sys
import os


def setup_environment():
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        bundle_dir = sys._MEIPASS
    else:
        # Running in normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # Add resources path to environment
    os.environ['RESOURCEPATH'] = os.path.join(bundle_dir, 'resources')

    # Add Qt plugin path
    if getattr(sys, 'frozen', False):
        os.environ['QT_PLUGIN_PATH'] = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'plugins')


def get_resource_path(relative_path):
    """Get the absolute path to a resource file"""
    if hasattr(sys, '_MEIPASS'):
        # Running as compiled executable
        return os.path.join(sys._MEIPASS, relative_path)
    # Running as script
    return os.path.join(os.path.abspath("."), relative_path)

from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, \
    QAction, QHBoxLayout, QLabel, QLineEdit, QFrame
from qt_material import apply_stylesheet

from src.api_client import APIClient
from src.auth_dialog import AuthDialog
from src.connection_dialog import ConnectionDialog
from src.connection_manager import ConnectionManager
from src.connection_selection import ConnectionSelectionDialog
from src.data_loader import DataLoader
from src.table_view import TableView
from src.utils import SettingsManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        if sys.platform.startswith('win'):
            # Ensure proper DPI scaling on Windows
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
            os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

        # Setup main window
        self.setWindowTitle("Adjustment Rules Demystifier")
        self.setGeometry(100, 100, 1600, 800)  # Adjust as needed

        # Initialize managers
        self.api_client = APIClient()
        self.settings_manager = SettingsManager()
        self.connection_manager = ConnectionManager()

        # Create central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Top Layout for Buttons and Search Bar
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Left side buttons group
        left_buttons_layout = QHBoxLayout()

        # Load JSON Button
        self.load_button = QPushButton()
        self.load_button.setIcon(QIcon(get_resource_path("resources/images/open.png")))
        self.load_button.setIconSize(QSize(24, 24))
        self.load_button.setToolTip("Load Adjustment Rule JSON")
        self.load_button.clicked.connect(self.load_json_file)
        self.load_button.setFixedSize(40, 40)
        self.load_button.setFlat(True)
        left_buttons_layout.addWidget(self.load_button)

        # Export CSV Button
        self.export_button = QPushButton()
        self.export_button.setIcon(QIcon(get_resource_path("resources/images/csv.png")))
        self.export_button.setIconSize(QSize(24, 24))
        self.export_button.setToolTip("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setFixedSize(40, 40)
        self.export_button.setFlat(True)
        left_buttons_layout.addWidget(self.export_button)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        left_buttons_layout.addWidget(separator)

        # API Connection buttons group

        # Manage Connections button
        self.manage_connections_btn = QPushButton()
        self.manage_connections_btn.setIcon(QIcon(get_resource_path("resources/images/manage.png")))
        self.manage_connections_btn.setIconSize(QSize(24, 24))
        self.manage_connections_btn.setToolTip("Manage Connections")
        self.manage_connections_btn.clicked.connect(self.show_connection_manager)
        self.manage_connections_btn.setFixedSize(40, 40)
        self.manage_connections_btn.setFlat(True)
        left_buttons_layout.addWidget(self.manage_connections_btn)

        # Connect to Tenant button
        self.connect_btn = QPushButton()
        self.connect_btn.setIcon(QIcon(get_resource_path("resources/images/connect.png")))
        self.connect_btn.setIconSize(QSize(24, 24))
        self.connect_btn.setToolTip("Connect to Tenant")
        self.connect_btn.clicked.connect(self.show_connection_selector)
        self.connect_btn.setFixedSize(40, 40)
        self.connect_btn.setFlat(True)
        left_buttons_layout.addWidget(self.connect_btn)

        # Fetch API Button
        self.fetch_api_button = QPushButton()
        self.fetch_api_button.setIcon(QIcon(get_resource_path("resources/images/get.png")))
        self.fetch_api_button.setIconSize(QSize(24, 24))
        self.fetch_api_button.setToolTip("Reteieve Adjustment Rules")
        self.fetch_api_button.clicked.connect(self.get_adjustment_rules_api)
        self.fetch_api_button.setEnabled(False)
        self.fetch_api_button.setFixedSize(40, 40)
        self.fetch_api_button.setFlat(True)
        left_buttons_layout.addWidget(self.fetch_api_button)

        # Add left buttons group to top layout
        top_layout.addLayout(left_buttons_layout)

        # Add stretch to push search to the right
        top_layout.addStretch()

        # Search Layout (right side)
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter search term...")
        self.search_bar.textChanged.connect(self.search_table)
        search_layout.addWidget(self.search_bar)

        # Add search layout to top layout
        top_layout.addLayout(search_layout)

        # Add menu bar
        self.create_menu_bar()

        # Table Widget to Display Adjustment Rules
        self.table_view = TableView()
        main_layout.addWidget(self.table_view)

    def create_menu_bar(self):
        """Create the menu bar with connection management options"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        open_action = QAction("&Open", self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_json_file)
        file_menu.addAction(open_action)

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut('Ctrl+W')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # Connection menu
        connection_menu = menubar.addMenu('Connections')

        manage_action = QAction('Manage Connections...', self)
        manage_action.setShortcut('Ctrl+M')
        manage_action.triggered.connect(self.show_connection_manager)
        connection_menu.addAction(manage_action)

        connect_action = QAction('Connect to Tenant...', self)
        connect_action.setShortcut('Ctrl+C')
        connect_action.triggered.connect(self.show_connection_selector)
        connection_menu.addAction(connect_action)

        # Add separator
        connection_menu.addSeparator()

        disconnect_action = QAction('Disconnect', self)
        disconnect_action.triggered.connect(self.disconnect_tenant)
        connection_menu.addAction(disconnect_action)

    def show_connection_manager(self):
        """Show the connection manager dialog"""
        dialog = ConnectionDialog(self)
        dialog.exec_()

    def show_connection_selector(self):
        """Show the connection selector dialog"""
        connections = self.connection_manager.get_all_connections()
        if not connections:
            reply = QMessageBox.question(
                self, "No Saved Connections",
                "No saved connections found. Would you like to add a connection now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.show_connection_manager()
            return

        dialog = ConnectionSelectionDialog(self)
        if dialog.exec_() == ConnectionSelectionDialog.Accepted:
            selected_connection = dialog.get_selected_connection()
            if selected_connection:
                self.authenticate_with_saved_connection(selected_connection)

    def disconnect_tenant(self):
        """Disconnect from current tenant"""
        self.api_client.set_tokens(None, None, None)
        self.fetch_api_button.setEnabled(False)
        # self.connect_btn.setText("Connect to Tenant")
        QMessageBox.information(self, "Disconnected", "Successfully disconnected from tenant.")

    def update_connection_status(self, connected=False, tenant_name=None):
        """Update UI elements based on connection status"""
        self.fetch_api_button.setEnabled(connected)
        # if connected and tenant_name:
        # self.connect_btn.setText(f"Connected: {tenant_name}")
        # else:
        # self.connect_btn.setText("Connect to Tenant")

    # In main.py, add to the MainWindow class:

    # In main.py

    def authenticate_with_saved_connection(self, connection_name):
        """Handle authentication when switching connections"""
        credentials = self.connection_manager.get_connection(connection_name)
        if not credentials:
            QMessageBox.warning(self, "Error", "Could not find connection details.")
            return

        try:
            # First, clear existing connection state
            self.api_client.clear_tokens()

            # Switch to new connection
            if self.api_client.switch_connection(credentials):
                self.update_connection_status(True, connection_name)
                QMessageBox.information(self, "Success", f"Connected to {connection_name}")

                # Verify token state
                if not self.api_client.access_token or not self.api_client.refresh_token:
                    QMessageBox.warning(self, "Warning", "Connection successful but token state is incomplete.")
                    self.update_connection_status(False)
                    return
            else:
                self.update_connection_status(False)
                QMessageBox.critical(self, "Error", "Failed to connect. Please check your credentials.")

        except Exception as e:
            QMessageBox.critical(self, "Authentication Failed", str(e))
            self.update_connection_status(False)

    def update_connection_status(self, connected=False, tenant_name=None):
        self.fetch_api_button.setEnabled(connected)
        # if connected and tenant_name:
        # self.connect_btn.setText(f"Connected: {tenant_name}")
        # else:
        # self.connect_btn.setText("Connect to Tenant")

    def update_auth_status(self):
        """Update UI elements based on authentication status"""
        if (self.settings_manager.has_saved_credentials() and
                self.settings_manager.access_token is not None):
            # self.auth_button.setText("Authenticate")
            self.fetch_api_button.setEnabled(True)
        else:
            # self.auth_button.setText("Authenticate")
            self.fetch_api_button.setEnabled(False)

    def open_auth_dialog(self):
        dialog = AuthDialog(self)
        if dialog.exec_() == AuthDialog.Accepted:
            # Refresh tokens from settings
            self.settings_manager.load_tokens()
            self.api_client.set_tokens(
                self.settings_manager.access_token,
                self.settings_manager.refresh_token,
                self.settings_manager.token_type
            )
            QMessageBox.information(self, "Success", "Authentication successful.")

    def load_saved_tokens(self):
        settings = QSettings('YourCompany', 'AdjustmentRuleApp')
        self.auth_url = settings.value('auth_url', type=str)
        self.username = settings.value('username', type=str)
        self.password = settings.value('password', type=str)
        self.client_id = settings.value('client_id', type=str)
        self.client_secret = settings.value('client_secret', type=str)
        self.access_token = settings.value('access_token', type=str)
        self.refresh_token = settings.value('refresh_token', type=str)
        self.token_type = settings.value('token_type', type=str)
        self.expires_in = settings.value('expires_in', type=int)
        self.scope = settings.value('scope', type=str)

    def get_adjustment_rules_api(self):
        if not self.api_client.access_token:
            QMessageBox.warning(self, "Authentication Required", "Please authenticate first.")
            return
        try:
            data = self.api_client.get_adjustment_rules()

            #print("\nAPI Response Debug:")
            #print(f"Data type: {type(data)}")
            if isinstance(data, list):
                #print(f"Number of rules: {len(data)}")
                if data:
                    triggers = []

            # Handle the list response directly
            if isinstance(data, list):
                for rule in data:
                    # Extract the rule name from the top level
                    rule_name = rule.get('name', 'Unknown Rule')
                    #print(f"Processing rule: {rule_name}")  # Debug print

                    if 'ruleVersions' in rule and 'adjustmentRuleVersion' in rule['ruleVersions']:
                        versions = rule['ruleVersions']['adjustmentRuleVersion']
                        for version in versions:
                            if 'triggers' in version and 'adjustmentTriggerForRule' in version['triggers']:
                                # Add the rule name to each trigger
                                version_triggers = version['triggers']['adjustmentTriggerForRule']
                                for trigger in version_triggers:
                                    trigger_copy = dict(trigger)  # Create a copy of the trigger
                                    trigger_copy['ruleName'] = rule_name  # Add the rule name
                                    triggers.append(trigger_copy)
                                    #print(f"Added trigger for rule: {rule_name}")  # Debug print
            else:
                # Handle other data types through the DataLoader
                triggers = DataLoader.extract_triggers(data)

            # Verify triggers before display
            if triggers:
                self.table_view.display_triggers(triggers)
                QMessageBox.information(self, "Success",
                                        f"Adjustment Rules retrieved successfully. Found {len(rule_name)} rules.")
            else:
                QMessageBox.warning(self, "No Triggers Found",
                                    "No adjustment triggers were found in the API response.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred while fetching Adjustment Rules:\n{str(e)}")

    def load_json_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Adjustment Rule JSON File",
            "",
            "JSON Files (*.json);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                data = DataLoader.load_json(file_name)
                if data:
                    triggers = DataLoader.extract_triggers(data)
                    # print(f"Number of triggers found: {len(triggers)}")

                    if triggers:
                        self.table_view.display_triggers(triggers)
                        QMessageBox.information(self, "Success",
                                                f"JSON file loaded and parsed successfully. Found {len(triggers)} triggers.")
                    else:
                        QMessageBox.warning(self, "No Triggers Found",
                                            "No adjustment triggers were found in the JSON file. Please verify the file format.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to load JSON file or file is empty.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error processing JSON file:\n{str(e)}")
                import traceback
                traceback.print_exc()

    def search_table(self, text):
        """
        Filters the table rows based on the search text.
        Shows entire rows that contain the search term in any cell.
        """
        text = text.lower()
        for row in range(self.table_view.rowCount()):
            match = False
            for column in range(self.table_view.columnCount()):
                item = self.table_view.item(row, column)
                if text in item.text().lower():
                    match = True
                    break
            self.table_view.setRowHidden(row, not match)

    def export_to_csv(self):
        """
        Exports the table data to a CSV file.
        """
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save as CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )
        if file_name:
            if not file_name.endswith(".csv"):
                file_name += ".csv"
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write headers
                    headers = []
                    for i in range(self.table_view.columnCount()):
                        header_item = self.table_view.horizontalHeaderItem(i)
                        headers.append(header_item.text() if header_item else f"Column {i}")
                    writer.writerow(headers)
                    # Write data rows
                    for row in range(self.table_view.rowCount()):
                        if not self.table_view.isRowHidden(row):  # Only export visible rows
                            row_data = []
                            for column in range(self.table_view.columnCount()):
                                item = self.table_view.item(row, column)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                QMessageBox.information(self, "Success", "Data exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data:\n{str(e)}")

    def resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # Then use it for loading resources:
    icon_path = resource_path("resources/images/icon.ico")


def main():
    app = QApplication(sys.argv)

    # QT_Material Design stylesheet
    apply_stylesheet(app, theme='light_teal_500.xml')

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
