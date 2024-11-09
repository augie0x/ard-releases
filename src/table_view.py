# table_view.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAction, QApplication, QShortcut


class TableView(QTableWidget):
    def __init__(self):
        super().__init__()
        self.modified_cells = set()
        self.setup_table()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.selectionModel().selectionChanged.connect(self.highlight_selection)
        self.undo_stack = []

        self.original_values = {} # Dictionary to track original values

        # Connect to itemChanged, itemDoubleClicked and currentCellChanged for tracking changes
        self.itemDoubleClicked.connect(self.store_original_value)
        self.currentCellChanged.connect(self.on_current_cell_changed)  #
        self.itemChanged.connect(self.on_item_changed)

        # Setup keyboard shortcuts globally for the TableView
        QShortcut(QKeySequence.Cut, self, activated=self.do_cut)
        QShortcut(QKeySequence.Copy, self, activated=self.do_copy)
        QShortcut(QKeySequence.Paste, self, activated=self.do_paste)
        QShortcut(QKeySequence.Undo, self, activated=self.do_undo)

    def setup_table(self):
        # Define columns, including separate columns for Bonus and Wage details
        total_columns = 21
        self.setColumnCount(total_columns)
        headers = [
            "Rule ID",  # 0
            "Rule Name",  # 1
            "Trigger Version",  # 2
            "Adjustment Type",  # 3
            "Version Number",  # 4
            "Match Anywhere",  # 5
            "Job or Location",  # 6
            "Effective Date",  # 7
            "Labor Category Entries",  # 8
            "Trigger Pay Codes",  # 9
            # Bonus Details
            "Bonus Rate Amount",  # 10
            "Bonus Rate Hourly Rate",  # 11
            "Once Per Day",  # 12
            "Time Period",  # 13
            "Job Code Type",  # 14
            "Week Start",  # 15
            # Wage Details
            "Amount",  # 16
            "Override If Primary Job Switch",  # 17
            "Type",  # 18
            "Use Highest Wage Switch",  # 19
            "Bonus Pay Code"  # 20
        ]

        # Verify the correct number of headers
        assert len(headers) == total_columns, f"Expected {total_columns} headers, got {len(headers)}"

        self.setHorizontalHeaderLabels(headers)

        header = self.horizontalHeader()
        for col in range(self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        for col in range(self.columnCount()):
            width = header.sectionSize(col)
            self.setColumnWidth(col, width + 20)

        self.setAlternatingRowColors(True)  # Improve readability
        self.setSortingEnabled(True)  # Allow sorting

        header.setVisible(True)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setDefaultSectionSize(200)
        self.setWordWrap(True)

    def context_menu(self, position):
        """Open the context menu when right-clicking on the table"""

        context_menu = QMenu()
        cut_action = QAction("Cut",self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.do_cut)
        context_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.do_copy)
        context_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.do_paste)
        context_menu.addAction(paste_action)

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.do_undo)
        context_menu.addAction(undo_action)

        context_menu.exec_(self.viewport().mapToGlobal(position))

    def do_cut(self):
        """Cut selected cells"""
        self.do_copy()
        # Clear the selected cells and record changes in the undo stack
        selected_items = self.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            if item:
                row, col = item.row(), item.column()
                old_value = item.text()
                self.undo_stack.append((row, col, old_value, "")) # Add the action to the undo stack
                item.setText("") # Clear the content of the cell
                self.modified_cells.add((row, col)) # Add the cell to modified cells set for tracking purposes
                item.setBackground(QColor("#e06666")) # Change the background color to indicate a change

    def do_copy(self):
        """Copy selected cells to clipboard"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        # Assuming the user wants to copy a rectangular area
        text_to_copy = ""
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                text_to_copy += "\t".join(row_data) + "\n"

        self.clipboard.setText(text_to_copy.strip())

    def do_paste(self):
        """Paste clipboard content to selected cells"""
        data = self.clipboard.text().strip().split('\n')
        if not data:
            return

        # Handle single cell selection to paste into multiple cells
        selected_items = self.selectedItems()
        if len(selected_items) > 1:
            # Pasting the same value into multiple selected cells
            value_to_paste = data[0].split('\t')[0]  # Get the first value from clipboard data
            for item in selected_items:
                if item:
                    row, col = item.row(), item.column()
                    old_value = item.text()
                    self.undo_stack.append((row, col, old_value, value_to_paste))
                    item.setText(value_to_paste)
                    self.modified_cells.add((row, col))
                    item.setBackground(QColor("#FFFF99"))
        else:
            # Pasting into cells from the starting position
            start_row = self.currentRow()
            start_col = self.currentColumn()

            for r_offset, line in enumerate(data):
                cells = line.split('\t')
                for c_offset, cell in enumerate(cells):
                    row = start_row + r_offset
                    col = start_col + c_offset
                    if row < self.rowCount() and col < self.columnCount():
                        item = self.item(row, col)
                        if not item:
                            item = QTableWidgetItem()
                            self.setItem(row, col, item)

                        old_value = item.text()
                        self.undo_stack.append((row, col, old_value, cell))
                        item.setText(cell)
                        self.modified_cells.add((row, col))
                        item.setBackground(QColor("#FFFF99"))

    def before_edit(self, item):
        self.current_edit = (item.row(), item.column(), item.text())
        #print(f"Before edit: {self.current_edit}")  # Debug print

    def after_edit(self,item):
        if self.signalsBlocked():
            return
        row = item.row()
        col = item.column()
        new_value = item.text()

        if self.current_edit and self.current_edit[0] == row and self.current_edit[1] == col:
            old_value = self.current_edit[2]
        else:
            old_value = new_value

        if old_value != new_value:
            #print(f"Recording change: ({row}, {col}) from '{old_value}' to '{new_value}'")  # Debug print
            self.undo_stack.append((row, col, old_value, new_value))
            self.modified_cells.add((row,col))
            item.setBackground(QColor("#FFFF99"))

        self.current_edit = None

    def do_undo(self):
        """Undo the last change"""
        #print("\nAttempting undo operation...")
        #print(f"Current undo stack size: {len(self.undo_stack)}")
        #print(f"Modified cells count: {len(self.modified_cells)}")

        if not self.undo_stack:
            print("No changes to undo")
            return

        # Get the last change
        row, col, old_value, new_value = self.undo_stack.pop()
        key = (row, col)
        #print(f"Undoing change at ({row}, {col})")
        #print(f"Reverting from '{new_value}' to '{old_value}'")

        self.blockSignals(True)

        item = self.item(row, col)
        if item:
            item.setText(old_value)

            # Check if this was the last change for this cell
            has_more_changes = any((r == row and c == col) for r, c, _, _ in self.undo_stack)

            if not has_more_changes:
                # Restore original background color
                adjustment_type = self.item(row, 3).text()
                color = (
                    QColor("#e0f7fa") if adjustment_type == "Bonus"
                    else QColor("#ffe0b2") if adjustment_type == "Wage"
                    else QColor("#f0f0f0")
                )
                item.setBackground(color)
                self.modified_cells.discard(key)  # Use the key tuple consistently
                #print(f"Restored original color for cell ({row}, {col})")
            else:
                item.setBackground(QColor("#FFFF99"))
                #print(f"Kept highlight color for cell ({row}, {col}) - has more changes")

        self.blockSignals(False)
        #print("Undo operation completed")
        #print(f"Modified cells remaining: {len(self.modified_cells)}")

    def highlight_selection(self, selected, deselected):
        """Highlight cells when selection changes"""
        for index in selected.indexes():
            self.modified_cells.add((index.row(), index.column()))
            self.item(index.row(), index.column()).setBackground(QColor("#FFFF99"))

    def __parse_boolean(self, value):
        """Helper method to parse boolean values"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == 'true'
        return False

    def resizeEvent(self, event):
        """Override resize event to adjust columns when window is resized"""
        super().resizeEvent(event)
        self.adjust_columns_to_contents()

    def adjust_columns_to_contents(self):
        """Adjust column widths to fit contents while maintaining minimum widths"""
        header = self.horizontalHeader()
        available_width = self.viewport().width()
        total_width = sum([self.columnWidth(col) for col in range(self.columnCount())])

        if total_width < available_width:
            # Distribute extra space proportionally
            extra_width = available_width - total_width
            extra_per_column = extra_width / self.columnCount()

            for col in range(self.columnCount()):
                current_width = self.columnWidth(col)
                new_width = current_width + extra_per_column
                self.setColumnWidth(col, new_width)

    @staticmethod
    def format_dict(data_dict):
        """
        Formats a dictionary into a readable string.
        """
        if not data_dict:
            return "N/A"
        if 'qualifier' in data_dict:
            return data_dict['qualifier']
        return "N/A"
        # return ", ".join([f"{k}: {v}" for k, v in data_dict.items()])

    def format_pay_codes(self, pay_codes):
        """
        Formats pay codes list into a readable string without duplication.
        """
        if not pay_codes:
            return ""
        return ", ".join([pc.get('name', '') for pc in pay_codes])

    def display_triggers(self, triggers):
        """
        Populates the table with the list of triggers.
        """
        self.setRowCount(len(triggers))

        for row, trigger in enumerate(triggers):
            # Initialize all cells in the row first

            # Rule ID (column 0)
            rule_id = trigger.get('ruleId', 'N/A')
            self.setItem(row, 0, QTableWidgetItem(str(rule_id)))

            # Rule Name (column 1)
            rule_name = trigger.get('ruleName', 'Unknown Rule')
            self.setItem(row, 1, QTableWidgetItem(str(rule_name)))

            # Adjustment allocation information
            adjustment_allocation = trigger.get("adjustmentAllocation", {}).get("adjustmentAllocation", {})
            adjustment_type = adjustment_allocation.get("adjustmentType", "Unknown").strip()

            # Trigger Version
            version_id = trigger.get('versionId', '')
            version_num = trigger.get('versionNum', '')
            version_text = f"{version_num}" if version_num else ''
            self.setItem(row, 2, QTableWidgetItem(version_text))

            # Adjustment Type (Shifted to index 3)
            adjustment_type_item = QTableWidgetItem(adjustment_type)
            self.setItem(row, 3, adjustment_type_item)

            # Version Number (Shifted to index 4)
            self.setItem(row, 4, QTableWidgetItem(str(version_num) if version_num else ''))

            # Match Anywhere (Shifted to index 5)
            match_anywhere = self.__parse_boolean(trigger.get("matchAnywhere", False))
            self.setItem(row, 5, QTableWidgetItem(str(match_anywhere)))

            # Job or Location (Shifted to index 6)
            job_or_location = trigger.get("jobOrLocation", {})
            job_or_location_text = job_or_location.get('qualifier', '') if job_or_location else ''
            self.setItem(row, 6, QTableWidgetItem(job_or_location_text))

            # Effective Date (Shifted to index 7)
            effective_date = trigger.get("jobOrLocationEffectiveDate", '')
            self.setItem(row, 7, QTableWidgetItem(effective_date))

            # Labor Category Entries (Shifted to index 8)
            labor_category_entries = trigger.get("laborCategoryEntries", '')
            self.setItem(row, 8, QTableWidgetItem(str(labor_category_entries)))

            # Pay Codes (Shifted to index 9)
            pay_codes = trigger.get("payCodes", [])
            pay_codes_str = self.format_pay_codes(pay_codes)
            self.setItem(row, 9, QTableWidgetItem(pay_codes_str))

            adjustment_allocation = trigger.get("adjustmentAllocation", {}).get("adjustmentAllocation", {})
            adjustment_type = adjustment_allocation.get("adjustmentType", "Unknown").strip()

            bonus_pay_code_column = self.columnCount() - 1 # Always use the last column
            bonus_pay_code_column = self.columnCount() - 1

            if adjustment_type == "Bonus":
                # First try to get the bonus pay code from our extracted data
                bonus_pay_code = trigger.get('bonusPayCode', {})

                # Get the pay code name
                bonus_pay_code_name = bonus_pay_code.get('name', '')

                # Create the table item
                bonus_pay_code_item = QTableWidgetItem(bonus_pay_code_name)
                self.setItem(row, bonus_pay_code_column, bonus_pay_code_item)
            else:
                self.setItem(row, bonus_pay_code_column, QTableWidgetItem("N/A"))

            # Adjustment Allocation Details (starting from index 10)
            if adjustment_type == "Bonus":
                # Populate Bonus-specific columns (indices 10-15)
                self.setItem(row, 10, QTableWidgetItem(str(adjustment_allocation.get("bonusRateAmount", ''))))
                self.setItem(row, 11, QTableWidgetItem(str(adjustment_allocation.get("bonusRateHourlyRate", ''))))
                self.setItem(row, 12, QTableWidgetItem(str(adjustment_allocation.get("oncePerDay", False))))
                self.setItem(row, 13, QTableWidgetItem(str(adjustment_allocation.get("timePeriod", ''))))
                self.setItem(row, 14, QTableWidgetItem(str(adjustment_allocation.get("jobCodeType", ''))))
                self.setItem(row, 15, QTableWidgetItem(str(adjustment_allocation.get("weekStart", ''))))

                # Clear Wage-specific columns (indices 16-19)
                for col in range(16, 20):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            elif adjustment_type == "Wage":
                # Clear Bonus-specific columns (indices 10-15)
                for col in range(10, 16):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

                # Populate Wage-specific columns (indices 16-19)
                self.setItem(row, 16, QTableWidgetItem(str(adjustment_allocation.get("amount", ''))))
                self.setItem(row, 17,
                             QTableWidgetItem(str(adjustment_allocation.get("overrideIfPrimaryJobSwitch", False))))
                self.setItem(row, 18, QTableWidgetItem(str(adjustment_allocation.get("type", ''))))
                self.setItem(row, 19, QTableWidgetItem(str(adjustment_allocation.get("useHighestWageSwitch", False))))

            else:
                # Clear all specific columns for unknown types (indices 10-19)
                for col in range(10, 20):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            # Apply color coding after all items are created
            color = (
                QColor("#e0f7fa") if adjustment_type == "Bonus"
                else QColor("#ffe0b2") if adjustment_type == "Wage"
                else QColor("#f0f0f0")
            )

            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(color)

        # Adjust columns after all data is loaded
        self.adjust_columns_to_contents()

        # Set minimum widths for specific columns
        min_widths = {
            1: 250,  # Rule Name
            6: 200,  # Job or Location
            9: 200,  # Pay Codes
            17: 150,  # Override If Primary Job Switch
            19: 150,  # Use Highest Wage Switch
            20: 200  # Bonus Pay Code
        }

        for col, width in min_widths.items():
            if self.columnWidth(col) < width:
                self.setColumnWidth(col, width)

    def on_item_double_clicked(self, item):
        """Store the original value when editing starts"""
        self.original_value = item.text()

    def store_original_value(self, item):
        """Store the original value when editing starts"""
        key = (item.row(), item.column())
        self.original_values[key] = item.text()
        #print(f"Stored original value: {key} = {item.text()}")

    def on_item_changed(self, item):
        """Handle cell value changes"""
        if self.signalsBlocked():
            return

        row = item.row()
        col = item.column()
        key = (row, col)
        current_value = item.text()

        # Get the original value if we have it
        original_value = self.original_values.get(key)

        #print(f"Change detected - Row: {row}, Col: {col}")
        #print(f"Original value: {original_value}")
        #print(f"Current value: {current_value}")

        if original_value is not None and original_value != current_value:
            change_entry = (row, col, original_value, current_value)
            self.undo_stack.append(change_entry)
            self.modified_cells.add(key)
            item.setBackground(QColor("#FFFF99"))
            #print(f"Added to undo stack: {change_entry}")
            #print(f"Undo stack size now: {len(self.undo_stack)}")

            # Clear the stored original value
            del self.original_values[key]

    def on_current_cell_changed(self, current_row, current_col, previous_row, previous_col):
        """Store original value when cell selection changes"""
        if current_row >= 0 and current_col >= 0:  # Valid cell selected
            item = self.item(current_row, current_col)
            if item:
                key = (current_row, current_col)
                # Only store if we don't already have an original value for this cell
                if key not in self.original_values:
                    self.original_values[key] = item.text()
                    #print(f"Stored original value (from selection): {key} = {item.text()}")

    """def print_debug_info(self):
        print("\nDebug Information:")
        print(f"Undo stack size: {len(self.undo_stack)}")
        print(f"Modified cells: {len(self.modified_cells)}")
        print("Last 5 undo stack entries:")
        for entry in self.undo_stack[-5:]:
            print(entry)"""