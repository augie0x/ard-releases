# table_view.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


class TableView(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_table()

    def setup_table(self):
        # Define columns, including separate columns for Bonus and Wage details
        self.setColumnCount(18)
        headers = [
            "Rule Name", "Trigger Version", "Adjustment Type", "Version Number",
            "Match Anywhere", "Job or Location", "Effective Date",
            "Labor Category Entries", "Pay Codes",
            # Bonus Details
            "Bonus Rate Amount", "Bonus Rate Hourly Rate", "Once Per Day",
            "Time Period", "Job Code Type", "Week Start",
            # Wage Details
            "Amount", "Override If Primary Job Switch", "Type", "Use Highest Wage Switch",
            "Other Details"
        ]

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
            for col in range(self.columnCount()):
                if self.item(row, col) is None:
                    self.setItem(row, col, QTableWidgetItem(""))

            # Rule Name
            rule_name = trigger.get('ruleName')
            if not isinstance(rule_name, str):
                rule_name = 'Unknown Rule'

            rule_name_item = QTableWidgetItem(rule_name)
            self.setItem(row, 0, rule_name_item)

            # Adjustment allocation information
            adjustment_allocation = trigger.get("adjustmentAllocation", {}).get("adjustmentAllocation", {})
            adjustment_type = adjustment_allocation.get("adjustmentType", "Unknown").strip()

            # Trigger Version
            trigger_version = f"Version {trigger.get('versionNum', 'N/A')}"
            self.setItem(row, 1, QTableWidgetItem(trigger_version))

            # Adjustment Type
            adjustment_type_item = QTableWidgetItem(adjustment_type)
            self.setItem(row, 2, adjustment_type_item)

            # Version Number
            version_num = str(trigger.get("versionNum", "N/A"))
            self.setItem(row, 3, QTableWidgetItem(version_num))

            # Match Anywhere
            match_anywhere = str(trigger.get("matchAnywhere", False))
            self.setItem(row, 4, QTableWidgetItem(match_anywhere))

            # Job or Location
            job_or_location = self.format_dict(trigger.get("jobOrLocation", {}))
            self.setItem(row, 5, QTableWidgetItem(job_or_location))

            # Effective Date
            effective_date = trigger.get("jobOrLocationEffectiveDate", "N/A")
            self.setItem(row, 6, QTableWidgetItem(effective_date))

            # Labor Category Entries
            labor_category_entries = trigger.get("laborCategoryEntries", "N/A")
            self.setItem(row, 7, QTableWidgetItem(str(labor_category_entries)))

            # Pay Codes
            pay_codes = trigger.get("payCodes", [])
            pay_codes_str = self.format_pay_codes(pay_codes)
            self.setItem(row, 8, QTableWidgetItem(pay_codes_str))

            # Adjustment Allocation Details
            if adjustment_type == "Bonus":
                # Populate Bonus-specific columns
                self.setItem(row, 9, QTableWidgetItem(str(adjustment_allocation.get("bonusRateAmount", "N/A"))))
                self.setItem(row, 10, QTableWidgetItem(str(adjustment_allocation.get("bonusRateHourlyRate", "N/A"))))
                self.setItem(row, 11, QTableWidgetItem(str(adjustment_allocation.get("oncePerDay", False))))
                self.setItem(row, 12, QTableWidgetItem(str(adjustment_allocation.get("timePeriod", "N/A"))))
                self.setItem(row, 13, QTableWidgetItem(str(adjustment_allocation.get("jobCodeType", "N/A"))))
                self.setItem(row, 14, QTableWidgetItem(str(adjustment_allocation.get("weekStart", "N/A"))))

                # Clear Wage-specific columns
                for col in range(15, 19):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            elif adjustment_type == "Wage":
                # Clear Bonus-specific columns
                for col in range(9, 15):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

                # Populate Wage-specific columns
                self.setItem(row, 15, QTableWidgetItem(str(adjustment_allocation.get("amount", "N/A"))))
                self.setItem(row, 16,
                             QTableWidgetItem(str(adjustment_allocation.get("overrideIfPrimaryJobSwitch", False))))
                self.setItem(row, 17, QTableWidgetItem(str(adjustment_allocation.get("type", "N/A"))))
                self.setItem(row, 18, QTableWidgetItem(str(adjustment_allocation.get("useHighestWageSwitch", False))))
            else:
                # Clear all specific columns for unknown types
                for col in range(9, 19):
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
            0: 250,  # Rule Name
            5: 200,  # Job or Location
            8: 200,  # Pay Codes
            16: 150,  # Override If Primary Job Switch
            18: 150  # Use Highest Wage Switch
        }

        for col, width in min_widths.items():
            if self.columnWidth(col) < width:
                self.setColumnWidth(col, width)

