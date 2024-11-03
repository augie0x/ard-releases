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
        Handles both API responses and manual JSON file structures.
        """
        triggers = []
        processed_rules = 0

        if not data:
            print("[DEBUG] No data to process")
            return triggers

        try:
            # First determine the data source and format
            print("\n[DEBUG] Analyzing input data format:")
            print(f"Data type: {type(data)}")
            if isinstance(data, dict):
                print("Keys in data:", list(data.keys()))
            elif isinstance(data, list):
                print(f"Number of items: {len(data)}")
                if data:
                    print("First item keys:", list(data[0].keys()))

            def process_single_rule(rule, source_type="api"):
                """Helper function to process a single rule consistently"""
                rule_id = str(rule.get('id', 'N/A'))
                rule_name = rule.get('name', 'Unknown Rule')

                local_triggers = []

                if 'ruleVersions' in rule and isinstance(rule['ruleVersions'], dict):
                    versions = rule['ruleVersions'].get('adjustmentRuleVersion', [])
                    if not isinstance(versions, list):
                        versions = [versions]

                    for version in versions:
                        if 'triggers' in version and 'adjustmentTriggerForRule' in version['triggers']:
                            version_triggers = version['triggers']['adjustmentTriggerForRule']
                            if not isinstance(version_triggers, list):
                                version_triggers = [version_triggers]

                            for trigger in version_triggers:
                                # Create a new trigger dictionary with rule information
                                new_trigger = {
                                    'ruleId': rule_id,
                                    'ruleName': rule_name,
                                    'versionNum': version.get('versionNum', 'N/A')
                                }

                                # Add adjustment allocation if present
                                if 'adjustmentAllocation' in trigger:
                                    new_trigger['adjustmentAllocation'] = trigger['adjustmentAllocation']

                                # Add other trigger fields
                                fields_to_copy = [
                                    'jobOrLocation', 'jobOrLocationEffectiveDate',
                                    'laborCategoryEntries', 'payCodes', 'matchAnywhere'
                                ]
                                for field in fields_to_copy:
                                    if field in trigger:
                                        new_trigger[field] = trigger[field]

                                local_triggers.append(new_trigger)
                                print(f"Added trigger for rule {rule_id}")

                return local_triggers

            # Handle API response format (list of rules)
            if isinstance(data, list):
                for rule in data:
                    if isinstance(rule, dict):
                        new_triggers = process_single_rule(rule, "api")
                        triggers.extend(new_triggers)
                        processed_rules += 1

            # Handle manual JSON file format
            elif isinstance(data, dict) and 'itemsRetrieveResponses' in data:
                for response in data['itemsRetrieveResponses']:
                    if 'responseObjectNode' in response:
                        rule = response['responseObjectNode']
                        new_triggers = process_single_rule(rule, "manual")
                        triggers.extend(new_triggers)
                        processed_rules += 1

        except Exception as e:
            import traceback
            traceback.print_exc()

        return triggers