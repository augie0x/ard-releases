# data_loader.py
class DataLoader:
    @staticmethod
    def load_json(file_path):
        """
        Loads a JSON file and returns the parsed data.
        """
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            # print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            # print(f"Error loading JSON file: {e}")
            return None

    @staticmethod
    def __parse_boolean(value):
        """Helper method to parse boolean values"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == 'true'
        return False

    @staticmethod
    def extract_triggers(data):
        """
        Extracts triggers from the given data.
        Handles both API responses and manual JSON file structures.
        """
        triggers = []
        processed_rules = 0

        if not data:
            return triggers

        try:
            def process_single_rule(rule, source_type="api"):
                """Helper function to process a single rule consistently"""
                rule_id = str(rule.get('id', ''))
                rule_name = rule.get('name', '')

                local_triggers = []

                if 'ruleVersions' in rule and isinstance(rule['ruleVersions'], dict):
                    versions = rule['ruleVersions'].get('adjustmentRuleVersion', [])
                    if not isinstance(versions, list):
                        versions = [versions]

                    for version in versions:
                        version_id = version.get('versionId', '')

                        if 'triggers' in version and 'adjustmentTriggerForRule' in version['triggers']:
                            version_triggers = version['triggers']['adjustmentTriggerForRule']
                            if not isinstance(version_triggers, list):
                                version_triggers = [version_triggers]

                            for trigger in version_triggers:
                                # Create a new trigger dictionary with rule information
                                new_trigger = {
                                    'ruleId': rule_id,
                                    'ruleName': rule_name,
                                    'versionId': version_id,  # Add version ID
                                    'versionNum': trigger.get('versionNum', '1'),  # Add trigger version number
                                    'effectiveDate': version.get('effectiveDate', ''),
                                    'expirationDate': version.get('expirationDate', ''),
                                    'description': version.get('description', '')
                                }

                                # Add adjustment allocation if present
                                if 'adjustmentAllocation' in trigger:
                                    adjustment_alloc = trigger['adjustmentAllocation'].get('adjustmentAllocation', {})
                                    new_trigger['adjustmentAllocation'] = trigger['adjustmentAllocation']

                                    # Extract bonus pay code separately if it exists
                                    if adjustment_alloc.get('adjustmentType') == 'Bonus':
                                        bonus_pay_code = adjustment_alloc.get('payCode')
                                        new_trigger['bonusPayCode'] = bonus_pay_code

                                # Add other trigger fields
                                fields_to_copy = [
                                    'jobOrLocation', 'jobOrLocationEffectiveDate',
                                    'laborCategoryEntries', 'payCodes', 'matchAnywhere'
                                ]
                                for field in fields_to_copy:
                                    if field in trigger:
                                        new_trigger[field] = trigger[field]

                                local_triggers.append(new_trigger)

                return local_triggers

            # Handle multiple data formats
            if isinstance(data, dict):
                if 'itemsRetrieveResponses' in data:
                    for response in data['itemsRetrieveResponses']:
                        if 'responseObjectNode' in response:
                            rule = response['responseObjectNode']
                            new_triggers = process_single_rule(rule, "file")
                            triggers.extend(new_triggers)
                            processed_rules += 1
                elif 'ruleVersions' in data:
                    new_triggers = process_single_rule(data, "single")
                    triggers.extend(new_triggers)
                    processed_rules += 1

            # Handle API response format (list of rules)
            elif isinstance(data, list):
                for rule in data:
                    if isinstance(rule, dict):
                        new_triggers = process_single_rule(rule, "api")
                        triggers.extend(new_triggers)
                        processed_rules += 1

        except Exception as e:
            import traceback
            print(f"\n[ERROR] Exception in extract_triggers: {str(e)}")
            traceback.print_exc()

        return triggers
