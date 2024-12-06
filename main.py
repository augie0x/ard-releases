# main.py
import csv
import json
import os
import sys
import zipfile
from datetime import datetime

import requests
from PyQt5.QtCore import QSettings, QSize, QThread, pyqtSignal, QTimer, Qt, QSharedMemory
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, \
    QAction, QHBoxLayout, QLabel, QLineEdit, QFrame, QComboBox, QProgressDialog
from qt_material import apply_stylesheet

from src.about_dialog import AboutDialog
from src.adjustment_rules_utils import AdjustmentRuleUpdater
from src.api_client import APIClient
from src.auth_dialog import AuthDialog
from src.connection_dialog import ConnectionDialog
from src.connection_manager import ConnectionManager
from src.connection_selection import ConnectionSelectionDialog
from src.data_loader import DataLoader
from src.help_dialog import HelpDialog
from src.recent_files_manager import RecentFilesManager
from src.table_view import TableView
from src.utils import SettingsManager
from src.utils import get_resource_path
from src.version_manager import VersionManager
from src.version import __app_name__, __version__

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


icon_path = resource_path("resources/images/icon.ico")

class UpdateWorker(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, version_manager):
        super().__init__()
        self.version_manager = version_manager

    def run(self):
        try:
            installer_path = self.version_manager.download_update(
                progress_callback=lambda p: self.progress.emit(p)
            )
            if installer_path:
                self.finished.emit(installer_path)
            else:
                self.error.emit("Failed to download update")
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        if sys.platform.startswith('win'):
            # Ensure proper DPI scaling on Windows
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
            os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

        self.appKey = 'AdjustmentRuleUpdater_1_1_Mutex'
        self.memory = QSharedMemory(self.appKey)
        if not self.memory.create(1):
            sys.exit(0)

        # Setup main window
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setGeometry(100, 100, 1600, 800)  # Adjust as needed
        self.statusBar = self.statusBar()

        # Initialise managers
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
        self.fetch_api_button.setToolTip("Retrieve Adjustment Rules")
        self.fetch_api_button.clicked.connect(self.get_adjustment_rules_api)
        self.fetch_api_button.setEnabled(False)
        self.fetch_api_button.setFixedSize(40, 40)
        self.fetch_api_button.setFlat(True)
        left_buttons_layout.addWidget(self.fetch_api_button)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        left_buttons_layout.addWidget(separator)

        # Update Rules Button
        self.update_rules_button = QPushButton()
        self.update_rules_button.setIcon(QIcon(get_resource_path("resources/images/update.png")))
        self.update_rules_button.setIconSize(QSize(24, 24))
        self.update_rules_button.setToolTip("Update Adjustment Rules")
        self.update_rules_button.clicked.connect(self.update_adjustment_rules)
        self.update_rules_button.setFixedSize(40, 40)
        self.update_rules_button.setFlat(True)
        self.update_rules_button.setEnabled(False)
        left_buttons_layout.addWidget(self.update_rules_button)

        # Export JSON Button
        self.export_json_button = QPushButton()
        self.export_json_button.setIcon(QIcon(get_resource_path("resources/images/json.png")))
        self.export_json_button.setIconSize(QSize(24, 24))
        self.export_json_button.setToolTip("Export as JSON")
        self.export_json_button.clicked.connect(self.export_to_json)
        self.export_json_button.setFixedSize(40, 40)
        self.export_json_button.setFlat(True)
        self.export_json_button.setEnabled(False)
        left_buttons_layout.addWidget(self.export_json_button)

        # Add left buttons group to top layout
        top_layout.addLayout(left_buttons_layout)

        # Push search bar to the right
        top_layout.addStretch()

        # Rules filter combo box
        self.rule_filter_combo = QComboBox()
        self.rule_filter_combo.setPlaceholderText("Select a rule...")
        self.rule_filter_combo.setFixedWidth(350)
        self.rule_filter_combo.currentIndexChanged.connect(self.filter_by_rule)
        top_layout.addWidget(self.rule_filter_combo)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        top_layout.addWidget(separator)

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

        self.recent_files_manager = RecentFilesManager(max_files=10)

        # Add menu bar
        self.create_menu_bar()

        # Table Widget to Display Adjustment Rules
        self.table_view = TableView()
        main_layout.addWidget(self.table_view)

        # API retrieve and update buttons default state
        self.fetch_api_button.setEnabled(False)
        self.update_rules_button.setEnabled(False)

        # Initialise version manager
        self.version_manager = VersionManager(
            current_version="1.1.0",
            repository_url="https://api.github.com/repos/augie0x/ard-releases"
        )

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(3600000)

        QTimer.singleShot(5000, self.check_for_updates)

    def check_for_updates(self):
        update_available, update_info = self.version_manager.check_for_updates()

        if update_available:
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"Version {update_info['version']} is available. Would you like to update?\n\n"
                f"Release Notes:\n{update_info['release_notes']}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.start_update()

    def start_update(self):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.update_worker = UpdateWorker(self.version_manager)
        self.update_worker.progress.connect(self.progress_dialog.setValue)
        self.update_worker.finished.connect(self.finish_update)
        self.update_worker.error.connect(self.handle_update_error)
        self.update_worker.start()

    def finish_update(self, installer_path):
        self.progress_dialog.close()

        reply = QMessageBox.question(self, "Install Update",
                                     "The update has been downloaded, The application will close to install the update. Continue?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.version_manager.install_update(installer_path)

    def handle_update_error(self, error_message):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Update Error", f"An error occured during the update:\n{error_message}")


    def create_menu_bar(self):
        """Create the menu bar with connection management options"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        open_action = QAction("&Open", self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_json_file)
        file_menu.addAction(open_action)

        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_files_menu()

        # Add separator
        file_menu.addSeparator()

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
        connect_action.setShortcut('Ctrl+T')
        connect_action.triggered.connect(self.show_connection_selector)
        connection_menu.addAction(connect_action)

        # Add separator
        connection_menu.addSeparator()

        disconnect_action = QAction('Disconnect', self)
        disconnect_action.triggered.connect(self.disconnect_tenant)
        connection_menu.addAction(disconnect_action)

        # Help Menu
        help_menu = menubar.addMenu("Help")

        user_guide_action = QAction('User Guide', self)
        user_guide_action.setShortcut('F1')
        user_guide_action.triggered.connect(self.show_help)
        help_menu.addAction(user_guide_action)

        # About Menu
        about_menu = menubar.addMenu("About")
        about_action = QAction('About Adjustment Rule Updater', self)
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

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
        self.update_rules_button.setEnabled(False)
        self.export_json_button.setEnabled(False)
        QMessageBox.information(self, "Disconnected", "Successfully disconnected from tenant.")

    def update_connection_status(self, connected=False, tenant_name=None):
        """Update UI elements based on connection status"""
        # print(f"Updating connection status: connected={connected}, tenant={tenant_name}")  # Debug print
        print(f"Updating connection status: connected={connected}")
        self.fetch_api_button.setEnabled(connected)
        self.update_rules_button.setEnabled(connected)

        if hasattr(self, 'statusBar'):
            if connected and tenant_name:
                self.statusBar.showMessage(f"Connected to: {tenant_name}")
            else:
                self.statusBar.showMessage("Not connected")

    def authenticate_with_saved_connection(self, connection_name):
        """Handle authentication when switching connections"""
        credentials = self.connection_manager.get_connection(connection_name)
        if not credentials:
            QMessageBox.warning(self, "Error", "Could not find connection details.")
            return

        try:
            # Clear existing connection state
            self.api_client.clear_tokens()

            # Switch to new connection
            if self.api_client.switch_connection(credentials):
                self.update_connection_status(True, connection_name)
                QMessageBox.information(self, "Success", f"Connected to {connection_name}")

                # Verify token state
                if not self.api_client.access_token or not self.api_client.refresh_token:
                    QMessageBox.warning(self, "Warning", "Connection successful but token state is incomplete.")
                    self.update_connection_status(False)
                    self.fetch_api_button.setEnabled(False)
                    self.update_rules_button.setEnabled(False)
                    return
            else:
                self.update_connection_status(False)
                self.fetch_api_button.setEnabled(False)
                self.update_rules_button.setEnabled(False)
                QMessageBox.critical(self, "Error", "Failed to connect. Please check your credentials.")

        except Exception as e:
            QMessageBox.critical(self, "Authentication Failed", str(e))
            self.update_connection_status(False)

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
        """
        Retrieves adjustment rules from the API and displays them in the table.
        """
        if not self.api_client.access_token:
            QMessageBox.warning(self, "Authentication Required", "Please authenticate first.")
            return

        try:
            triggers = self.api_client.get_adjustment_rules()  # Now returns triggers directly

            if isinstance(triggers, list):

                if triggers:
                    self.table_view.display_triggers(triggers)
                    self.populate_rule_filter_combo(triggers)
                    self.rule_filter_combo.blockSignals(True)
                    self.rule_filter_combo.setCurrentText("All Rules")
                    self.rule_filter_combo.blockSignals(False)
                    self.filter_by_rule()
                    self.export_json_button.setEnabled(True)
                    self.update_rules_button.setEnabled(True)
                    '''QMessageBox.information(
                        self,
                        "Success",
                        f"Adjustment Rules retrieved successfully."
                    )'''
                else:
                    QMessageBox.warning(
                        self,
                        "No Triggers Found",
                        "No adjustment triggers were found in the API response."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Response",
                    "Received an unexpected response format from the API."
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while fetching Adjustment Rules:\n{str(e)}"
            )
            return None

        finally:
            QApplication.processEvents()

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
                    self.populate_rule_filter_combo(triggers)
                    self.export_json_button.setEnabled(True)
                    self.update_rules_button.setEnabled(True)
                    self.recent_files_manager.add_file(file_name)
                    self.update_recent_files_menu()
                else:
                    QMessageBox.warning(self, "No Triggers Found",
                                        "No adjustment triggers were found in the JSON file. Please verify the file format.")
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
        try:
            # Get table data
            data = self.get_table_data()
            if not data:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

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

                # Exporting data to CSV file
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
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV:\n{str(e)}")
            import traceback
            traceback.print_exc()

    # Update Adjustment Rules functions
    def get_table_data(self):
        """Get all data from the table"""
        data = []
        for row in range(self.table_view.rowCount()):
            row_data = {}
            for col in range(self.table_view.columnCount()):
                header = self.table_view.horizontalHeaderItem(col).text()
                item = self.table_view.item(row, col)
                value = item.text() if item else ""

                # Clean up version number
                if header == "Version Number" and value.startswith("Version "):
                    value = value.replace("Version ", "")

                # Don't include empty or N/A values
                if value and value.lower() != "n/a":
                    row_data[header] = value
                else:
                    row_data[header] = ""

            data.append(row_data)
        return data

    def get_modified_rule_data(self, rule_id):
        """
        Gets all data for a specific rule that has been modified.

        Args:
            rule_id (str): The ID of the rule to get data for

        Returns:
            dict: Complete rule data including all modifications
        """
        rule_data = {}

        # Find all rows that belong to this rule
        for row in range(self.rowCount()):
            current_rule_id = self.item(row, 0).text()
            if current_rule_id == rule_id:
                # Check if this row has any modifications
                row_has_modifications = any((row, col) in self.modified_cells
                                            for col in range(self.columnCount()))

                if row_has_modifications:
                    # Get all data for this row
                    row_data = {}
                    for column in range(self.columnCount()):
                        header = self.horizontalHeaderItem(column).text()
                        item = self.item(row, column)
                        row_data[header] = item.text() if item else ""

                    # If we haven't stored data for this rule yet, store it
                    if not rule_data:
                        rule_data = row_data

        return rule_data

    def _validate_update_payload(self, payload):
        """
        Validates the update payload before sending to API
        """
        if not isinstance(payload, dict) or 'update' not in payload:
            return False

        updates = payload.get('update', [])
        if not isinstance(updates, list) or not updates:
            return False

        for update in updates:
            if not isinstance(update, dict):
                return False
            if 'adjustmentRuleVersion' not in update.get('ruleVersions', {}):
                return False

        return True

    def update_adjustment_rules(self):
        if not self.api_client.access_token:
            QMessageBox.warning(self, "Authentication Required", "Please authenticate first.")
            return

        try:
            modified_data = self.table_view.get_modified_row_data()

            if not modified_data:
                QMessageBox.information(self, "No Changes", "No modifications detected.")
                return

            # Processing each modified rule separately
            for rule_data in modified_data:
                rule_id = rule_data.get('Rule ID')
                if not rule_id:
                    #print("No rule ID found, skipping")
                    continue

                # Get original trigger data from the retreive API
                original_trigger = self.api_client.get_adjustment_rules_by_ids(rule_id)
                if not original_trigger:
                    raise Exception(f"Could not retrieve original data for rule {rule_id}")

                payload = AdjustmentRuleUpdater.create_update_payload([rule_data], original_trigger)

                if not original_trigger:
                    #print(f"\nFailed to find rule {rule_id} in stored data")
                    raise Exception(f"Could not find original data for rule {rule_id}")

                # Create payload using both modified and original data
                #print("Creating update payload")
                payload = AdjustmentRuleUpdater.create_update_payload([rule_data], original_trigger)

                #print(f"\nSending update for rule {rule_id}:")
                #print(json.dumps(payload, indent=2))

                # Send update request
                base_hostname = self.api_client.base_hostname.rstrip('/')
                url = f"{self.api_client.base_hostname}/api/v1/timekeeping/setup/adjustment_rules/{rule_id}"
                # Debug print the URL and payload
                #print(f"\nAttempting to update rule {rule_id}")
                #print(f"URL: {url}")
                #print(f"Payload: {json.dumps(payload, indent=2)}")

                # Set headers
                headers = {
                    'Authorization': f"{self.api_client.token_type} {self.api_client.access_token}",
                    'Content-Type': 'application/json'
                }

                # Make the request using PUT method
                #print("Making PUT request")
                response = requests.put(url, json=payload, headers=headers)
                #print(f"Response status code: {response.status_code}")

                if response.status_code != 200:
                    #print(f"Error response: {response.text}")
                    error_msg = f"Failed to update rule {rule_id}"
                    try:
                        error_details = response.json()
                        #print(f"\nError response: {json.dumps(error_details, indent=2)}")
                        if 'message' in error_details:
                            error_msg += f": {error_details['message']}"
                    except:
                        error_msg += f": {response.text}"
                    raise Exception(error_msg)

            QMessageBox.information(self, "Success", "Rules updated successfully!")
            self.get_adjustment_rules_api()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update rules:\n{str(e)}")

    def export_to_json(self):
        """Export adjustment rules to JSON file"""
        try:
            # Get table data
            data = self.get_table_data()

            if not data:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

            # Create the export payload - get separate rules for file export
            rules_by_id = AdjustmentRuleUpdater.create_export_payload(data, separate_rules=True)

            if not rules_by_id:
                QMessageBox.warning(self, "No Rules", "No valid rules found to export.")
                return

            # Get file name for saving
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"AdjustmentRules_{timestamp}"

            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export as JSON",
                default_name,
                "ZIP Files (*.zip)",
                options=options
            )

            if file_name:
                if not file_name.endswith('.zip'):
                    file_name += '.zip'

                # Create ZIP file with JSON
                with zipfile.ZipFile(file_name, 'w') as zf:
                    for rule_id, rule_data in rules_by_id.items():
                        rule_name = rule_data['name'].replace(' ', '_')
                        json_content = json.dumps(rule_data, indent=2)
                        zf.writestr(f'AdjustmentRule_{rule_id}_{rule_name}/response.json', json_content)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Exported {len(rules_by_id)} adjustment rules successfully."
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export JSON:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def populate_rule_filter_combo(self, triggers):
        """Populate the combo box with unique rule names from triggers."""
        self.rule_filter_combo.clear()
        rule_names = set()

        for trigger in triggers:
            if 'ruleName' in trigger:
                rule_names.add(trigger['ruleName'])

        self.rule_filter_combo.addItem("All Rules")

        for rule_name in sorted(rule_names):
            if rule_name:
                self.rule_filter_combo.addItem(rule_name)

    def filter_by_rule(self):
        """Filter the table based on the selected rule name from the combo box."""
        selected_rule = self.rule_filter_combo.currentText()

        # If "All Rules" is selected, make all rows visible
        if selected_rule == "All Rules":
            for row in range(self.table_view.rowCount()):
                self.table_view.setRowHidden(row, False)
        else:
            # Filter the rows to show only those that match the selected rule name
            for row in range(self.table_view.rowCount()):
                item = self.table_view.item(row, 1)
                if item and item.text() == selected_rule:
                    self.table_view.setRowHidden(row, False)  # Show row if it matches
                else:
                    self.table_view.setRowHidden(row, True)  # Hide row if it does not match

        # Refresh the UI to ensure changes are displayed correctly
        QApplication.processEvents()

    def update_recent_files_menu(self):
        self.recent_menu.clear()

        recent_files = self.recent_files_manager.get_files()
        if not recent_files:
            no_recent = QAction("No Recent Files",self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
            return

        for file_entry in recent_files:
            action = QAction(file_entry['path'],self)
            size_mb = file_entry['size'] / (1024*1024)
            tooltip = (f"Path: {file_entry['path']}\n"
                        f"Size: {size_mb: .2f} MB\n"
                        f"Last accessed: {file_entry['last_accessed']}")
            action.setToolTip(tooltip)
            action.triggered.connect(
                lambda checked, path=file_entry['path']: self.load_recent_files(path)
            )
            self.recent_menu.addAction(action)

            self.recent_menu.addSeparator()
            clear_action = QAction("Clear Recent Files",self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)

    def load_recent_files(self, filepath):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "File Not Found", f"The file {filepath} no longer exists.")
            self.update_recent_files_menu()
            self.statusBar.showMessage("Cannot load recent file, file not found")
            return

        try:
            data = DataLoader.load_json(filepath)
            if data:
                triggers = DataLoader.extract_triggers(data)
                if triggers:
                    self.table_view.display_triggers(triggers)
                    self.populate_rule_filter_combo(triggers)
                    self.recent_files_manager.add_file(filepath)
                    self.update_recent_files_menu()
                    self.statusBar.showMessage(f"File loaded: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading file {filepath}:\n{str(e)}")

    def clear_recent_files(self):
        """
            Clear the recent files list, but only if there are files to clear.
            First checks if the recent files list contains any entries before
            showing
        """
        recent_files = self.recent_files_manager.get_files()

        if not recent_files:
            QMessageBox.information(self, "No Recent Files", "The recent files list is already empty.",QMessageBox.Ok)
            return

        reply = QMessageBox.question(self,"Clear Recent Files", "Are you sure you want to clear the recent files list?",QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.recent_files_manager.clear_recent_files()
            self.update_recent_files_menu()
            self.statusBar.showMessage("Recent files cleared")

def main():
    app = QApplication(sys.argv)

    # QT_Material Design stylesheet
    apply_stylesheet(app, theme='light_teal_500.xml')

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
