from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox)

from src.version import __app_name__


class HelpDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"{__app_name__} - User Guide")
        self.setModal(True)
        self.resize(700,700)

        layout = QVBoxLayout()

        help_browser = QTextBrowser()
        help_browser.setOpenExternalLinks(True)
        help_browser.setHtml(self.get_help_content())
        layout.addWidget(help_browser)
        help_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    padding: 10px;
                }
            """)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.setStyleSheet("""
               QPushButton {
                   background-color: #008080;
                   color: white;
                   border: none;
                   padding: 6px 20px;
                   border-radius: 4px;
                   min-width: 80px;
               }
               QPushButton:hover {
                   background-color: #036c5f;
               }
               QPushButton:pressed {
                   background-color: #025043;
               }
           """)
        layout.addWidget(buttons)

        self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                }
            """)


        self.setLayout(layout)

    def get_help_content(self):
        """Returns the formatted help content"""
        return """
         <style>
        /* Main text color and font */
        body {
            color: #2c3e50;  /* Dark blue-gray for main text */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }
        
        p { color: #37474F; }
        
        /* Headings */
        h2 {
            color: #1976D2;  /* Material Blue */
            border-bottom: 2px solid #1976D2;
            padding-bottom: 8px;
        }
        
        h3 {
            color: #0D47A1;  /* Darker Blue */
            margin-top: 20px;
        }
        
        h4 {
            color: #2196F3;  /* Lighter Blue */
            margin-top: 15px;
        }
        
        /* List items */
        ul {
            margin-left: 20px;
        }
        
        li {
            color: #37474F;  /* Dark gray-blue */
            margin: 8px 0;
        }
        
        /* Bold text */
        b {
            color: #1565C0;  /* Emphasis blue */
        }
        
        /* Notes section */
        p b {
            color: #E53935;  /* Red for important notes */
        }
        
        li p b {
            color: #E53935;
        }
        
        /* Keyboard shortcuts */
        li b {
            color: #00796B;  /* Teal for shortcuts */
        }
    </style>
        <h2>Adjustment Rules Updater - User Guide</h2>

        <h3>Getting Started</h3>
        <p>This tool helps demystify and analyse adjustment rules and its triggers. Here's how to use the main features:</p>
        <p><b>Note:</b> You must be authenticated before attempting to retrieve or update rules.</p>

        <h4>File Operations</h4>
        <ul>
            <li><b>Load JSON:</b>Click the folder icon or use Ctrl+O to load adjustment rules from a JSON file.</li>
            <li><b>Export to CSV:</b> Click the CSV icon to export the current table to a CSV file.</li>
            <li><b>Export to JSON:</b> Click the JSON icon to export modifications as a JSON file.</li>
        </ul>

        <h4>Connection Management</h4>
        <ul>
            <li><b>Manage:</b> Click the Manage button or use Ctrl+M to open the manage tenant connections dialog to create, edit or delete tenant details.</li>
            <li><b>Connect to Tenant:</b> Use the dropdown that say "Select connection" to select a saved tenant or Ctrl+T select a tenant.</li>
            <li><b>Get Rules:</b> Once connected, use the Get Rules button to retrieve all adjustment rules from the tenant.</li>
        </ul>

        <h4>Table Operations</h4>
        <ul>
            <li><b>Search:</b> Use the search bar to filter rules in real-time.</li>
            <p><b>Note: Search will look through all adjustment rules loaded and not only the one selected in the Rules selector</b></p>
            <li><b>Filter:</b> Use the filter drop down box to only filter the rules and only see specific rules in real-time.</li>
            <li><b>Edit Cells:</b> Double-click any cell to modify its content or start typing while a cell is selected.</li>
            <li><b>Copy/Paste:</b> Use Ctrl+C and Ctrl+V or right-click menu for clipboard operations.</li>
            <li><b>Sort:</b> Click column headers to sort the table.</li>
        </ul>

        <h4>Updates and Modifications</h4>
        <ul>
            <li><b>Manual Upload:</b>Use the JSON button to export a file with individual folders of each rule. Users can select which rule to upload or upload all rules.</li>
            <li><b>Update via API:</b>Use the update icon to send changes to the tenant via API. When updating, it preserves all unmodified triggers and only updates the modified triggers</li>
        </ul>

    """