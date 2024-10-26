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
        Handles both API response and manual JSON file structures.
        """
        triggers = []

        if not data:
            return triggers

        try:
            def extract_triggers_from_rule_version(version):
                """Helper function to extract triggers from a rule version"""
                if 'triggers' in version and 'adjustmentTriggerForRule' in version['triggers']:
                    return version['triggers']['adjustmentTriggerForRule']
                return []

            # Case 1: Direct list of rules (API response)
            if isinstance(data, list):
                # print(f"Processing list of {len(data)} rules")
                for rule in data:
                    if 'ruleVersions' in rule and 'adjustmentRuleVersion' in rule['ruleVersions']:
                        for version in rule['ruleVersions']['adjustmentRuleVersion']:
                            triggers.extend(extract_triggers_from_rule_version(version))

            # Case 2: Dictionary response
            elif isinstance(data, dict):
                # Case 2a: Manual JSON file structure
                if 'itemsRetrieveResponses' in data:
                    # print("Processing itemsRetrieveResponses structure")
                    for response in data['itemsRetrieveResponses']:
                        if ('responseObjectNode' in response and
                                'ruleVersions' in response['responseObjectNode'] and
                                'adjustmentRuleVersion' in response['responseObjectNode']['ruleVersions']):

                            versions = response['responseObjectNode']['ruleVersions']['adjustmentRuleVersion']
                            for version in versions:
                                triggers.extend(extract_triggers_from_rule_version(version))

                # Case 2b: Direct rule versions container
                elif 'ruleVersions' in data and 'adjustmentRuleVersion' in data['ruleVersions']:
                    # print("Processing direct ruleVersions structure")
                    for version in data['ruleVersions']['adjustmentRuleVersion']:
                        triggers.extend(extract_triggers_from_rule_version(version))

            # print(f"\nTotal triggers extracted: {len(triggers)}")
            # if triggers:
            # print(f"First trigger keys: {list(triggers[0].keys())}")
            # else:
            # print("No triggers were found in the data")

        except Exception as e:
            # print(f"Error during trigger extraction: {e}")
            import traceback
            traceback.print_exc()

        return triggers
