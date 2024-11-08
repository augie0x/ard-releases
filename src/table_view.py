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
        self.modified_cells = set()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.selectionModel().selectionChanged.connect(self.highlight_selection)
        self.undo_stack = []

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

        # Print header count for verification
        print(f"Number of headers: {len(headers)}")

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

    def do_undo(self):
        """Undo the last change made"""
        if not self.undo_stack:
            return

        row, col, old_value, new_value = self.undo_stack.pop()

        self.blockSignals(True)  # Prevent triggering `record_change` while undoing
        item = self.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self.setItem(row, col, item)

        item.setText(old_value)
        self.blockSignals(False)

        self.modified_cells.add((row, col))
        item.setBackground(QColor("#FFFF99"))

    def record_change(self,row,col):
        current_value = self.item(row,col).text()

        if self.undo_stack and self.undo_stack[-1][0:2] == (row,col):
            _,_,old_value,_ = self.undo_stack.pop()
            self.undo_stack.append((row,col,old_value,current_value))

        else:
            old_value = current_value
            if self.item(row,col).text() != "":
                old_value = self.item(row,col).text()

            self.undo_stack.append((row, col, old_value, current_value))

            self.modified_cells.add((row,col))
            self.item(row,col).setBackground(QColor("#FFFF99"))

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

    def on_cell_changed(self, row, column):
        """Track modified cells"""
        self.modified_cells.add((row, column))
        item = self.item(row, column)
        if item:
            item.setBackground(QColor("#FFEB3B"))  # Highlight modified cells