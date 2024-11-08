class AdjustmentRuleUpdater:
    @staticmethod
    def __parse_boolean(value):
        """Helper method to parse boolean values"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == 'true'
        return False

    @staticmethod
    def __clean_value(value):
        """Clean value by removing N/A and empty strings"""
        if not value or value.lower() == 'n/a':
            return None
        return value

    @staticmethod
    def create_update_payload(table_data, separate_rules=False):
        """
        Creates the update payload from table data
        Args:
            table_data: List of rule data from table
            separate_rules: If True, returns dict of rules by ID. If False, returns single rule with all versions
        """
        if not isinstance(table_data, list):
            raise ValueError("Table data must be a list")

        rules_by_id = {}
        for rule_data in table_data:
            rule_id = rule_data.get('Rule ID')
            if not rule_id:
                continue

            # Initialize rule structure if not exists
            if rule_id not in rules_by_id:
                rules_by_id[rule_id] = {
                    "id": rule_id,
                    "name": rule_data.get('Rule Name', ''),
                    "uniqueKey": "AdjustmentRule",
                    "itemsRetrieveResponses": [{
                        "itemDataInfo": {
                            "title": rule_data.get('Rule Name', ''),
                            "key": rule_data.get('Rule Name', '').replace(' ', '%20'),
                            "env": None,
                            "urlparams": f"key={rule_data.get('Rule Name', '').replace(' ', '%20')}&name={rule_data.get('Rule Name', '')}"
                        },
                        "responseObjectNode": {
                            "id": rule_id,
                            "name": rule_data.get('Rule Name', ''),
                            "ruleVersions": {
                                "adjustmentRuleVersion": []
                            }
                        }
                    }]
                }

            version_entry = {
                "versionId": str(rule_data.get('Version Number', '1')),
                "description": "",
                "expirationDate": "3000-01-01",
                "effectiveDate": rule_data.get('Effective Date', '2024-11-03'),
                "triggers": {
                    "adjustmentTriggerForRule": [{
                        "adjustmentAllocation": {
                            "adjustmentAllocation": {}
                        },
                        "jobOrLocation": {},
                        "jobOrLocationEffectiveDate": rule_data.get('Effective Date', '2024-11-03'),
                        "laborCategoryEntries": rule_data.get('Labor Category Entries', ''),
                        "matchAnywhere": AdjustmentRuleUpdater.__parse_boolean(rule_data.get('Match Anywhere', False)),
                        "versionNum": str(rule_data.get('Version Number', '1'))
                    }]
                }
            }

            adjustment_allocation = version_entry["triggers"]["adjustmentTriggerForRule"][0]["adjustmentAllocation"][
                "adjustmentAllocation"]

            # Handle adjustment type-specific fields
            if rule_data.get('Adjustment Type') == 'Bonus':
                adjustment_allocation.update({
                    "adjustmentType": "Bonus",
                    "bonusRateAmount": rule_data.get('Bonus Rate Amount', '1.00'),
                    "jobCodeType": rule_data.get('Job Code Type', 'Worked'),
                    "timePeriod": rule_data.get('Time Period', 'Shift'),
                    "oncePerDay": AdjustmentRuleUpdater.__parse_boolean(rule_data.get('Once Per Day', True))
                })

                bonus_pay_code = rule_data.get('Bonus Pay Code')
                if bonus_pay_code:
                    adjustment_allocation["payCode"] = {
                        "qualifier": bonus_pay_code,
                        "name": bonus_pay_code
                    }
            else:  # Wage type
                adjustment_allocation.update({
                    "adjustmentType": "Wage",
                    "amount": float(rule_data.get('Amount', 0)),
                    "type": rule_data.get('Type', 'FlatRate'),
                    "overrideIfPrimaryJobSwitch": AdjustmentRuleUpdater.__parse_boolean(
                        rule_data.get('Override If Primary Job Switch', False)
                    ),
                    "useHighestWageSwitch": AdjustmentRuleUpdater.__parse_boolean(
                        rule_data.get('Use Highest Wage Switch', False)
                    )
                })

            # Add pay codes if they exist
            pay_codes_str = rule_data.get('Trigger Pay Codes', '')
            if pay_codes_str and pay_codes_str.lower() != 'n/a':
                pay_codes = []
                for pc in pay_codes_str.split(','):
                    pc = pc.strip()
                    if pc:
                        pay_codes.append({
                            "qualifier": pc,
                            "name": pc
                        })
                if pay_codes:
                    version_entry["triggers"]["adjustmentTriggerForRule"][0]["payCodes"] = pay_codes

            # Add version to rule
            rules_by_id[rule_id]["itemsRetrieveResponses"][0]["responseObjectNode"][
                "ruleVersions"]["adjustmentRuleVersion"].append(version_entry)

        if separate_rules:
            # Return dictionary of rules for file export
            return rules_by_id
        else:
            # Return first rule containing all versions for API
            first_rule_id = next(iter(rules_by_id))
            return rules_by_id[first_rule_id]