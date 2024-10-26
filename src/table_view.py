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
            "Trigger Version", "Adjustment Type", "Version Number",
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
            adjustment_allocation = trigger.get("adjustmentAllocation", {}).get("adjustmentAllocation", {})
            adjustment_type = adjustment_allocation.get("adjustmentType", "Unknown").strip()

            self.adjust_columns_to_contents()
            min_widths = {
                4: 200,  # Job or Location
                7: 200,  # Pay Codes
                15: 150,  # Override If Primary Job Switch
                17: 150  # Use Highest Wage Switch
            }
            for col, width in min_widths.items():
                if self.columnWidth(col) < width:
                    self.setColumnWidth(col, width)

            # Populate table cells
            # Trigger Version
            trigger_version = f"Version {trigger.get('versionNum', 'N/A')}"
            self.setItem(row, 0, QTableWidgetItem(trigger_version))

            # Adjustment Type
            adjustment_type_item = QTableWidgetItem(adjustment_type)
            self.setItem(row, 1, adjustment_type_item)

            # Version Number
            version_num = str(trigger.get("versionNum", "N/A"))
            self.setItem(row, 2, QTableWidgetItem(version_num))

            # Match Anywhere
            match_anywhere = str(trigger.get("matchAnywhere", False))
            self.setItem(row, 3, QTableWidgetItem(match_anywhere))

            # Job or Location
            job_or_location = self.format_dict(trigger.get("jobOrLocation", {}))
            self.setItem(row, 4, QTableWidgetItem(job_or_location))

            # Effective Date
            effective_date = trigger.get("jobOrLocationEffectiveDate", "N/A")
            self.setItem(row, 5, QTableWidgetItem(effective_date))

            # Labor Category Entries
            labor_category_entries = trigger.get("laborCategoryEntries", "N/A")
            self.setItem(row, 6, QTableWidgetItem(labor_category_entries))

            # Pay Codes
            pay_codes = trigger.get("payCodes", [])
            pay_codes_str = self.format_pay_codes(pay_codes)
            self.setItem(row, 7, QTableWidgetItem(pay_codes_str))

            # Adjustment Allocation Details
            if adjustment_type == "Bonus":
                # Populate Bonus-specific columns
                self.setItem(row, 8, QTableWidgetItem(adjustment_allocation.get("bonusRateAmount", "N/A")))
                self.setItem(row, 9, QTableWidgetItem(str(adjustment_allocation.get("bonusRateHourlyRate", "N/A"))))
                self.setItem(row, 10, QTableWidgetItem(str(adjustment_allocation.get("oncePerDay", False))))
                self.setItem(row, 11, QTableWidgetItem(adjustment_allocation.get("timePeriod", "N/A")))
                self.setItem(row, 12, QTableWidgetItem(adjustment_allocation.get("jobCodeType", "N/A")))
                self.setItem(row, 13, QTableWidgetItem(adjustment_allocation.get("weekStart", "N/A")))

                # Wage-specific columns remain empty
                self.setItem(row, 14, QTableWidgetItem("N/A"))
                self.setItem(row, 15, QTableWidgetItem("N/A"))
                self.setItem(row, 16, QTableWidgetItem("N/A"))
                self.setItem(row, 17, QTableWidgetItem("N/A"))

            elif adjustment_type == "Wage":
                # Populate Wage-specific columns
                self.setItem(row, 8, QTableWidgetItem("N/A"))
                self.setItem(row, 9, QTableWidgetItem("N/A"))
                self.setItem(row, 10, QTableWidgetItem("N/A"))
                self.setItem(row, 11, QTableWidgetItem("N/A"))
                self.setItem(row, 12, QTableWidgetItem("N/A"))
                self.setItem(row, 13, QTableWidgetItem("N/A"))

                self.setItem(row, 14, QTableWidgetItem(str(adjustment_allocation.get("amount", "N/A"))))
                self.setItem(row, 15,
                             QTableWidgetItem(str(adjustment_allocation.get("overrideIfPrimaryJobSwitch", False))))
                self.setItem(row, 16, QTableWidgetItem(adjustment_allocation.get("type", "N/A")))
                self.setItem(row, 17, QTableWidgetItem(str(adjustment_allocation.get("useHighestWageSwitch", False))))

            else:
                # For unknown types, leave all specific columns as "N/A" or populate if needed
                for col in range(8, 18):
                    self.setItem(row, col, QTableWidgetItem("N/A"))

            # Color-Coding based on Adjustment Type
            if adjustment_type == "Bonus":
                for col in range(self.columnCount()):
                    self.item(row, col).setBackground(QColor("#e0f7fa"))  # Light Cyan for Bonus
            elif adjustment_type == "Wage":
                for col in range(self.columnCount()):
                    self.item(row, col).setBackground(QColor("#ffe0b2"))  # Light Orange for Wage
            else:
                for col in range(self.columnCount()):
                    self.item(row, col).setBackground(QColor("#f0f0f0"))  # Default Gray
