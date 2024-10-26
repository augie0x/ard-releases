# utils.py
import logging

from PyQt5.QtCore import QSettings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SettingsManager:
    def __init__(self):
        self.settings = QSettings('YourCompany', 'AdjustmentRuleApp')
        self.load_tokens()

    def load_tokens(self):
        self.base_hostname = self.settings.value('base_hostname', type=str)
        self.username = self.settings.value('username', type=str)
        self.password = self.settings.value('password', type=str)
        self.client_id = self.settings.value('client_id', type=str)
        self.client_secret = self.settings.value('client_secret', type=str)
        self.access_token = self.settings.value('access_token', type=str)
        self.refresh_token = self.settings.value('refresh_token', type=str)
        self.token_type = self.settings.value('token_type', type=str)
        self.expires_in = self.settings.value('expires_in', type=int)
        self.scope = self.settings.value('scope', type=str)

    def save_credentials(self, base_hostname, username, password, client_id, client_secret, token_data=None):
        """Save credentials and token data"""
        # Save basic credentials
        self.settings.setValue('base_hostname', base_hostname)
        self.settings.setValue('username', username)
        self.settings.setValue('password', password)
        self.settings.setValue('client_id', client_id)
        self.settings.setValue('client_secret', client_secret)

        # Save token data if provided
        if token_data:
            self.settings.setValue('access_token', token_data.get('access_token'))
            self.settings.setValue('refresh_token', token_data.get('refresh_token'))
            self.settings.setValue('token_type', token_data.get('token_type'))
            self.settings.setValue('expires_in', token_data.get('expires_in'))
            self.settings.setValue('scope', token_data.get('scope'))

        # Reload the tokens
        self.load_tokens()

    def has_saved_credentials(self):
        """Check if there are saved credentials"""
        return all([
            self.base_hostname,
            self.username,
            self.client_id,
            self.access_token,
            self.token_type
        ])

    def clear_credentials(self):
        """Clear all saved credentials"""
        settings_keys = [
            'base_hostname', 'username', 'password', 'client_id', 'client_secret',
            'access_token', 'refresh_token', 'token_type', 'expires_in', 'scope'
        ]
        try:
            for key in settings_keys:
                self.settings.remove(key)
                self.settings.sync()
                return True
        except Exception as e:
            logger.error(f"Erorr clearing connections: {str(e)}")
            return False
