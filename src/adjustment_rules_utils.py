# adjustment_rules_utils.py
import copy
import json
import logging



class AdjustmentRuleUpdater:
    """
    A utility class for managing adjustment rule updates and payload creation.
    This class handles the conversion of table data into properly structured API payloads
    for creating and updating adjustment rules.
    """
    json = json

    @staticmethod
    def __parse_boolean(value):
        """
        Converts various input formats to boolean values.

        Args:
            value: The input value to parse (can be bool, str, or other)

        Returns:
            bool: True if the value represents a truthy value, False otherwise
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == 'true'
        return False

    @staticmethod
    def __clean_value(value):
        """
        Sanitizes input values by removing empty or N/A values.

        Args:
            value: The input value to clean

        Returns:
            The cleaned value or None if the value is empty or N/A
        """
        if not value or (isinstance(value, str) and value.lower() == 'n/a'):
            return None
        return value

    def _get_valid_effective_date(rule_data, original_trigger):
        """
        Gets a valid effective date, with proper fallback handling.

        Args:
            rule_data (dict): The modified rule data
            original_trigger (dict): The original trigger data

        Returns:
            str: A valid effective date string in YYYY-MM-DD format
        """
        effective_date = rule_data.get('Effective Date')

        if not effective_date and original_trigger:
            original_version = original_trigger.get('ruleVersions', {}).get('adjustmentRuleVersion', [{}])[0]
            effective_date = original_version.get('effectiveDate')

        if not effective_date:
            effective_date = "1753-01-01"

        return effective_date

    @staticmethod
    def _get_valid_version_number(rule_data, original_trigger):
        """
        Gets a valid version number for the trigger, with proper fallback handling.

        Args:
            rule_data (dict): The modified rule data
            original_trigger (dict): The original trigger data

        Returns:
            str: A valid version number, defaulting to "1" if none found
        """
        version_num = rule_data.get('Version Number')

        if not version_num and original_trigger:
            original_version = original_trigger.get('ruleVersions', {}).get('adjustmentRuleVersion', [{}])[0]
            original_triggers = original_version.get('triggers', {}).get('adjustmentTriggerForRule', [{}])
            if original_triggers:
                version_num = original_triggers[0].get('versionNum')
        if not version_num:
            version_num = "1"

        return str(version_num)  # Always return a string value

    @staticmethod
    def parse_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def parse_boolean(value, default=False):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == 'true'
        return default

    @classmethod
    def create_update_payload(cls, table_data, original_trigger=None):
        """Creates the update payload while preserving all unmodified triggers."""
        """Creates the update payload while preserving all unmodified triggers."""
        logging.info("\n=== Creating Update Payload ===")
        logging.info("Input Table Data:")
        #logging.debug(json.dumps(table_data, indent=2))
        logging.info("\nOriginal Trigger Data:")
        #logging.debug(  json.dumps(original_trigger, indent=2))

        if not isinstance(table_data, list) or not table_data:
            raise ValueError("Table data must be a list")

        if not original_trigger:
            raise ValueError("Original trigger data is required for updates")

        rule_data = table_data[0]
        required_fields = ['Rule ID', 'Version Number', 'Adjustment Type']
        missing_fields = [field for field in required_fields if field not in rule_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        if not original_trigger:
            raise ValueError("Original trigger data is required for updates")

        logging.info("\nValidating modification data:")
        logging.info(f"Version Number (expected number): {rule_data.get('Version Number')}")
        logging.info(f"Amount (expected number): {rule_data.get('Amount')}")
        logging.info(f"Adjustment Type (expected string): {rule_data.get('Adjustment Type')}")

        version_num = str(rule_data.get('Version Number'))
        if not version_num.isdigit():
            raise ValueError(f"Invalid version number format: {version_num}")

        # Get the original version and trigger data
        try:
            original_version = original_trigger['ruleVersions']['adjustmentRuleVersion'][0]
            original_triggers = original_version['triggers']['adjustmentTriggerForRule']
            if not isinstance(original_triggers, list):
                original_triggers = [original_triggers]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid original trigger structure: {e}")

        # Deep copy the original version to preserve it
        updated_version = copy.deepcopy(original_version)

        # Find the trigger that matches the modification
        modified_version_num = rule_data.get('Version Number')

        # Convert triggers to list if it's not already
        if not isinstance(updated_version['triggers']['adjustmentTriggerForRule'], list):
            updated_version['triggers']['adjustmentTriggerForRule'] = [
                updated_version['triggers']['adjustmentTriggerForRule']]

        # Find and update only the matching trigger
        triggers_list = updated_version['triggers']['adjustmentTriggerForRule']
        for i, trigger in enumerate(triggers_list):
            if str(trigger.get('versionNum')) == str(modified_version_num):
                # Update the specific trigger while preserving the full structure
                updated_trigger = copy.deepcopy(trigger)

                # Update the adjustment allocation
                adjustment_type = rule_data.get('Adjustment Type')
                if 'adjustmentAllocation' not in updated_trigger:
                    updated_trigger['adjustmentAllocation'] = {'adjustmentAllocation': {}}

                allocation = updated_trigger['adjustmentAllocation']['adjustmentAllocation']
                allocation['adjustmentType'] = adjustment_type

                # Update fields based on adjustment type
                if adjustment_type == "Bonus":
                    allocation.update({
                        'bonusRateAmount': float(rule_data.get('Bonus Rate Amount', 0)),
                        'oncePerDay': AdjustmentRuleUpdater.parse_boolean(rule_data.get('Once Per Day')),
                        'timePeriod': rule_data.get('Time Period', 'Shift'),
                        'jobCodeType': rule_data.get('Job Code Type', 'Worked')
                    })
                else:  # Wage type
                    allocation.update({
                        'amount': float(rule_data.get('Amount', 0)),
                        'type': rule_data.get('Type', 'FlatRate'),
                        'overrideIfPrimaryJobSwitch': AdjustmentRuleUpdater.parse_boolean(
                            rule_data.get('Override If Primary Job Switch')),
                        'useHighestWageSwitch': AdjustmentRuleUpdater.parse_boolean(
                            rule_data.get('Use Highest Wage Switch'))
                    })

                # Replace the trigger in the list with the updated version
                triggers_list[i] = updated_trigger
                break

        # Construct the payload with all triggers
        payload = {
            "id": int(rule_data.get('Rule ID', original_trigger.get('id', 0))),
            "name": rule_data.get('Rule Name', original_trigger.get('name', '')),
            "ruleVersions": {
                "adjustmentRuleVersion": [updated_version]
            }
        }

        logging.info("\n=== Final Update Payload ===")
        #logging.debug(json.dumps(payload, indent=2))

        return payload

    @staticmethod
    def create_export_payload(table_data, separate_rules=False):
        """
        Creates the update payload from table data
        Args:
            table_data: List of rule data from table
            separate_rules: If True, returns dict of rules by ID. If False, returns single rule with all versions
        """

        def safe_float_convert(value, default=0.0):
            """Safely convert a value to float, returning default if conversion fails"""
            if not value or value.lower() == 'n/a':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

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
                    "bonusRateAmount": safe_float_convert(rule_data.get('Bonus Rate Amount')),
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
                    "amount": safe_float_convert(rule_data.get('Amount')),
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

    @staticmethod
    def _create_adjustment_allocation(rule_data):
        """
        Creates the adjustment allocation based on the adjustment type.
        Handles both Bonus and Wage type allocations with their specific fields.

        Args:
            rule_data (dict): Dictionary containing the rule data

        Returns:
            dict: A properly formatted adjustment allocation object
        """
        adjustment_type = rule_data.get('Adjustment Type')
        if not adjustment_type:
            return {}

        # Initialize base allocation with type
        allocation = {
            "adjustmentType": adjustment_type
        }

        # Handle Bonus type adjustments
        if adjustment_type == "Bonus":
            bonus_fields = {
                "bonusRateAmount": AdjustmentRuleUpdater.__clean_value(rule_data.get('Bonus Rate Amount')),
                "jobCodeType": rule_data.get('Job Code Type', 'Worked'),
                "timePeriod": rule_data.get('Time Period', 'Shift'),
                "oncePerDay": AdjustmentRuleUpdater.__parse_boolean(rule_data.get('Once Per Day', 'false'))
            }
            # Only add non-None values to the allocation
            allocation.update({k: v for k, v in bonus_fields.items() if v is not None})

        # Handle Wage type adjustments
        elif adjustment_type == "Wage":
            # Convert amount to float and handle potential conversion errors
            amount = rule_data.get('Amount', '0')
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                amount = 0.0

            wage_fields = {
                "amount": amount,
                "type": rule_data.get('Type', 'FlatRate'),
                "overrideIfPrimaryJobSwitch": AdjustmentRuleUpdater.__parse_boolean(
                    rule_data.get('Override If Primary Job Switch', 'false')),
                "useHighestWageSwitch": AdjustmentRuleUpdater.__parse_boolean(
                    rule_data.get('Use Highest Wage Switch', 'false'))
            }
            # Only add non-None values to the allocation
            allocation.update({k: v for k, v in wage_fields.items() if v is not None})

        return allocation

