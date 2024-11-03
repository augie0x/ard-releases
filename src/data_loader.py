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
    def extract_triggers(data):
        """
        Extracts triggers from the given data.
        Handles API responses, manual JSON file structures, and single rule dictionaries.
        """
        triggers = []

        if not data:
            return triggers

        try:
            def extract_triggers_from_rule_version(version, rule_name):
                """Helper function to extract triggers from a rule version"""
                extracted_triggers = []
                if 'triggers' in version and 'adjustmentTriggerForRule' in version['triggers']:
                    for trigger in version['triggers']['adjustmentTriggerForRule']:
                        # Create a deep copy of the trigger
                        trigger_copy = dict(trigger)
                        # Explicitly set the rule name with a consistent key
                        trigger_copy['ruleName'] = rule_name
                        extracted_triggers.append(trigger_copy)

                return extracted_triggers

            # Case 1: API response format (list of rules)
            if isinstance(data, list):
                for rule in data:
                    # Extract rule name directly from the rule object
                    rule_name = rule.get('name')

                    if not rule_name:
                        rule_name = "Unknown Rule"

                    if 'ruleVersions' in rule and isinstance(rule['ruleVersions'], dict):
                        versions = rule['ruleVersions'].get('adjustmentRuleVersion', [])
                        if versions:
                            for version in versions:
                                new_triggers = extract_triggers_from_rule_version(version, rule_name)
                                triggers.extend(new_triggers)

            # Case 2: Single rule dictionary
            elif isinstance(data, dict) and 'id' in data and 'ruleVersions' in data:
                rule = data
                # Extract rule name directly from the rule object
                rule_name = rule.get('name')

                if not rule_name:
                    rule_name = "Unknown Rule"

                if 'ruleVersions' in rule and isinstance(rule['ruleVersions'], dict):
                    versions = rule['ruleVersions'].get('adjustmentRuleVersion', [])
                    if versions:
                        for version in versions:
                            new_triggers = extract_triggers_from_rule_version(version, rule_name)
                            triggers.extend(new_triggers)

            # Case 3: Manual JSON file format
            elif isinstance(data, dict) and 'itemsRetrieveResponses' in data:
                for response in data['itemsRetrieveResponses']:
                    if 'responseObjectNode' in response:
                        # Get rule name from responseObjectNode
                        rule_name = response['responseObjectNode'].get('name')
                        if not rule_name and 'itemDataInfo' in response:
                            rule_name = response['itemDataInfo'].get('title')
                        if not rule_name:
                            rule_name = 'Unknown Rule'

                        if ('ruleVersions' in response['responseObjectNode'] and
                                'adjustmentRuleVersion' in response['responseObjectNode']['ruleVersions']):
                            versions = response['responseObjectNode']['ruleVersions']['adjustmentRuleVersion']
                            for version in versions:
                                new_triggers = extract_triggers_from_rule_version(version, rule_name)
                                triggers.extend(new_triggers)

        except Exception as e:
            import traceback
            traceback.print_exc()

        return triggers

