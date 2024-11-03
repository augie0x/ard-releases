# api_client.py

import logging
from logging.handlers import RotatingFileHandler

import requests

from .utils import SettingsManager

# Configure logging to file with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler('app.log', maxBytes=5 * 1024 * 1024, backupCount=2)  # 5MB per file
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class APIClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.settings_manager = SettingsManager()
        self.base_hostname = None
        self.client_id = None
        self.client_secret = None
        self.username = None
        self.password = None
        self.load_tokens()

    def load_tokens(self):
        """Load all authentication-related data from settings"""
        try:
            self.access_token = self.settings_manager.access_token
            self.refresh_token = self.settings_manager.refresh_token
            self.token_type = self.settings_manager.token_type
            self.base_hostname = self.settings_manager.base_hostname
            self.client_id = self.settings_manager.client_id
            self.client_secret = self.settings_manager.client_secret
            self.username = self.settings_manager.username
            self.password = self.settings_manager.password

            logger.debug(f"Loaded tokens - Access Token: {'Present' if self.access_token else 'None'}, "
                         f"Refresh Token: {'Present' if self.refresh_token else 'None'}, "
                         f"Base Hostname: {self.base_hostname}")

        except Exception as e:
            logger.error(f"Error loading tokens: {str(e)}")
            self.clear_tokens()

    def set_tokens(self, access_token, refresh_token, token_type):
        """Set tokens with validation"""
        if not all([access_token, refresh_token, token_type]):
            logger.warning("Attempting to set incomplete token data")
            return False

        logger.debug("Setting new tokens")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        return True

    def switch_connection(self, connection_data):
        """Handle switching to a new connection with proper token management"""
        logger.debug(f"Switching connection to: {connection_data.get('base_hostname')}")

        try:
            # Clear existing tokens and settings
            self.clear_tokens()

            # Set new connection details
            self.base_hostname = connection_data.get('base_hostname')
            self.username = connection_data.get('username')
            self.password = connection_data.get('password')
            self.client_id = connection_data.get('client_id')
            self.client_secret = connection_data.get('client_secret')

            # Authenticate with new connection
            token_data = self.authenticate(
                self.base_hostname,
                self.username,
                self.password,
                self.client_id,
                self.client_secret
            )

            if token_data:
                # Explicitly save the new tokens
                self.settings_manager.save_credentials(
                    self.base_hostname,
                    self.username,
                    self.password,
                    self.client_id,
                    self.client_secret,
                    token_data
                )

                # Set the tokens in memory
                self.set_tokens(
                    token_data.get('access_token'),
                    token_data.get('refresh_token'),
                    token_data.get('token_type')
                )

                logger.debug("Connection switch successful")
                return True
            else:
                logger.error("Failed to get token data during connection switch")
                return False

        except Exception as e:
            logger.error(f"Error during connection switch: {str(e)}")
            self.clear_tokens()  # Clear tokens on failure
            return False

    def clear_tokens(self):
        """Clear all token and connection data"""
        logger.debug("Clearing all tokens and connection data")
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.base_hostname = None
        self.username = None
        self.password = None
        self.client_id = None
        self.client_secret = None
        self.token_expires_at = None

    def refresh_auth_token(self):
        """Refresh the authentication token"""
        if not all([self.refresh_token, self.base_hostname, self.client_id, self.client_secret]):
            try:
                if all([self.base_hostname, self.username, self.password, self.client_id, self.client_secret]):
                    token_data = self.authenticate(
                        self.base_hostname,
                        self.username,
                        self.password,
                        self.client_id,
                        self.client_secret
                    )
                    return token_data is not None
                else:
                    raise Exception("Insufficient credentials for re-authentication")
            except Exception as e:
                return False

        auth_url = f"{self.base_hostname}/api/authentication/access_token"

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(auth_url, data=payload, headers=headers)

            if response.status_code == 200:
                token_data = response.json()
                self.set_tokens(
                    token_data.get('access_token'),
                    token_data.get('refresh_token'),
                    token_data.get('token_type')
                )
                return True
            else:
                return False
        except Exception as e:
            return False

    def authenticate(self, base_hostname, username, password, client_id, client_secret):
        """Authenticate with improved token handling"""
        logger.debug(f"Authenticating with {base_hostname}")

        auth_url = f"{base_hostname}/api/authentication/access_token"

        payload = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_chain': 'OAuthLdapService'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(auth_url, data=payload, headers=headers)
            logger.debug(f"Authentication response status: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()

                # Validate token data
                if all([
                    token_data.get('access_token'),
                    token_data.get('refresh_token'),
                    token_data.get('token_type')
                ]):
                    logger.debug("Authentication successful with complete token data")
                    return token_data
                else:
                    logger.error("Received incomplete token data from authentication")
                    return None
            else:
                logger.error(f"Authentication failed with status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def get_adjustment_rules(self):
        """
        Retrieves adjustment rules from the API.
        """
        if not self.access_token:
            raise Exception("Access token is missing. Please authenticate first.")

        base_hostname = self.settings_manager.base_hostname
        if base_hostname.endswith("/"):
            base_hostname = base_hostname[:-1]

        adjustment_rules_path = "/api/v1/timekeeping/setup/adjustment_rules"
        adjustment_rules_url = f"{base_hostname}{adjustment_rules_path}"

        # print(f"\nAPI Debug Information:")
        # print(f"Base Hostname: {base_hostname}")
        # print(f"Full URL: {adjustment_rules_url}")

        headers = {
            'Authorization': f"{self.token_type} {self.access_token}",
            'Accept': 'application/json'
        }

        try:
            # print("\nSending API request...")
            response = requests.get(adjustment_rules_url, headers=headers)
            # print(f"Response Status Code: {response.status_code}")

            if response.status_code == 401:
                logger.debug("Received 401, attempting token refresh")
                if self.refresh_auth_token():
                    headers['Authorization'] = f"{self.token_type} {self.access_token}"
                    response = requests.get(adjustment_rules_url, headers=headers)
                else:
                    raise Exception("Token refresh failed. Please authenticate again")

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if data:
                        first_rule = data[0]
                        # Process and extract triggers
                        from src.data_loader import DataLoader  # Make sure to import at the top
                        triggers = DataLoader.extract_triggers(data)
                        return triggers  # Return triggers instead of raw data

                return data

                return data
            else:
                # print(f"Error response content: {response.text[:500]}")
                raise Exception(f"API request failed with status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            # print(f"Request Exception: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")

    def disconnect(self):
        """Handle proper disconnection and cleanup"""
        try:
            logger.debug("Initiating disconnect")

            # Clear all tokens and credentials from memory
            self.clear_tokens()

            # Clear saved credentials from settings
            self.settings_manager.clear_credentials()

            logger.debug("Disconnect successful")
            return True

        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            return False

    @staticmethod
    def mask_sensitive_info(payload):
        """
        Masks sensitive information in the payload for logging purposes.
        """
        masked = payload.copy()
        if 'password' in masked:
            masked['password'] = '******'
        if 'client_secret' in masked:
            masked['client_secret'] = '******'
        return masked
