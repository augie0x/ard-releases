# table_view.py
import json

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QKeySequence, QTextOption
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAction, QApplication, QShortcut, \
    QStyledItemDelegate, QStyle
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log', mode='w')])


class WrapDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        text = index.data(Qt.DisplayRole) or ""

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        available_width = option.rect.width()
        metrics = option.fontMetrics

        truncated = metrics.elidedText(text, Qt.ElideRight, available_width)
        if truncated != text:
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WordWrap)
            painter.setPen(option.palette.text().color())
            painter.drawText(QRectF(option.rect), text, text_option)
        else:
            painter.setPen(option.palette.text().color())
            painter.drawText(option.rect, Qt.AlignVCenter | Qt.AlignLeft, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole) or ""
        metrics = option.fontMetrics

        available_width = option.rect.width() if option.rect.width() > 0 else 350
        rect = metrics.boundingRect(0,0, available_width, 10000, Qt.TextWordWrap, text)
        return rect.size()

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
        self.current_rules_data = None

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
        total_columns = 22
        self.setColumnCount(total_columns)
        headers = [
            "Rule ID",  # 0
            "Rule Name",  # 1
            "Version Number",  # 2
            "Effective Date",  # 3
            "Adjustment Type",  # 4
            "Match Anywhere",  # 5
            "Job or Location",  # 6
            "Labor Category Entries",  # 7
            "Trigger Pay Codes",  # 8
            # Bonus Details
            "Bonus Rate Amount",  # 9
            "Bonus Hourly Rate",  # 10 - New
            "Max Amount",  # 11 - New
            "Min Time",  # 12 - New
            "Once Per Day",  # 13
            "Time Period",  # 14
            "Job Code Type",  # 15
            "Week Start",  # 16
            "Bonus Pay Code",  # 17
            # Wage Details
            "Amount",  # 18
            "Type",  # 19
            "Override If Primary Job Switch",  # 20
            "Use Highest Wage Switch",  # 21
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

        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        header.setVisible(True)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionsMovable(False)
        header.setSectionsClickable(True)
        header.setDefaultSectionSize(150)
        self.setWordWrap(True)

        wrap_delegate = WrapDelegate(self)
        self.setItemDelegateForColumn(8,wrap_delegate)

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
                self.undo_stack.append((row, col, old_value, ""))
                item.setText("") # Clear the content of the cell
                self.modified_cells.add((row, col))
                item.setBackground(QColor("#e06666"))

    def do_copy(self):
        """Copy selected cells to clipboard"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

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
            self.undo_stack.append((row, col, old_value, new_value))
            self.modified_cells.add((row,col))
            item.setBackground(QColor("#FFFF99"))

        self.current_edit = None

    def do_undo(self):
        """Undo the last change"""

        if not self.undo_stack:
            return

        # Get the last change
        row, col, old_value, new_value = self.undo_stack.pop()
        key = (row, col)

        self.blockSignals(True)

        try:
            item = self.item(row, col)
            if item:
                current_value = item.text()
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
                else:
                    item.setBackground(QColor("#FFFF99"))
        finally:
            self.blockSignals(False)

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

    def format_pay_codes(self, pay_codes):
        """
        Formats pay codes list into a readable string without duplication.
        """
        if not pay_codes:
            return ""
        return ", ".join([pc.get('name', '') for pc in pay_codes])

    def format_time_value(self, value):
        """Formats numeric values to HH:MM format"""
        if isinstance(value, (int, float)):
            hours = int(value)
            minutes = int((value - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        return str(value)

    def display_triggers(self, triggers):
        """
        Populates the table with the list of triggers.
        """
        self.setRowCount(len(triggers))
        self.current_rules_data = triggers

        for row, trigger in enumerate(triggers):
            # Get adjustment allocation info upfront
            adjustment_allocation = trigger.get("adjustmentAllocation", {}).get("adjustmentAllocation", {})
            adjustment_type = adjustment_allocation.get("adjustmentType", "Unknown").strip()

            # Basic fields
            self.setItem(row, 0, QTableWidgetItem(str(trigger.get('ruleId', 'N/A'))))  # Rule ID
            self.setItem(row, 1, QTableWidgetItem(str(trigger.get('ruleName', 'Unknown Rule'))))  # Rule Name
            self.setItem(row, 2, QTableWidgetItem(str(trigger.get('versionNum', ''))))  # Version Number
            self.setItem(row, 3, QTableWidgetItem(str(trigger.get('effectiveDate', ''))))  # Effective Date
            self.setItem(row, 4, QTableWidgetItem(adjustment_type))  # Adjustment Type
            self.setItem(row, 5, QTableWidgetItem(
                str(self.__parse_boolean(trigger.get("matchAnywhere", False)))))  # Match Anywhere

            # Job/Location and Categories
            job_location = trigger.get("jobOrLocation", {})
            self.setItem(row, 6, QTableWidgetItem(job_location.get('qualifier', '')))  # Job or Location
            self.setItem(row, 7,
                         QTableWidgetItem(str(trigger.get("laborCategoryEntries", ''))))  # Labor Category Entries

            # Pay Codes
            pay_codes = trigger.get("payCodes", [])
            self.setItem(row, 8, QTableWidgetItem(self.format_pay_codes(pay_codes)))  # Trigger Pay Codes

            if adjustment_type == "Bonus":
                # Bonus Rate Amount formatting
                bonus_rate = adjustment_allocation.get("bonusRateAmount", '')
                self.setItem(row, 9, QTableWidgetItem(self.format_time_value(bonus_rate)))  # Bonus Rate Amount

                # Other Bonus fields
                self.setItem(row, 10, QTableWidgetItem(
                    str(adjustment_allocation.get("bonusRateHourlyRate", ''))))  # Bonus Hourly Rate
                self.setItem(row, 11, QTableWidgetItem(
                    str(adjustment_allocation.get("timeAmountMaximumAmount", ''))))  # Max Amount
                self.setItem(row, 12, QTableWidgetItem(
                    self.format_time_value(adjustment_allocation.get("timeAmountMinimumTime", ''))))  # Min Time
                self.setItem(row, 13,
                             QTableWidgetItem(str(adjustment_allocation.get("oncePerDay", False))))  # Once Per Day
                self.setItem(row, 14, QTableWidgetItem(str(adjustment_allocation.get("timePeriod", ''))))  # Time Period
                self.setItem(row, 15,
                             QTableWidgetItem(str(adjustment_allocation.get("jobCodeType", ''))))  # Job Code Type
                self.setItem(row, 16, QTableWidgetItem(str(adjustment_allocation.get("weekStart", ''))))  # Week Start

                # Bonus Pay Code
                bonus_pay_code = adjustment_allocation.get("payCode", {})
                self.setItem(row, 17, QTableWidgetItem(bonus_pay_code.get('name', '')))  # Bonus Pay Code

                # Clear Wage fields
                for col in range(18, 22):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            elif adjustment_type == "Wage":
                # Clear Bonus fields
                for col in range(9, 18):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

                # Wage fields
                self.setItem(row, 18, QTableWidgetItem(str(adjustment_allocation.get("amount", ''))))  # Amount
                self.setItem(row, 19, QTableWidgetItem(str(adjustment_allocation.get("type", ''))))  # Type
                self.setItem(row, 20, QTableWidgetItem(str(adjustment_allocation.get("overrideIfPrimaryJobSwitch",
                                                                                     False))))  # Override If Primary Job Switch
                self.setItem(row, 21, QTableWidgetItem(
                    str(adjustment_allocation.get("useHighestWageSwitch", False))))  # Use Highest Wage Switch

            else:
                # Clear all specific columns for unknown types
                for col in range(9, 22):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            # Apply color coding
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
            8: 200,  # Trigger Pay Codes
            17: 200,  # Bonus Pay Code
            20: 150,  # Override If Primary Job Switch
            21: 150  # Use Highest Wage Switch
        }

        for col, width in min_widths.items():
            if self.columnWidth(col) < width:
                self.setColumnWidth(col, width)

        self.resizeRowsToContents()

    def on_item_double_clicked(self, item):
        """Store the original value when editing starts"""
        self.original_value = item.text()

    def store_original_value(self, item):
        """Store the original value when editing starts"""
        key = (item.row(), item.column())
        self.original_values[key] = item.text()
        #logging.debug(f"Stored original value: {key} = {item.text()}")

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

        if original_value is not None and original_value != current_value:
            change_entry = (row, col, original_value, current_value)
            self.undo_stack.append(change_entry)
            self.modified_cells.add(key)
            item.setBackground(QColor("#FFFF99"))

            # Clear the stored original value
            self.original_values.pop(key, None)

    def on_current_cell_changed(self, current_row, current_col, previous_row, previous_col):
        """Store original value when cell selection changes"""
        if current_row >= 0 and current_col >= 0:  # Valid cell selected
            item = self.item(current_row, current_col)
            if item:
                key = (current_row, current_col)
                # Only store if there is no original value for this cell
                if key not in self.original_values:
                    self.original_values[key] = item.text()

    # In table_view.py, modify get_modified_row_data method

    def get_modified_row_data(self):
        """Gets modified row data from the table"""
        modified_data = []

        logging.info("\n=== Modified Cells ===")
        logging.info(f"Total modified cells: {len(self.modified_cells)}")

        for (row, col) in self.modified_cells:
            # Get the header for the modified column
            header_item = self.horizontalHeaderItem(col)
            if not header_item:
                logging.warning(f"Warning: No header found for column {col}")
                continue
            header = header_item.text()

            # Get Rule ID from first column
            rule_id_item = self.item(row, 0)
            if not rule_id_item:
                logging.warning(f"Warning: No Rule ID found for row {row}")
                continue
            rule_id = rule_id_item.text()

            # Get version number - it's in column 2 (0-based indexing)
            version_num_item = self.item(row, 2)
            if not version_num_item:
                logging.warning(f"Warning: No Version Number found for row {row}")
                continue
            version_num = version_num_item.text()

            # Get the modified value
            modified_item = self.item(row, col)
            if not modified_item:
                logging.warning(f"Warning: No item found at row {row}, col {col}")
                continue
            modified_value = modified_item.text()

            # Skip N/A values
            if modified_value.upper() == 'N/A':
                logging.info(f"Skipping N/A value for Rule {rule_id}, {header}")
                continue

            logging.debug(f"Processing modification - Rule: {rule_id}, Version: {version_num}, {header}: {modified_value}")

            # Create rule data with correct fields and version number
            rule_data = {'Rule ID': rule_id, 'Rule Name': self.item(row, 1).text(), 'Version Number': version_num,
                         'Effective Date': self.item(row, 3).text(), 'Adjustment Type': self.item(row, 4).text(),
                         header: modified_value}

            # Add the modified field

            logging.info("\n=== Rule Data Being Added ===")
            #logging.debug(json.dumps(rule_data, indent=2))

            modified_data.append(rule_data)

        return modified_data